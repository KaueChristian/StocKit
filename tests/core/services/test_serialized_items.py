"""Itens serializados nos serviços (M1.10, RF-009, INV-07; caso TP-M1-06)."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from adapters.clock import FixedClock
from adapters.memory.repositories import MemoryState
from adapters.memory.unit_of_work import MemoryUnitOfWork
from core.domain.catalog import Item, ItemKind
from core.domain.errors import InsufficientStockError, SerialNumberError, ValidationError
from core.domain.location import Location
from core.domain.movement import Movement, MovementKind
from core.domain.policy import NegativeStockPolicy
from core.domain.quantity import STANDARD_UNITS, Quantity
from core.domain.serials import serial_positions
from core.services.balances import balances_by_location, item_balance
from core.services.movements import RecordMovement, TransferStock, record_movement, transfer_stock
from core.services.serials import serial_location, serials_in_stock

pytestmark = pytest.mark.req("RF-009")

UN = STANDARD_UNITS["un"]
NOW = datetime(2026, 10, 27, 15, tzinfo=UTC)
IN, OUT = MovementKind.RECEIPT, MovementKind.ISSUE


class Shop:
    def __init__(self) -> None:
        self.state = MemoryState()
        self.clock = FixedClock(NOW)
        self.laptop = Item(sku="NOTE", name="Notebook", kind=ItemKind.SERIALIZED, base_unit=UN)
        self.screw = Item(sku="PAR", name="Parafuso", kind=ItemKind.RESALE, base_unit=UN)
        self.deposito = Location(name="Depósito")
        self.sala = Location(name="Sala TI", parent_id=self.deposito.id)
        self.loja = Location(name="Loja")
        self.locations = [self.deposito, self.sala, self.loja]
        with self.uow() as uow:
            uow.items.add(self.laptop)
            uow.items.add(self.screw)
            for location in self.locations:
                uow.locations.add(location)
            uow.commit()

    def uow(self) -> MemoryUnitOfWork:
        return MemoryUnitOfWork(self.state)

    def record(
        self,
        kind: MovementKind,
        *serials: str,
        quantity: str | None = None,
        at: Location | None = None,
        days_ago: int = 0,
        item: Item | None = None,
        policy: NegativeStockPolicy = NegativeStockPolicy.FORBID,
    ) -> tuple[Movement, ...]:
        return record_movement(
            self.uow(),
            self.clock,
            RecordMovement(
                kind=kind,
                item_id=(item or self.laptop).id,
                location_id=(at or self.loja).id,
                quantity=Quantity(Decimal(quantity or len(serials)), UN),
                occurred_at=NOW - timedelta(days=days_ago),
                author="Ana",
                serials=frozenset(serials),
                reason="conferência" if kind.requires_reason else None,
            ),
            policy=policy,
        )

    def move(self, source: Location, target: Location, *serials: str, days_ago: int = 0) -> None:
        transfer_stock(
            self.uow(),
            self.clock,
            TransferStock(
                item_id=self.laptop.id,
                from_location=source.id,
                to_location=target.id,
                quantity=Quantity(Decimal(len(serials)), UN),
                occurred_at=NOW - timedelta(days=days_ago),
                author="Ana",
                serials=frozenset(serials),
            ),
        )

    def where(self, serial: str, **kwargs: object) -> Location | None:
        found = serial_location(self.uow(), self.laptop.id, serial, **kwargs)  # type: ignore[arg-type]
        return next((loc for loc in self.locations if loc.id == found), None)


@pytest.fixture
def shop() -> Shop:
    s = Shop()
    s.record(IN, "SN-1", "SN-2", "SN-3", days_ago=10)
    return s


# --- TP-M1-06 ----------------------------------------------------------------------------


def test_repeated_serial_is_refused(shop: Shop) -> None:
    with pytest.raises(SerialNumberError, match=r"SN-1 de NOTE já está em 'Loja'"):
        shop.record(IN, "sn-1", at=shop.deposito)
    assert len(shop.state.movements) == 1


def test_fractional_quantity_is_refused(shop: Shop) -> None:
    with pytest.raises(ValidationError, match="fracionária") as error:
        shop.record(OUT, "SN-1", quantity="0.5")
    assert error.value.field == "quantity"


# --- regras ------------------------------------------------------------------------------


def test_serials_are_required_and_must_match_the_quantity(shop: Shop) -> None:
    with pytest.raises(ValidationError, match="informe os números de série"):
        shop.record(IN, quantity="1")
    with pytest.raises(ValidationError, match="igual ao número de séries"):
        shop.record(IN, "SN-9", quantity="2")


def test_non_serialized_item_refuses_serials(shop: Shop) -> None:
    with pytest.raises(ValidationError, match="não é serializado"):
        shop.record(IN, "X-1", item=shop.screw)


def test_issue_return_and_issue_again(shop: Shop) -> None:
    shop.record(OUT, "SN-1")
    assert shop.where("SN-1") is None
    with pytest.raises(SerialNumberError, match=r"não está em 'Loja'.*fora do estoque"):
        shop.record(OUT, "SN-1")
    shop.record(MovementKind.CUSTOMER_RETURN, "SN-1", at=shop.sala)
    assert shop.where("SN-1") == shop.sala
    shop.record(MovementKind.SUPPLIER_RETURN, "SN-1", at=shop.sala)
    assert shop.where("SN-1") is None


def test_issue_from_the_wrong_location_is_refused(shop: Shop) -> None:
    with pytest.raises(SerialNumberError, match=r"não está em 'Sala TI'.*está em 'Loja'"):
        shop.record(OUT, "SN-2", at=shop.sala)


def test_allow_policy_does_not_bypass_serials(shop: Shop) -> None:
    with pytest.raises(SerialNumberError):
        shop.record(OUT, "SN-404", policy=NegativeStockPolicy.ALLOW)


def test_backdated_movements_must_fit_the_serial_timeline(shop: Shop) -> None:
    shop.record(OUT, "SN-3", days_ago=2)
    with pytest.raises(SerialNumberError):
        shop.record(OUT, "SN-3", days_ago=5)
    with pytest.raises(SerialNumberError, match="já está"):
        shop.record(IN, "SN-3", at=shop.sala, days_ago=4)
    shop.record(IN, "SN-3", at=shop.sala, days_ago=1)


def test_transfer_moves_serials(shop: Shop) -> None:
    shop.move(shop.loja, shop.sala, "SN-1", "SN-2")
    assert (shop.where("SN-1"), shop.where("SN-3")) == (shop.sala, shop.loja)
    assert shop.where("SN-1", at=NOW - timedelta(days=1)) == shop.loja
    with pytest.raises(SerialNumberError):
        shop.move(shop.loja, shop.sala, "SN-1")
    with pytest.raises(ValidationError, match="informe os números de série"):
        transfer_stock(
            shop.uow(),
            shop.clock,
            TransferStock(
                item_id=shop.laptop.id,
                from_location=shop.loja.id,
                to_location=shop.sala.id,
                quantity=Quantity(Decimal(1), UN),
                author="Ana",
            ),
        )


def test_failed_serial_check_records_nothing(shop: Shop) -> None:
    before = list(shop.state.movements)
    with pytest.raises(SerialNumberError):
        shop.record(OUT, "SN-1", "SN-404")
    assert shop.state.movements == before


def test_forbid_policy_still_applies(shop: Shop) -> None:
    """A conferência de série é a mais forte; o saldo continua coerente com ela."""
    shop.record(OUT, "SN-1", "SN-2", "SN-3")
    with pytest.raises((SerialNumberError, InsufficientStockError)):
        shop.record(OUT, "SN-1")


# --- consultas ---------------------------------------------------------------------------


def test_serials_in_stock_by_location_and_date(shop: Shop) -> None:
    shop.move(shop.loja, shop.sala, "SN-1")
    shop.record(OUT, "SN-2")
    in_stock = serials_in_stock(shop.uow(), shop.laptop.id)
    assert in_stock == {"SN-1", "SN-3"}
    assert serials_in_stock(shop.uow(), shop.laptop.id, location_id=shop.deposito.id) == {"SN-1"}
    assert (
        serials_in_stock(
            shop.uow(), shop.laptop.id, location_id=shop.deposito.id, include_sublocations=False
        )
        == frozenset()
    )
    assert serials_in_stock(shop.uow(), shop.laptop.id, at=NOW - timedelta(days=11)) == frozenset()
    assert shop.where("never-seen") is None


# --- propriedade (INV-07) ----------------------------------------------------------------

SERIALS = [f"SN-{i}" for i in range(6)]


@given(
    st.lists(
        st.tuples(
            st.sampled_from(["in", "out", "move"]),
            st.lists(st.sampled_from(SERIALS), min_size=1, max_size=3, unique=True),
            st.integers(min_value=0, max_value=2),
            st.integers(min_value=0, max_value=2),
            st.integers(min_value=0, max_value=15),
        ),
        max_size=25,
    )
)
def test_a_serial_is_never_in_two_places_and_balances_are_whole(
    operations: list[tuple[str, list[str], int, int, int]],
) -> None:
    """INV-07: aceite ou recuse o que for, cada série está em um lugar só e o saldo é inteiro."""
    s = Shop()
    for action, serials, first, second, days_ago in operations:
        source, target = s.locations[first], s.locations[second]
        try:
            if action == "in":
                s.record(IN, *serials, at=source, days_ago=days_ago)
            elif action == "out":
                s.record(OUT, *serials, at=source, days_ago=days_ago)
            else:
                s.move(source, target, *serials, days_ago=days_ago)
        except SerialNumberError, InsufficientStockError, ValidationError:
            pass
    positions = serial_positions(s.state.movements)
    for location in s.locations:
        own = balances_by_location(s.uow(), s.laptop.id).get(location.id)
        expected = sum(1 for where in positions.values() if where == location.id)
        assert (own.value if own else 0) == expected
    total = item_balance(s.uow(), s.laptop.id).value
    assert total == total.to_integral_value() == sum(1 for w in positions.values() if w)
