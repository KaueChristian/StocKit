"""Regras comuns aos serviços de lançamento (uso interno do pacote ``core.services``)."""

from core.domain.catalog import Item
from core.domain.errors import (
    InactiveRecordError,
    IncompatibleUnitsError,
    InsufficientStockError,
    ValidationError,
)
from core.domain.ids import ItemId, LocationId, LotId
from core.domain.ledger import first_negative_from
from core.domain.location import Location
from core.domain.lot import Lot
from core.domain.movement import Movement
from core.domain.quantity import Quantity
from core.ports.unit_of_work import UnitOfWork


def active_item(uow: UnitOfWork, item_id: ItemId) -> Item:
    item = uow.items.get(item_id)
    if not item.active:
        raise InactiveRecordError(f"o item {item.sku} está inativo")
    return item


def active_location(uow: UnitOfWork, location_id: LocationId) -> Location:
    location = uow.locations.get(location_id)
    if not location.active:
        raise InactiveRecordError(f"o local {location.name!r} está inativo")
    return location


def item_lot(uow: UnitOfWork, item: Item, lot_id: LotId | None) -> Lot | None:
    """Confere o lote informado: o item controla lote, o lote existe e é deste item."""
    if lot_id is None:
        return None
    if not item.tracks_lots:
        raise ValidationError("lot_id", f"o item {item.sku} não controla lote")
    lot = uow.lots.get(lot_id)
    if lot.item_id != item.id:
        raise ValidationError("lot_id", f"o lote {lot.code} não é do item {item.sku}")
    return lot


def require_lot(item: Item, lot_id: LotId | None) -> None:
    if lot_id is None and item.tracks_lots:
        raise ValidationError("lot_id", f"o item {item.sku} controla lote: informe o lote")


def check_balance(uow: UnitOfWork, item: Item, location: Location, movement: Movement) -> None:
    """Recusa se algum ponto do livro, a partir da movimentação, ficar negativo (INV-05)."""
    history = uow.movements.list(item_id=item.id, location_id=location.id, lot_id=movement.lot_id)
    negative = first_negative_from(history, movement, item.base_unit)
    if negative is not None:
        raise InsufficientStockError(
            f"saldo insuficiente de {item.sku} em {location.name!r}: ficaria "
            f"{negative.balance} em {negative.at:%d/%m/%Y %H:%M} UTC"
        )


def in_base_unit(item: Item, quantity: Quantity) -> Quantity:
    """Converte para a unidade base; recusa conversão que arredondaria (o livro não perde valor)."""
    converted = quantity.to(item.base_unit)
    if converted.to(quantity.unit) != quantity:
        raise IncompatibleUnitsError(
            f"{quantity} não vira um número exato de {item.base_unit} (unidade base de "
            f"{item.sku}); lance na unidade base"
        )
    return converted
