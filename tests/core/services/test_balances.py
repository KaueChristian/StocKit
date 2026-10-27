"""Consultas de saldo (M1.7, RF-006, INV-01, INV-08; casos TP-M1-01 e TP-M1-02)."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from hypothesis import given
from hypothesis import strategies as st

from adapters.memory.repositories import MemoryState
from adapters.memory.unit_of_work import MemoryUnitOfWork
from core.domain.catalog import Item, ItemKind
from core.domain.errors import NotFoundError
from core.domain.ids import ItemId, LocationId, LotId
from core.domain.location import Location
from core.domain.movement import Movement, MovementKind, make_transfer
from core.domain.quantity import STANDARD_UNITS, Quantity
from core.services.balances import balances_by_location, balances_by_lot, item_balance

pytestmark = pytest.mark.req("RF-006")

UN = STANDARD_UNITS["un"]
T0 = datetime(2026, 10, 1, tzinfo=UTC)
LOT_A, LOT_B = LotId(uuid4()), LotId(uuid4())


class Stock:
    """Depósito › Corredor A › Prateleira 1, e a Loja na raiz; um item com lote."""

    def __init__(self) -> None:
        self.state = MemoryState()
        self.item = Item(
            sku="LEITE", name="Leite", kind=ItemKind.RESALE, base_unit=UN, tracks_lots=True
        )
        self.other = Item(sku="CAFE", name="Café", kind=ItemKind.RESALE, base_unit=UN)
        self.deposito = Location(name="Depósito")
        self.corredor = Location(name="Corredor A", parent_id=self.deposito.id)
        self.prateleira = Location(name="Prateleira 1", parent_id=self.corredor.id)
        self.loja = Location(name="Loja")
        self.locations = [self.deposito, self.corredor, self.prateleira, self.loja]
        with self.uow() as uow:
            uow.items.add(self.item)
            uow.items.add(self.other)
            for location in self.locations:
                uow.locations.add(location)
            uow.commit()

    def uow(self) -> MemoryUnitOfWork:
        return MemoryUnitOfWork(self.state)

    def append(self, *movements: Movement) -> None:
        with self.uow() as uow:
            for movement in movements:
                uow.movements.append(movement)
            uow.commit()

    def mov(
        self,
        kind: MovementKind,
        value: int | str,
        location: Location,
        *,
        day: int = 0,
        lot: LotId | None = LOT_A,
        item: Item | None = None,
    ) -> Movement:
        return Movement(
            kind=kind,
            item_id=(item or self.item).id,
            location_id=location.id,
            quantity=Quantity(Decimal(value), UN),
            occurred_at=T0 + timedelta(days=day),
            author="Ana",
            lot_id=lot,
            reason="teste" if kind.requires_reason else None,
        )

    def balance(self, **kwargs: object) -> Decimal:
        return item_balance(self.uow(), self.item.id, **kwargs).value  # type: ignore[arg-type]


IN, OUT = MovementKind.RECEIPT, MovementKind.ISSUE


@pytest.fixture
def stock() -> Stock:
    s = Stock()
    s.append(
        s.mov(IN, 10, s.prateleira, day=0),
        s.mov(IN, 4, s.corredor, day=1, lot=LOT_B),
        s.mov(OUT, 3, s.prateleira, day=2),
        s.mov(IN, 6, s.loja, day=3),
        s.mov(IN, 100, s.loja, day=0, item=s.other, lot=None),
    )
    return s


# --- exemplos ----------------------------------------------------------------------------


def test_total_balance_is_the_signed_sum(stock: Stock) -> None:
    assert stock.balance() == 17
    assert item_balance(stock.uow(), stock.other.id) == Quantity(Decimal(100), UN)


def test_location_balance_includes_sublocations_by_default(stock: Stock) -> None:
    assert stock.balance(location_id=stock.deposito.id) == 11
    assert stock.balance(location_id=stock.corredor.id) == 11
    assert stock.balance(location_id=stock.prateleira.id) == 7
    assert stock.balance(location_id=stock.loja.id) == 6


def test_location_balance_without_sublocations(stock: Stock) -> None:
    assert stock.balance(location_id=stock.deposito.id, include_sublocations=False) == 0
    assert stock.balance(location_id=stock.corredor.id, include_sublocations=False) == 4


def test_lot_balance(stock: Stock) -> None:
    assert stock.balance(lot_id=LOT_A) == 13
    assert stock.balance(lot_id=LOT_B) == 4
    assert stock.balance(lot_id=LOT_A, location_id=stock.deposito.id) == 7


def test_balance_at_a_date_is_inclusive(stock: Stock) -> None:
    assert stock.balance(at=T0 - timedelta(seconds=1)) == 0
    assert stock.balance(at=T0) == 10
    assert stock.balance(at=T0 + timedelta(days=2)) == 11
    assert stock.balance(at=T0 + timedelta(days=2, seconds=-1)) == 14


def test_backdated_movement_changes_the_past_balance(stock: Stock) -> None:
    before = stock.balance(at=T0 + timedelta(days=1))
    stock.append(stock.mov(MovementKind.LOSS, 2, stock.prateleira, day=1))
    assert stock.balance(at=T0 + timedelta(days=1)) == before - 2


def test_balances_by_location_and_lot(stock: Stock) -> None:
    by_location = balances_by_location(stock.uow(), stock.item.id)
    assert {k: v.value for k, v in by_location.items()} == {
        stock.prateleira.id: 7,
        stock.corredor.id: 4,
        stock.loja.id: 6,
    }
    assert {k: v.value for k, v in balances_by_lot(stock.uow(), stock.item.id).items()} == {
        LOT_A: 13,
        LOT_B: 4,
    }
    in_shop = balances_by_lot(stock.uow(), stock.item.id, location_id=stock.loja.id)
    assert {k: v.value for k, v in in_shop.items()} == {LOT_A: 6}
    early = balances_by_location(stock.uow(), stock.item.id, at=T0)
    assert {k: v.value for k, v in early.items()} == {stock.prateleira.id: 10}


def test_location_that_went_to_zero_still_shows(stock: Stock) -> None:
    stock.append(stock.mov(OUT, 6, stock.loja, day=4))
    assert balances_by_location(stock.uow(), stock.item.id)[stock.loja.id].value == 0


def test_item_without_lot_shows_under_none() -> None:
    s = Stock()
    s.append(s.mov(IN, 5, s.loja, item=s.other, lot=None))
    assert {k: v.value for k, v in balances_by_lot(s.uow(), s.other.id).items()} == {None: 5}


def test_transfer_moves_stock_without_changing_the_total(stock: Stock) -> None:
    stock.append(
        *make_transfer(
            item_id=stock.item.id,
            from_location=stock.prateleira.id,
            to_location=stock.loja.id,
            quantity=Quantity(Decimal(5), UN),
            occurred_at=T0 + timedelta(days=5),
            author="Ana",
            lot_id=LOT_A,
        )
    )
    assert stock.balance() == 17
    assert stock.balance(location_id=stock.prateleira.id) == 2
    assert stock.balance(location_id=stock.loja.id) == 11


QUERIES: dict[str, Callable[[Stock, ItemId], object]] = {
    "total": lambda s, i: item_balance(s.uow(), i),
    "location": lambda s, i: item_balance(s.uow(), i, location_id=s.loja.id),
    "by_location": lambda s, i: balances_by_location(s.uow(), i),
    "by_lot": lambda s, i: balances_by_lot(s.uow(), i),
}


@pytest.mark.parametrize("query", QUERIES)
def test_unknown_item_is_an_error(stock: Stock, query: str) -> None:
    with pytest.raises(NotFoundError):
        QUERIES[query](stock, ItemId(uuid4()))


def test_unknown_location_is_an_error_not_zero(stock: Stock) -> None:
    with pytest.raises(NotFoundError):
        stock.balance(location_id=LocationId(uuid4()))
    with pytest.raises(NotFoundError):
        balances_by_lot(stock.uow(), stock.item.id, location_id=LocationId(uuid4()))


def test_queries_do_not_write(stock: Stock) -> None:
    before = list(stock.state.movements)
    stock.balance(location_id=stock.deposito.id)
    balances_by_location(stock.uow(), stock.item.id)
    assert stock.state.movements == before


# --- propriedades (TP-M1-01, TP-M1-02) ---------------------------------------------------

KINDS = [k for k in MovementKind if not k.is_transfer]


@st.composite
def ledgers(draw: st.DrawFn) -> tuple[Stock, list[Movement]]:
    """Livro aleatório com transferências; pode ficar negativo e o saldo tem de bater igual."""
    s = Stock()
    movements: list[Movement] = []
    for _ in range(draw(st.integers(min_value=0, max_value=30))):
        day = draw(st.integers(min_value=0, max_value=20))
        value = draw(st.integers(min_value=1, max_value=50))
        lot = draw(st.sampled_from([LOT_A, LOT_B]))
        if draw(st.integers(min_value=0, max_value=4)) == 0:
            source, target = draw(st.permutations(s.locations))[:2]
            movements += make_transfer(
                item_id=s.item.id,
                from_location=source.id,
                to_location=target.id,
                quantity=Quantity(Decimal(value), UN),
                occurred_at=T0 + timedelta(days=day),
                author="Ana",
                lot_id=lot,
            )
        else:
            kind = draw(st.sampled_from(KINDS))
            location = draw(st.sampled_from(s.locations))
            movements.append(s.mov(kind, value, location, day=day, lot=lot))
    s.append(*movements)
    return s, movements


def signed_sum(movements: list[Movement], at: datetime | None = None) -> Decimal:
    return sum(
        (m.signed_quantity.value for m in movements if at is None or m.occurred_at <= at),
        Decimal(0),
    )


@given(ledgers(), st.integers(min_value=-1, max_value=21))
def test_balance_equals_signed_sum_at_any_date(
    case: tuple[Stock, list[Movement]], day: int
) -> None:
    """INV-01: saldo == soma assinada, no total e em qualquer data."""
    stock, movements = case
    at = T0 + timedelta(days=day)
    assert stock.balance() == signed_sum(movements)
    assert stock.balance(at=at) == signed_sum(movements, at)


@given(ledgers())
def test_sum_by_location_and_by_lot_equals_total(case: tuple[Stock, list[Movement]]) -> None:
    """INV-08: a soma dos saldos por local (e por lote) é o saldo total."""
    stock, _ = case
    total = stock.balance()
    by_location = balances_by_location(stock.uow(), stock.item.id)
    by_lot = balances_by_lot(stock.uow(), stock.item.id)
    assert sum((q.value for q in by_location.values()), Decimal(0)) == total
    assert sum((q.value for q in by_lot.values()), Decimal(0)) == total


@given(ledgers())
def test_location_with_sublocations_is_the_sum_of_its_subtree(
    case: tuple[Stock, list[Movement]],
) -> None:
    stock, _ = case
    own = balances_by_location(stock.uow(), stock.item.id)

    def own_value(location: Location) -> Decimal:
        return own[location.id].value if location.id in own else Decimal(0)

    subtree = [stock.deposito, stock.corredor, stock.prateleira]
    assert stock.balance(location_id=stock.deposito.id) == sum(map(own_value, subtree))
    roots = stock.balance(location_id=stock.deposito.id) + stock.balance(location_id=stock.loja.id)
    assert roots == stock.balance()
