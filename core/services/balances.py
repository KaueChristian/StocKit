"""Consultas de saldo (M1.7, RF-006, INV-01, INV-08).

O saldo nunca é lido de um campo: é sempre a soma assinada das movimentações (ADR-004). Todas as
consultas aceitam ``at`` — o saldo "em uma data", contando as movimentações que **ocorreram** até
aquele instante, inclusive (``occurred_at``; um lançamento retroativo muda o saldo do passado).

Saldo de um local inclui, por padrão, os locais abaixo dele: o depósito soma corredores e
prateleiras. A soma dos saldos de cada local é o saldo total do item (INV-08).

Estas consultas só leem: nunca fazem ``commit``.
"""

from collections import defaultdict
from collections.abc import Mapping
from datetime import datetime

from core.domain.catalog import Item
from core.domain.ids import ItemId, LocationId, LotId
from core.domain.ledger import balance
from core.domain.location import LocationTree
from core.domain.movement import Movement
from core.domain.quantity import Quantity
from core.ports.unit_of_work import UnitOfWork


def item_balance(
    uow: UnitOfWork,
    item_id: ItemId,
    *,
    location_id: LocationId | None = None,
    lot_id: LotId | None = None,
    at: datetime | None = None,
    include_sublocations: bool = True,
) -> Quantity:
    """Saldo do item, na unidade base: total, num local (com ou sem sublocais) e/ou num lote."""
    with uow:
        item = uow.items.get(item_id)
        movements = uow.movements.list(item_id=item_id, lot_id=lot_id, until=at)
        if location_id is None:
            return balance(movements, item.base_unit)
        uow.locations.get(location_id)  # local inexistente: NotFoundError, não saldo zero
        tree = LocationTree(uow.locations.list())
        scope = {location_id}
        if include_sublocations:
            scope |= {loc.id for loc in tree.descendants(location_id)}
        return balance((m for m in movements if m.location_id in scope), item.base_unit)


def balances_by_location(
    uow: UnitOfWork, item_id: ItemId, *, at: datetime | None = None
) -> Mapping[LocationId, Quantity]:
    """Saldo próprio de cada local que já teve movimentação do item (sem somar sublocais).

    A soma dos valores é o saldo total do item (INV-08). Locais com saldo zero aparecem se já
    tiveram movimentação — "zerou" é informação diferente de "nunca teve".
    """
    with uow:
        item = uow.items.get(item_id)
        grouped: defaultdict[LocationId, list[Movement]] = defaultdict(list)
        for movement in uow.movements.list(item_id=item_id, until=at):
            grouped[movement.location_id].append(movement)
        return _totals(grouped, item)


def balances_by_lot(
    uow: UnitOfWork,
    item_id: ItemId,
    *,
    location_id: LocationId | None = None,
    at: datetime | None = None,
) -> Mapping[LotId | None, Quantity]:
    """Saldo de cada lote do item (opcionalmente só num local, sem sublocais). Chave ``None`` =
    movimentações sem lote."""
    with uow:
        item = uow.items.get(item_id)
        if location_id is not None:
            uow.locations.get(location_id)
        grouped: defaultdict[LotId | None, list[Movement]] = defaultdict(list)
        for movement in uow.movements.list(item_id=item_id, location_id=location_id, until=at):
            grouped[movement.lot_id].append(movement)
        return _totals(grouped, item)


def _totals[K](grouped: Mapping[K, list[Movement]], item: Item) -> dict[K, Quantity]:
    return {key: balance(movements, item.base_unit) for key, movements in grouped.items()}
