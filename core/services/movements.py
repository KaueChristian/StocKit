"""Registrar movimentações e transferências (M1.6, M1.8, M1.9; RF-005, RF-007, RF-008).

São os únicos caminhos para lançar no livro: conferem os cadastros, convertem a quantidade para a
unidade base do item, aplicam a política de saldo negativo e gravam numa Unit of Work — tudo ou
nada. ``record_movement`` lança uma movimentação (ou várias, quando o FEFO reparte uma saída entre
lotes); ``transfer_stock`` lança as duas pontas de uma transferência juntas.
"""

from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal

from core.domain.catalog import Item
from core.domain.errors import InactiveRecordError, InsufficientStockError, ValidationError
from core.domain.ids import ItemId, LocationId, LotId, PartyId, new_movement_id
from core.domain.ledger import available_at, balance
from core.domain.location import Location
from core.domain.lot import Lot
from core.domain.movement import Direction, Movement, MovementKind, make_transfer
from core.domain.policy import NegativeStockPolicy
from core.domain.quantity import Quantity
from core.ports.clock import Clock
from core.ports.unit_of_work import UnitOfWork
from core.services._rules import (
    active_item,
    active_location,
    check_balance,
    check_serials,
    in_base_unit,
    item_lot,
    require_lot,
    serial_quantity,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class RecordMovement:
    """Pedido de lançamento, como chega da tela ou da API.

    ``quantity`` pode vir em qualquer unidade da mesma grandeza da unidade base do item, desde que
    a conversão seja exata. ``occurred_at`` vazio = agora. Saída de item com lote **sem** lote
    informado é repartida por FEFO.
    """

    kind: MovementKind
    item_id: ItemId
    location_id: LocationId
    quantity: Quantity
    author: str
    occurred_at: datetime | None = None
    lot_id: LotId | None = None
    party_id: PartyId | None = None
    unit_cost: Decimal | None = None
    reason: str | None = None
    serials: frozenset[str] = frozenset()


@dataclass(frozen=True, slots=True, kw_only=True)
class TransferStock:
    """Pedido de transferência entre dois locais. Mesmas regras de unidade do ``RecordMovement``."""

    item_id: ItemId
    from_location: LocationId
    to_location: LocationId
    quantity: Quantity
    author: str
    occurred_at: datetime | None = None
    lot_id: LotId | None = None
    reason: str | None = None
    serials: frozenset[str] = frozenset()


def record_movement(
    uow: UnitOfWork,
    clock: Clock,
    command: RecordMovement,
    *,
    policy: NegativeStockPolicy | None = None,
) -> tuple[Movement, ...]:
    """Lança e devolve o que foi gravado: uma movimentação, ou uma por lote quando o FEFO
    reparte a saída. Erro de domínio = nada gravado."""
    if command.kind.is_transfer:
        raise ValidationError("kind", "transferência tem serviço próprio (as duas pontas juntas)")
    now = clock.now()

    with uow:
        policy = _policy(uow, policy)
        item = active_item(uow, command.item_id)
        location = active_location(uow, command.location_id)
        if command.party_id is not None and not uow.parties.get(command.party_id).active:
            raise InactiveRecordError("a parte informada está inativa")
        item_lot(uow, item, command.lot_id)
        use_fefo = (
            item.tracks_lots and command.lot_id is None and command.kind.direction is Direction.OUT
        )
        if not use_fefo:
            require_lot(item, command.lot_id)

        quantity = in_base_unit(item, command.quantity)
        serial_quantity(item, quantity, command.serials)
        movement = Movement(
            kind=command.kind,
            item_id=item.id,
            location_id=location.id,
            quantity=quantity,
            serials=command.serials,
            occurred_at=command.occurred_at if command.occurred_at is not None else now,
            recorded_at=now,
            author=command.author,
            lot_id=command.lot_id,
            party_id=command.party_id,
            unit_cost=command.unit_cost,
            reason=command.reason,
        )
        movements = (
            _split_by_fefo(uow, item, location, movement, policy) if use_fefo else (movement,)
        )
        check_serials(uow, item, movements)
        for each in movements:
            if policy is NegativeStockPolicy.FORBID:
                check_balance(uow, item, location, each)
            uow.movements.append(each)
        uow.commit()
    return movements


def transfer_stock(
    uow: UnitOfWork,
    clock: Clock,
    command: TransferStock,
    *,
    policy: NegativeStockPolicy | None = None,
) -> tuple[Movement, Movement]:
    """Lança saída na origem e entrada no destino, juntas (INV-03). Devolve (saída, entrada).

    A política de saldo negativo vale na origem; o destino só ganha. Se qualquer passo falhar,
    nenhuma das pontas fica gravada. Item com lote exige o lote (sem FEFO na transferência).
    """
    now = clock.now()
    with uow:
        policy = _policy(uow, policy)
        item = active_item(uow, command.item_id)
        origin = active_location(uow, command.from_location)
        destination = active_location(uow, command.to_location)
        item_lot(uow, item, command.lot_id)
        require_lot(item, command.lot_id)

        quantity = in_base_unit(item, command.quantity)
        serial_quantity(item, quantity, command.serials)
        outgoing, incoming = make_transfer(
            item_id=item.id,
            from_location=origin.id,
            to_location=destination.id,
            quantity=quantity,
            serials=command.serials,
            occurred_at=command.occurred_at if command.occurred_at is not None else now,
            recorded_at=now,
            author=command.author,
            lot_id=command.lot_id,
            reason=command.reason,
        )
        check_serials(uow, item, (outgoing, incoming))
        if policy is NegativeStockPolicy.FORBID:
            check_balance(uow, item, origin, outgoing)
        uow.movements.append(outgoing)
        uow.movements.append(incoming)
        uow.commit()
    return outgoing, incoming


def _policy(uow: UnitOfWork, given: NegativeStockPolicy | None) -> NegativeStockPolicy:
    """Política pedida na chamada ou, se nenhuma, a da configuração do sistema (M1.12)."""
    return given if given is not None else uow.settings.get().negative_stock_policy


def _split_by_fefo(
    uow: UnitOfWork,
    item: Item,
    location: Location,
    requested: Movement,
    policy: NegativeStockPolicy,
) -> tuple[Movement, ...]:
    """Reparte uma saída entre os lotes do item no local, do que vence primeiro ao que vence
    por último (INV-06). Lote vencido na data da saída fica de fora: baixar estoque vencido exige
    informar o lote."""
    day = requested.occurred_at.date()
    lots = uow.lots.list_for_item(item.id)
    usable = [lot for lot in lots if not lot.is_expired_on(day)]
    expired = [lot for lot in lots if lot.is_expired_on(day)]
    remaining = requested.quantity
    taken: list[tuple[Lot, Quantity]] = []
    for lot in usable:
        if remaining.value == 0:
            break
        history = uow.movements.list(item_id=item.id, location_id=location.id, lot_id=lot.id)
        available = available_at(history, requested.occurred_at, item.base_unit)
        take = remaining if remaining <= available else available
        if take.value > 0:
            taken.append((lot, take))
            remaining -= take

    if remaining.value > 0:
        if policy is NegativeStockPolicy.FORBID or not usable:
            raise InsufficientStockError(
                _fefo_shortage(uow, item, location, requested, remaining, expired)
            )
        last = usable[-1]
        if taken and taken[-1][0] == last:
            taken[-1] = (last, taken[-1][1] + remaining)
        else:
            taken.append((last, remaining))  # ALLOW: o que faltar sai do último lote válido

    # Cada parte é uma movimentação própria: id novo (replace copiaria o id do pedido).
    return tuple(
        replace(requested, id=new_movement_id(), lot_id=lot.id, quantity=amount)
        for lot, amount in taken
    )


def _fefo_shortage(
    uow: UnitOfWork,
    item: Item,
    location: Location,
    requested: Movement,
    missing: Quantity,
    expired: list[Lot],
) -> str:
    """Mensagem do saldo que faltou, avisando se havia estoque em lote vencido."""
    expired_stock = balance(
        (
            m
            for lot in expired
            for m in uow.movements.list(
                item_id=item.id, location_id=location.id, lot_id=lot.id, until=requested.occurred_at
            )
        ),
        item.base_unit,
    )
    message = (
        f"saldo insuficiente de {item.sku} em {location.name!r} nos lotes válidos: faltam {missing}"
    )
    if expired_stock.value > 0:
        message += f"; há {expired_stock} em lote(s) vencido(s), que o FEFO não usa"
    return message
