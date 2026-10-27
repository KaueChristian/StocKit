"""Repositório de lotes em memória (M1.9)."""

from datetime import date
from uuid import uuid4

import pytest

from adapters.memory.unit_of_work import MemoryUnitOfWork
from core.domain.errors import ConflictError
from core.domain.ids import ItemId
from core.domain.lot import Lot

A, B = sorted([ItemId(uuid4()), ItemId(uuid4())])


def test_lots_are_listed_per_item_in_fefo_order() -> None:
    with MemoryUnitOfWork() as uow:
        late = Lot(item_id=A, code="TARDE", expires_on=date(2027, 1, 1))
        soon = Lot(item_id=A, code="CEDO", expires_on=date(2026, 11, 1))
        other = Lot(item_id=B, code="X")
        for lot in (late, other, soon):
            uow.lots.add(lot)
        assert uow.lots.list_for_item(A) == (soon, late)
        assert uow.lots.list() == (soon, late, other)
        assert uow.lots.find_by_code(A, "CEDO") == soon
        assert uow.lots.find_by_code(B, "CEDO") is None


def test_lot_code_is_unique_within_the_item() -> None:
    with MemoryUnitOfWork() as uow:
        first = Lot(item_id=A, code="L1")
        uow.lots.add(first)
        uow.lots.add(Lot(item_id=B, code="L1"))
        with pytest.raises(ConflictError, match="L1"):
            uow.lots.add(Lot(item_id=A, code="l1"))
        second = Lot(item_id=A, code="L2")
        uow.lots.add(second)
        with pytest.raises(ConflictError):
            uow.lots.update(Lot(item_id=A, code="L1", id=second.id))
        uow.lots.update(Lot(item_id=A, code="L1", expires_on=date(2026, 12, 1), id=first.id))


def test_lots_follow_the_unit_of_work() -> None:
    uow = MemoryUnitOfWork()
    with uow:
        uow.lots.add(Lot(item_id=A, code="L1"))
    with uow:
        assert uow.lots.list() == ()
