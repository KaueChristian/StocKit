"""Registrar movimentações e transferências (M1.6, M1.8; RF-005, RF-007, INV-03, INV-05).

São os únicos caminhos para lançar no livro: conferem os cadastros, convertem a quantidade para a
unidade base do item, aplicam a política de saldo negativo e gravam numa Unit of Work — tudo ou
nada. ``record_movement`` lança uma movimentação; ``transfer_stock`` lança as duas pontas de uma
transferência juntas.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from core.domain.catalog import Item
from core.domain.errors import (
    InactiveRecordError,
    IncompatibleUnitsError,
    InsufficientStockError,
    ValidationError,
)
from core.domain.ids import ItemId, LocationId, LotId, PartyId
from core.domain.ledger import first_negative_from
from core.domain.location import Location
from core.domain.movement import Movement, MovementKind, make_transfer
from core.domain.policy import NegativeStockPolicy
from core.domain.quantity import Quantity
from core.ports.clock import Clock
from core.ports.unit_of_work import UnitOfWork


@dataclass(frozen=True, slots=True, kw_only=True)
class RecordMovement:
    """Pedido de lançamento, como chega da tela ou da API.

    ``quantity`` pode vir em qualquer unidade da mesma grandeza da unidade base do item, desde que
    a conversão seja exata. ``occurred_at`` vazio = agora.
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


def record_movement(
    uow: UnitOfWork,
    clock: Clock,
    command: RecordMovement,
    *,
    policy: NegativeStockPolicy = NegativeStockPolicy.FORBID,
) -> Movement:
    """Lança uma movimentação e devolve o que foi gravado. Erro de domínio = nada gravado."""
    if command.kind.is_transfer:
        raise ValidationError("kind", "transferência tem serviço próprio (as duas pontas juntas)")
    now = clock.now()

    with uow:
        item = _active_item(uow, command.item_id)
        location = _active_location(uow, command.location_id)
        if command.party_id is not None and not uow.parties.get(command.party_id).active:
            raise InactiveRecordError("a parte informada está inativa")
        _check_lot(item, command.lot_id)

        movement = Movement(
            kind=command.kind,
            item_id=item.id,
            location_id=location.id,
            quantity=_in_base_unit(item, command.quantity),
            occurred_at=command.occurred_at if command.occurred_at is not None else now,
            recorded_at=now,
            author=command.author,
            lot_id=command.lot_id,
            party_id=command.party_id,
            unit_cost=command.unit_cost,
            reason=command.reason,
        )
        if policy is NegativeStockPolicy.FORBID:
            _check_balance(uow, item, location, movement)
        uow.movements.append(movement)
        uow.commit()
    return movement


def transfer_stock(
    uow: UnitOfWork,
    clock: Clock,
    command: TransferStock,
    *,
    policy: NegativeStockPolicy = NegativeStockPolicy.FORBID,
) -> tuple[Movement, Movement]:
    """Lança saída na origem e entrada no destino, juntas (INV-03). Devolve (saída, entrada).

    A política de saldo negativo vale na origem; o destino só ganha. Se qualquer passo falhar,
    nenhuma das pontas fica gravada.
    """
    now = clock.now()
    with uow:
        item = _active_item(uow, command.item_id)
        origin = _active_location(uow, command.from_location)
        destination = _active_location(uow, command.to_location)
        _check_lot(item, command.lot_id)

        outgoing, incoming = make_transfer(
            item_id=item.id,
            from_location=origin.id,
            to_location=destination.id,
            quantity=_in_base_unit(item, command.quantity),
            occurred_at=command.occurred_at if command.occurred_at is not None else now,
            recorded_at=now,
            author=command.author,
            lot_id=command.lot_id,
            reason=command.reason,
        )
        if policy is NegativeStockPolicy.FORBID:
            _check_balance(uow, item, origin, outgoing)
        uow.movements.append(outgoing)
        uow.movements.append(incoming)
        uow.commit()
    return outgoing, incoming


def _active_item(uow: UnitOfWork, item_id: ItemId) -> Item:
    item = uow.items.get(item_id)
    if not item.active:
        raise InactiveRecordError(f"o item {item.sku} está inativo")
    return item


def _active_location(uow: UnitOfWork, location_id: LocationId) -> Location:
    location = uow.locations.get(location_id)
    if not location.active:
        raise InactiveRecordError(f"o local {location.name!r} está inativo")
    return location


def _check_balance(uow: UnitOfWork, item: Item, location: Location, movement: Movement) -> None:
    """Recusa se algum ponto do livro, a partir da movimentação, ficar negativo (INV-05)."""
    history = uow.movements.list(item_id=item.id, location_id=location.id, lot_id=movement.lot_id)
    negative = first_negative_from(history, movement, item.base_unit)
    if negative is not None:
        raise InsufficientStockError(
            f"saldo insuficiente de {item.sku} em {location.name!r}: ficaria "
            f"{negative.balance} em {negative.at:%d/%m/%Y %H:%M} UTC"
        )


def _in_base_unit(item: Item, quantity: Quantity) -> Quantity:
    """Converte para a unidade base; recusa conversão que arredondaria (o livro não perde valor)."""
    converted = quantity.to(item.base_unit)
    if converted.to(quantity.unit) != quantity:
        raise IncompatibleUnitsError(
            f"{quantity} não vira um número exato de {item.base_unit} (unidade base de "
            f"{item.sku}); lance na unidade base"
        )
    return converted


def _check_lot(item: Item, lot_id: LotId | None) -> None:
    if lot_id is not None and not item.tracks_lots:
        raise ValidationError("lot_id", f"o item {item.sku} não controla lote")
    if lot_id is None and item.tracks_lots:
        raise ValidationError("lot_id", f"o item {item.sku} controla lote: informe o lote")
