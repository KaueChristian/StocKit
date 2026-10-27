"""Adaptadores em memória (M1.5): repositórios, Unit of Work e relógios.

Estes testes viram a base da suíte de contrato da M2.6, que rodará os mesmos cenários contra o
SQLite.
"""

from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from hypothesis import given
from hypothesis import strategies as st

from adapters.clock import FixedClock, SystemClock
from adapters.memory.repositories import MemoryState
from adapters.memory.unit_of_work import MemoryUnitOfWork
from core.domain.catalog import Category, Item, ItemKind
from core.domain.errors import ConflictError, NotFoundError
from core.domain.ids import ItemId, LocationId, LotId, MovementId, TransferId
from core.domain.location import Location
from core.domain.movement import Movement, MovementKind, make_transfer
from core.domain.party import Party, PartyRole
from core.domain.quantity import STANDARD_UNITS, Quantity
from core.ports.clock import Clock
from core.ports.unit_of_work import UnitOfWork

UN = STANDARD_UNITS["un"]
WHEN = datetime(2026, 10, 27, 12, tzinfo=UTC)
SHOP, BACKROOM = LocationId(uuid4()), LocationId(uuid4())


def item(sku: str = "PAR-001", name: str = "Parafuso") -> Item:
    return Item(sku=sku, name=name, kind=ItemKind.RESALE, base_unit=UN)


def receipt(
    item_id: ItemId, *, at: datetime = WHEN, location: LocationId = SHOP, lot: LotId | None = None
) -> Movement:
    return Movement(
        kind=MovementKind.RECEIPT,
        item_id=item_id,
        location_id=location,
        quantity=Quantity(Decimal(1), UN),
        occurred_at=at,
        author="Ana",
        lot_id=lot,
    )


def test_adapters_satisfy_the_ports() -> None:
    """Conferido pelo mypy no check: as classes concretas cabem nos tipos das portas."""
    uow: UnitOfWork = MemoryUnitOfWork()
    clocks: list[Clock] = [SystemClock(), FixedClock(WHEN)]
    assert uow is not None
    assert all(c.now().tzinfo is UTC for c in clocks)


# --- cadastros ---------------------------------------------------------------------------


def test_add_get_update_and_list_items_in_sku_order() -> None:
    with MemoryUnitOfWork() as uow:
        b, a = item("B-2", "Bucha"), item("A-1", "Arruela")
        uow.items.add(b)
        uow.items.add(a)
        assert uow.items.get(a.id) is a
        assert [i.sku for i in uow.items.list()] == ["A-1", "B-2"]
        renamed = a.deactivated()
        uow.items.update(renamed)
        assert not uow.items.get(a.id).active


def test_registry_errors() -> None:
    with MemoryUnitOfWork() as uow:
        existing = item()
        uow.items.add(existing)
        with pytest.raises(ConflictError, match="já cadastrado"):
            uow.items.add(existing)
        with pytest.raises(NotFoundError, match="não encontrado"):
            uow.items.get(ItemId(uuid4()))
        with pytest.raises(NotFoundError, match="atualizar"):
            uow.items.update(item("OUTRO-1"))


def test_sku_is_unique_on_add_and_update() -> None:
    with MemoryUnitOfWork() as uow:
        first, second = item("PAR-001"), item("PAR-002", "Porca")
        uow.items.add(first)
        uow.items.add(second)
        with pytest.raises(ConflictError, match="PAR-001 já pertence"):
            uow.items.add(item("par-001", "Outro"))
        with pytest.raises(ConflictError, match="PAR-001"):
            uow.items.update(
                Item(sku="PAR-001", name="Porca", kind=ItemKind.RESALE, base_unit=UN, id=second.id)
            )
        uow.items.update(
            Item(sku="PAR-001", name="Parafuso M6", kind=ItemKind.RESALE, base_unit=UN, id=first.id)
        )
        assert uow.items.find_by_sku("PAR-001") == first
        assert uow.items.find_by_sku("NAO-EXISTE") is None


def test_other_registries_list_by_name_ignoring_case() -> None:
    with MemoryUnitOfWork() as uow:
        for name in ("loja", "Depósito", "almoxarifado"):
            uow.locations.add(Location(name=name))
            uow.categories.add(Category(name=name))
            uow.parties.add(Party(name=name, roles=frozenset({PartyRole.SUPPLIER})))
        expected = ["almoxarifado", "Depósito", "loja"]
        assert [x.name for x in uow.locations.list()] == expected
        assert [x.name for x in uow.categories.list()] == expected
        assert [x.name for x in uow.parties.list()] == expected


# --- livro de movimentações --------------------------------------------------------------


@pytest.mark.req("RF-005")
def test_ledger_appends_and_refuses_duplicates() -> None:
    with MemoryUnitOfWork() as uow:
        movement = receipt(ItemId(uuid4()))
        uow.movements.append(movement)
        assert uow.movements.get(movement.id) is movement
        with pytest.raises(ConflictError, match="já lançada"):
            uow.movements.append(movement)
        with pytest.raises(NotFoundError):
            uow.movements.get(MovementId(uuid4()))


@pytest.mark.req("RF-005")
def test_ledger_list_filters_and_orders() -> None:
    a, b = ItemId(uuid4()), ItemId(uuid4())
    lot = LotId(uuid4())
    late = receipt(a, at=WHEN + timedelta(hours=2))
    early = receipt(a, at=WHEN, location=BACKROOM, lot=lot)
    same_time = receipt(a, at=WHEN)
    other_item = receipt(b, at=WHEN + timedelta(hours=1))
    with MemoryUnitOfWork() as uow:
        for m in (late, early, same_time, other_item):
            uow.movements.append(m)
        ledger = uow.movements
        assert ledger.list() == (early, same_time, other_item, late), (
            "data, depois ordem de lançamento"
        )
        assert ledger.list(item_id=a) == (early, same_time, late)
        assert ledger.list(item_id=a, location_id=SHOP) == (same_time, late)
        assert ledger.list(lot_id=lot) == (early,)
        assert ledger.list(until=WHEN + timedelta(hours=1)) == (early, same_time, other_item), (
            "inclusive"
        )
        assert ledger.list(item_id=b, location_id=BACKROOM) == ()


@pytest.mark.req("RF-005")
def test_ledger_returns_transfer_pairs() -> None:
    outgoing, incoming = make_transfer(
        item_id=ItemId(uuid4()),
        from_location=SHOP,
        to_location=BACKROOM,
        quantity=Quantity(Decimal(2), UN),
        occurred_at=WHEN,
        author="Ana",
    )
    with MemoryUnitOfWork() as uow:
        uow.movements.append(incoming)
        assert outgoing.transfer_id is not None
        with pytest.raises(NotFoundError, match="incompleto"):
            uow.movements.transfer_pair(outgoing.transfer_id)
        uow.movements.append(outgoing)
        assert uow.movements.transfer_pair(outgoing.transfer_id) == (outgoing, incoming)
        with pytest.raises(NotFoundError):
            uow.movements.transfer_pair(TransferId(uuid4()))


# --- Unit of Work ------------------------------------------------------------------------


def test_commit_makes_changes_visible_to_other_units_of_work() -> None:
    state = MemoryState()
    saved = item()
    with MemoryUnitOfWork(state) as uow:
        uow.items.add(saved)
        with MemoryUnitOfWork(state) as other:
            assert other.items.list() == (), "antes do commit, ninguém mais vê"
        uow.commit()
    with MemoryUnitOfWork(state) as uow:
        assert uow.items.get(saved.id) == saved


def test_leaving_without_commit_discards_everything() -> None:
    state = MemoryState()
    with MemoryUnitOfWork(state) as uow:
        uow.items.add(item())
        uow.movements.append(receipt(ItemId(uuid4())))
    assert state.items == {}
    assert state.movements == []


def _add_then_fail(uow: MemoryUnitOfWork) -> None:
    with uow:
        uow.items.add(item())
        raise ZeroDivisionError


def test_exception_discards_and_propagates() -> None:
    state = MemoryState()
    with pytest.raises(ZeroDivisionError):
        _add_then_fail(MemoryUnitOfWork(state))
    assert state.items == {}


def test_rollback_discards_and_the_block_can_continue() -> None:
    state = MemoryState()
    kept, dropped = item("KEEP-1"), item("DROP-1")
    with MemoryUnitOfWork(state) as uow:
        uow.items.add(dropped)
        uow.rollback()
        assert uow.items.list() == ()
        uow.items.add(kept)
        uow.commit()
        uow.items.add(item("AFTER-1"))
    assert list(state.items.values()) == [kept]


def test_unit_of_work_must_be_open() -> None:
    uow = MemoryUnitOfWork()
    with pytest.raises(RuntimeError, match="with"):
        _ = uow.items
    with pytest.raises(RuntimeError, match="with"):
        uow.commit()
    with pytest.raises(RuntimeError, match="with"):
        uow.rollback()
    with uow, pytest.raises(RuntimeError, match="aninhados"), uow:
        pass


def test_committed_state_is_isolated_from_later_work() -> None:
    state = MemoryState()
    with MemoryUnitOfWork(state) as uow:
        uow.items.add(item())
        uow.commit()
        uow.items.add(item("NOVO-1"))
        assert len(state.items) == 1, "o que veio depois do commit ainda é rascunho"


@pytest.mark.req("RF-005")
@given(st.lists(st.sampled_from(["append", "commit", "rollback"]), max_size=30))
def test_ledger_keeps_exactly_the_committed_appends(operations: list[str]) -> None:
    """Modelo simples: só sobrevive o que foi lançado antes de um commit."""
    state = MemoryState()
    committed: list[Movement] = []
    pending: list[Movement] = []
    with MemoryUnitOfWork(state) as uow:
        for operation in operations:
            if operation == "append":
                movement = receipt(ItemId(uuid4()))
                uow.movements.append(movement)
                pending.append(movement)
            elif operation == "commit":
                uow.commit()
                committed += pending
                pending = []
            else:
                uow.rollback()
                pending = []
    assert state.movements == committed


# --- relógios ----------------------------------------------------------------------------


def test_fixed_clock_stays_put_until_advanced() -> None:
    brasilia = timezone(timedelta(hours=-3))
    clock = FixedClock(datetime(2026, 10, 27, 9, tzinfo=brasilia))
    assert clock.now() == WHEN
    assert clock.now().tzinfo is UTC
    clock.advance(timedelta(minutes=5))
    assert clock.now() == WHEN + timedelta(minutes=5)


def test_fixed_clock_rejects_naive_time_and_going_back() -> None:
    with pytest.raises(ValueError, match="fuso"):
        FixedClock(datetime(2026, 10, 27))  # noqa: DTZ001
    with pytest.raises(ValueError, match="volta"):
        FixedClock(WHEN).advance(timedelta(seconds=-1))


def test_system_clock_is_utc_and_current() -> None:
    before = datetime.now(UTC)
    now = SystemClock().now()
    assert now.tzinfo is UTC
    assert before <= now <= datetime.now(UTC)
