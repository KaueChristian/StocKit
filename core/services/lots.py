"""Cadastro de lotes (M1.9, RF-008)."""

from dataclasses import dataclass
from datetime import date

from core.domain.errors import ValidationError
from core.domain.ids import ItemId
from core.domain.lot import Lot
from core.ports.unit_of_work import UnitOfWork
from core.services._rules import active_item


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateLot:
    item_id: ItemId
    code: str
    expires_on: date | None = None


def create_lot(uow: UnitOfWork, command: CreateLot) -> Lot:
    """Cadastra um lote antes da primeira entrada dele.

    O item precisa controlar lote. Validade é obrigatória se o item controla validade, e recusada
    se não controla. Código repetido no mesmo item: ``ConflictError``.
    """
    with uow:
        item = active_item(uow, command.item_id)
        if not item.tracks_lots:
            raise ValidationError("item_id", f"o item {item.sku} não controla lote")
        if item.tracks_expiry and command.expires_on is None:
            raise ValidationError("expires_on", f"o item {item.sku} controla validade: informe")
        if not item.tracks_expiry and command.expires_on is not None:
            raise ValidationError("expires_on", f"o item {item.sku} não controla validade")
        lot = Lot(item_id=item.id, code=command.code, expires_on=command.expires_on)
        uow.lots.add(lot)
        uow.commit()
    return lot
