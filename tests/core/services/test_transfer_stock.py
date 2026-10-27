"""Transferência atômica (M1.8, RF-005, INV-03, INV-05; caso TP-M1-02)."""

import contextlib
from collections import Counter
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from hypothesis import given
from hypothesis import strategies as st

from adapters.clock import FixedClock
from adapters.memory.repositories import MemoryMovementRepository, MemoryState
from adapters.memory.unit_of_work import MemoryUnitOfWork
from core.domain.catalog import Item, ItemKind
from core.domain.errors import (
    InactiveRecordError,
    IncompatibleUnitsError,
    InsufficientStockError,
    NotFoundError,
    ValidationError,
)
from core.domain.ids import ItemId, LotId
from core.domain.ledger import in_ledger_order
from core.domain.location import Location
from core.domain.movement import Movement, MovementKind, check_transfer_pair
from core.domain.policy import NegativeStockPolicy
from core.domain.quantity import STANDARD_UNITS, Quantity, UnitOfMeasure
from core.services.balances import item_balance
from core.services.movements import (
    RecordMovement,
    TransferStock,
    record_movement,
    transfer_stock,
)

pytestmark = pytest.mark.req("RF-005")

UN, DZ, KG = STANDARD_UNITS["un"], STANDARD_UNITS["dz"], STANDARD_UNITS["kg"]
NOW = datetime(2026, 10, 27, 15, tzinfo=UTC)


class Stock:
    def __init__(self) -> None:
        self.state = MemoryState()
        self.clock = FixedClock(NOW)
        self.item = Item(sku="PAR-001", name="Parafuso", kind=ItemKind.RESALE, base_unit=UN)
        self.deposito = Location(name="Depósito")
        self.loja = Location(name="Loja")
        self.oficina = Location(name="Oficina")
        self.locations = [self.deposito, self.loja, self.oficina]
        with self.uow() as uow:
            uow.items.add(self.item)
            for location in self.locations:
                uow.locations.add(location)
            uow.commit()

    def uow(self) -> MemoryUnitOfWork:
        return MemoryUnitOfWork(self.state)

    def receive(self, value: int, location: Location, *, days_ago: int = 10) -> None:
        record_movement(
            self.uow(),
            self.clock,
            RecordMovement(
                kind=MovementKind.RECEIPT,
                item_id=self.item.id,
                location_id=location.id,
                quantity=Quantity(Decimal(value), UN),
                occurred_at=NOW - timedelta(days=days_ago),
                author="Ana",
            ),
        )

    def transfer(
        self,
        value: str,
        source: Location,
        target: Location,
        *,
        unit: UnitOfMeasure = UN,
        uow: MemoryUnitOfWork | None = None,
        policy: NegativeStockPolicy = NegativeStockPolicy.FORBID,
        **changes: object,
    ) -> tuple[Movement, Movement]:
        data: dict[str, object] = {
            "item_id": self.item.id,
            "from_location": source.id,
            "to_location": target.id,
            "quantity": Quantity(Decimal(value), unit),
            "author": "Ana",
        }
        data |= changes
        return transfer_stock(uow or self.uow(), self.clock, TransferStock(**data), policy=policy)  # type: ignore[arg-type]

    def at(self, location: Location) -> Decimal:
        return item_balance(
            self.uow(), self.item.id, location_id=location.id, include_sublocations=False
        ).value

    def total(self) -> Decimal:
        return item_balance(self.uow(), self.item.id).value


def dec(*values: int) -> tuple[Decimal, ...]:
    return tuple(Decimal(v) for v in values)


@pytest.fixture
def stock() -> Stock:
    s = Stock()
    s.receive(10, s.deposito)
    return s


# --- exemplos ----------------------------------------------------------------------------


def test_transfer_moves_stock_and_keeps_the_total(stock: Stock) -> None:
    outgoing, incoming = stock.transfer("4", stock.deposito, stock.loja, reason="reposição")
    assert (stock.at(stock.deposito), stock.at(stock.loja), stock.total()) == dec(6, 4, 10)
    check_transfer_pair(outgoing, incoming)
    assert outgoing.recorded_at == incoming.recorded_at == NOW
    assert outgoing.reason == incoming.reason == "reposição"
    assert outgoing.transfer_id is not None
    with stock.uow() as uow:
        assert uow.movements.transfer_pair(outgoing.transfer_id) == (outgoing, incoming)


def test_quantity_is_converted_to_the_base_unit(stock: Stock) -> None:
    outgoing, _ = stock.transfer("0.5", stock.deposito, stock.loja, unit=DZ)
    assert outgoing.quantity == Quantity(Decimal(6), UN)
    with pytest.raises(IncompatibleUnitsError):
        stock.transfer("1", stock.deposito, stock.loja, unit=KG)


def test_backdated_transfer_keeps_occurred_and_recorded_dates(stock: Stock) -> None:
    yesterday = NOW - timedelta(days=1)
    outgoing, incoming = stock.transfer("1", stock.deposito, stock.loja, occurred_at=yesterday)
    assert outgoing.occurred_at == incoming.occurred_at == yesterday
    assert outgoing.recorded_at == NOW


@pytest.mark.req("RF-007")
def test_origin_balance_follows_the_policy(stock: Stock) -> None:
    with pytest.raises(InsufficientStockError, match=r"'Depósito'.*-1 un"):
        stock.transfer("11", stock.deposito, stock.loja)
    assert (stock.at(stock.deposito), stock.at(stock.loja)) == dec(10, 0)
    stock.transfer("11", stock.deposito, stock.loja, policy=NegativeStockPolicy.ALLOW)
    assert (stock.at(stock.deposito), stock.at(stock.loja), stock.total()) == dec(-1, 11, 10)


@pytest.mark.req("RF-007")
def test_backdated_transfer_cannot_break_a_later_point_at_the_origin(stock: Stock) -> None:
    record_movement(
        stock.uow(),
        stock.clock,
        RecordMovement(
            kind=MovementKind.ISSUE,
            item_id=stock.item.id,
            location_id=stock.deposito.id,
            quantity=Quantity(Decimal(8), UN),
            occurred_at=NOW - timedelta(days=1),
            author="Ana",
        ),
    )
    with pytest.raises(InsufficientStockError):
        stock.transfer("5", stock.deposito, stock.loja, occurred_at=NOW - timedelta(days=5))


def test_same_location_is_refused(stock: Stock) -> None:
    with pytest.raises(ValidationError, match="locais diferentes"):
        stock.transfer("1", stock.deposito, stock.deposito)


@pytest.mark.parametrize("which", ["item", "origin", "destination"])
def test_inactive_records_are_refused(stock: Stock, which: str) -> None:
    with stock.uow() as uow:
        if which == "item":
            uow.items.update(stock.item.deactivated())
        else:
            target = stock.deposito if which == "origin" else stock.loja
            uow.locations.update(target.deactivated())
        uow.commit()
    with pytest.raises(InactiveRecordError):
        stock.transfer("1", stock.deposito, stock.loja)


def test_unknown_records_are_refused(stock: Stock) -> None:
    ghost = Location(name="Fantasma")
    with pytest.raises(NotFoundError):
        stock.transfer("1", stock.deposito, ghost)
    with pytest.raises(NotFoundError):
        stock.transfer("1", stock.deposito, stock.loja, item_id=ItemId(uuid4()))


def test_lot_rules_apply(stock: Stock) -> None:
    with pytest.raises(ValidationError, match="não controla lote"):
        stock.transfer("1", stock.deposito, stock.loja, lot_id=LotId(uuid4()))


# --- atomicidade -------------------------------------------------------------------------


class _FailingLedger(MemoryMovementRepository):
    """Livro que quebra ao gravar a ponta de entrada — simula queda no meio da transferência."""

    def append(self, movement: Movement) -> None:
        if movement.kind is MovementKind.TRANSFER_IN:
            raise OSError("disco cheio")
        super().append(movement)


class _FailingUnitOfWork(MemoryUnitOfWork):
    @property
    def movements(self) -> MemoryMovementRepository:
        return _FailingLedger(self._require_open().movements)


def test_failure_on_the_second_side_leaves_nothing_recorded(stock: Stock) -> None:
    before = list(stock.state.movements)
    with pytest.raises(OSError, match="disco cheio"):
        stock.transfer("4", stock.deposito, stock.loja, uow=_FailingUnitOfWork(stock.state))
    assert stock.state.movements == before, "sem meia transferência"
    assert (stock.at(stock.deposito), stock.at(stock.loja)) == dec(10, 0)


# --- propriedade (INV-03, TP-M1-02) ------------------------------------------------------


@given(
    st.lists(
        st.tuples(
            st.integers(min_value=0, max_value=2),
            st.integers(min_value=0, max_value=2),
            st.integers(min_value=1, max_value=8),
            st.integers(min_value=0, max_value=9),
        ),
        max_size=25,
    )
)
def test_random_transfers_conserve_the_total_and_never_go_negative(
    operations: list[tuple[int, int, int, int]],
) -> None:
    """INV-03 e INV-05: total constante, nenhum local negativo, nenhum par pela metade."""
    s = Stock()
    s.receive(10, s.deposito)
    for source, target, value, days_ago in operations:
        with contextlib.suppress(InsufficientStockError, ValidationError):
            s.transfer(
                str(value),
                s.locations[source],
                s.locations[target],
                occurred_at=NOW - timedelta(days=days_ago),
            )
    assert s.total() == 10
    sides = Counter(m.transfer_id for m in s.state.movements if m.transfer_id is not None)
    assert all(count == 2 for count in sides.values())
    for location in s.locations:
        running = Decimal(0)
        for m in in_ledger_order(x for x in s.state.movements if x.location_id == location.id):
            running += m.signed_quantity.value
            assert running >= 0
