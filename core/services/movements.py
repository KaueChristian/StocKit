"""Registrar movimentações (M1.6, RF-005, RF-007, INV-05).

O serviço é o único caminho para lançar entrada, saída, ajuste, perda e devolução: confere os
cadastros, converte a quantidade para a unidade base do item, aplica a política de saldo negativo
e grava tudo numa Unit of Work — ou nada. Transferência tem serviço próprio (M1.8).
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
from core.domain.movement import Movement, MovementKind
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
    occurred_at = command.occurred_at if command.occurred_at is not None else now

    with uow:
        item = uow.items.get(command.item_id)
        location = uow.locations.get(command.location_id)
        if not item.active:
            raise InactiveRecordError(f"o item {item.sku} está inativo")
        if not location.active:
            raise InactiveRecordError(f"o local {location.name!r} está inativo")
        if command.party_id is not None and not uow.parties.get(command.party_id).active:
            raise InactiveRecordError("a parte informada está inativa")
        _check_lot(item, command.lot_id)

        movement = Movement(
            kind=command.kind,
            item_id=item.id,
            location_id=location.id,
            quantity=_in_base_unit(item, command.quantity),
            occurred_at=occurred_at,
            recorded_at=now,
            author=command.author,
            lot_id=command.lot_id,
            party_id=command.party_id,
            unit_cost=command.unit_cost,
            reason=command.reason,
        )
        if policy is NegativeStockPolicy.FORBID:
            history = uow.movements.list(
                item_id=item.id, location_id=location.id, lot_id=command.lot_id
            )
            negative = first_negative_from(history, movement, item.base_unit)
            if negative is not None:
                raise InsufficientStockError(
                    f"saldo insuficiente de {item.sku} em {location.name!r}: ficaria "
                    f"{negative.balance} em {negative.at:%d/%m/%Y %H:%M} UTC"
                )
        uow.movements.append(movement)
        uow.commit()
    return movement


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
