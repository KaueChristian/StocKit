"""Regras comuns aos serviços de lançamento (uso interno do pacote ``core.services``)."""

from collections.abc import Sequence

from core.domain.catalog import Item, ItemKind
from core.domain.errors import (
    InactiveRecordError,
    IncompatibleUnitsError,
    InsufficientStockError,
    SerialNumberError,
    ValidationError,
)
from core.domain.ids import ItemId, LocationId, LotId
from core.domain.ledger import first_negative_from
from core.domain.location import Location
from core.domain.lot import Lot
from core.domain.movement import Movement
from core.domain.quantity import Quantity
from core.domain.serials import SerialProblem, first_serial_conflict
from core.ports.unit_of_work import UnitOfWork


def active_item(uow: UnitOfWork, item_id: ItemId) -> Item:
    item = uow.items.get(item_id)
    if not item.active:
        raise InactiveRecordError(f"o item {item.sku} está inativo", entity="item", record=item.sku)
    return item


def active_location(uow: UnitOfWork, location_id: LocationId) -> Location:
    location = uow.locations.get(location_id)
    if not location.active:
        raise InactiveRecordError(
            f"o local {location.name!r} está inativo", entity="location", record=location.name
        )
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
            f"{negative.balance} em {negative.at:%d/%m/%Y %H:%M} UTC",
            sku=item.sku,
            location=location.name,
            balance=negative.balance,
            at=negative.at,
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


def serial_quantity(item: Item, quantity: Quantity, serials: frozenset[str]) -> None:
    """Item serializado: quantidade inteira e números de série informados; outros: sem séries."""
    if item.kind is not ItemKind.SERIALIZED:
        if serials:
            raise ValidationError("serials", f"o item {item.sku} não é serializado")
        return
    if quantity.value != quantity.value.to_integral_value():
        raise ValidationError(
            "quantity", f"item serializado ({item.sku}) não tem quantidade fracionária: {quantity}"
        )
    if not serials:
        raise ValidationError(
            "serials", f"o item {item.sku} é serializado: informe os números de série"
        )


def check_serials(uow: UnitOfWork, item: Item, new: Sequence[Movement]) -> None:
    """Nenhuma série em dois lugares, nem saindo de onde não está (INV-07)."""
    if item.kind is not ItemKind.SERIALIZED:
        return
    conflict = first_serial_conflict(uow.movements.list(item_id=item.id), new)
    if conflict is None:
        return
    here = uow.locations.get(conflict.location_id).name
    where = (
        "fora do estoque"
        if conflict.current is None
        else (f"em {uow.locations.get(conflict.current).name!r}")
    )
    when = f"{conflict.at:%d/%m/%Y %H:%M} UTC"
    details: dict[str, object] = {
        "sku": item.sku,
        "serial": conflict.serial,
        "problem": conflict.problem,
        "location": here,
        "at": conflict.at,
    }
    if conflict.problem is SerialProblem.ALREADY_IN_STOCK:
        raise SerialNumberError(
            f"a série {conflict.serial} de {item.sku} já está {where} em {when}; "
            f"não pode entrar em {here!r}",
            **details,
        )
    raise SerialNumberError(
        f"a série {conflict.serial} de {item.sku} não está em {here!r} em {when} (está {where})",
        **details,
    )
