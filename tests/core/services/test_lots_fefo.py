"""Lotes, validade e FEFO (M1.9, RF-008, INV-06; caso TP-M1-05)."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from hypothesis import given
from hypothesis import strategies as st

from adapters.clock import FixedClock
from adapters.memory.repositories import MemoryState
from adapters.memory.unit_of_work import MemoryUnitOfWork
from core.domain.catalog import Item, ItemKind
from core.domain.errors import ConflictError, InsufficientStockError, NotFoundError, ValidationError
from core.domain.ids import LotId
from core.domain.location import Location
from core.domain.lot import Lot, fefo_order
from core.domain.movement import Movement, MovementKind
from core.domain.policy import NegativeStockPolicy
from core.domain.quantity import STANDARD_UNITS, Quantity
from core.services.balances import balances_by_lot
from core.services.lots import CreateLot, create_lot
from core.services.movements import RecordMovement, TransferStock, record_movement, transfer_stock

pytestmark = pytest.mark.req("RF-008")

UN = STANDARD_UNITS["un"]
NOW = datetime(2026, 10, 27, 15, tzinfo=UTC)
TODAY = NOW.date()
IN, OUT = MovementKind.RECEIPT, MovementKind.ISSUE


class Dairy:
    """Leite (controla lote e validade), café (só lote) e parafuso (sem lote), numa loja."""

    def __init__(self) -> None:
        self.state = MemoryState()
        self.clock = FixedClock(NOW)
        self.milk = Item(
            sku="LEITE",
            name="Leite",
            kind=ItemKind.RESALE,
            base_unit=UN,
            tracks_lots=True,
            tracks_expiry=True,
        )
        self.coffee = Item(
            sku="CAFE", name="Café", kind=ItemKind.RESALE, base_unit=UN, tracks_lots=True
        )
        self.screw = Item(sku="PAR", name="Parafuso", kind=ItemKind.RESALE, base_unit=UN)
        self.shop = Location(name="Loja")
        self.backroom = Location(name="Depósito")
        with self.uow() as uow:
            for item in (self.milk, self.coffee, self.screw):
                uow.items.add(item)
            uow.locations.add(self.shop)
            uow.locations.add(self.backroom)
            uow.commit()

    def uow(self) -> MemoryUnitOfWork:
        return MemoryUnitOfWork(self.state)

    def lot(self, code: str, expires: date | None, item: Item | None = None) -> Lot:
        return create_lot(
            self.uow(), CreateLot(item_id=(item or self.milk).id, code=code, expires_on=expires)
        )

    def record(
        self,
        kind: MovementKind,
        value: int,
        *,
        lot: Lot | None = None,
        item: Item | None = None,
        location: Location | None = None,
        days_ago: int = 0,
        policy: NegativeStockPolicy = NegativeStockPolicy.FORBID,
    ) -> tuple[Movement, ...]:
        return record_movement(
            self.uow(),
            self.clock,
            RecordMovement(
                kind=kind,
                item_id=(item or self.milk).id,
                location_id=(location or self.shop).id,
                quantity=Quantity(Decimal(value), UN),
                occurred_at=NOW - timedelta(days=days_ago),
                author="Ana",
                lot_id=lot.id if lot else None,
                reason="baixa" if kind.requires_reason else None,
            ),
            policy=policy,
        )

    def by_lot(self, location: Location | None = None) -> dict[str, Decimal]:
        balances = balances_by_lot(self.uow(), self.milk.id, location_id=(location or self.shop).id)
        codes = {lot.id: lot.code for lot in self.state.lots.values()}
        return {codes[k]: v.value for k, v in balances.items() if k is not None}


def taken(movements: tuple[Movement, ...], lots: dict[LotId, str]) -> list[tuple[str, int]]:
    return [(lots[m.lot_id], int(m.quantity.value)) for m in movements if m.lot_id is not None]


@pytest.fixture
def dairy() -> Dairy:
    return Dairy()


# --- cadastro de lote --------------------------------------------------------------------


def test_create_lot_rules(dairy: Dairy) -> None:
    milk = dairy.lot(" l1 ", TODAY + timedelta(days=5))
    assert (milk.code, milk.item_id) == ("L1", dairy.milk.id)
    assert dairy.state.lots == {milk.id: milk}
    with pytest.raises(ValidationError, match="controla validade"):
        dairy.lot("L2", None)
    with pytest.raises(ValidationError, match="não controla validade"):
        dairy.lot("C1", TODAY, item=dairy.coffee)
    with pytest.raises(ValidationError, match="não controla lote"):
        dairy.lot("P1", None, item=dairy.screw)
    with pytest.raises(ConflictError, match="L1"):
        dairy.lot("L1", TODAY)
    assert dairy.lot("L1", None, item=dairy.coffee).code == "L1", "mesmo código, outro item"


def test_lot_must_exist_and_belong_to_the_item(dairy: Dairy) -> None:
    coffee_lot = dairy.lot("C1", None, item=dairy.coffee)
    with pytest.raises(ValidationError, match="não é do item LEITE"):
        dairy.record(IN, 1, lot=coffee_lot)
    with pytest.raises(NotFoundError):
        record_movement(
            dairy.uow(),
            dairy.clock,
            RecordMovement(
                kind=IN,
                item_id=dairy.milk.id,
                location_id=dairy.shop.id,
                quantity=Quantity(Decimal(1), UN),
                author="Ana",
                lot_id=LotId(uuid4()),
            ),
        )
    assert dairy.state.movements == []


def test_receipt_of_a_lot_item_requires_the_lot(dairy: Dairy) -> None:
    with pytest.raises(ValidationError, match="informe o lote"):
        dairy.record(IN, 1)


# --- FEFO (TP-M1-05) ---------------------------------------------------------------------


def test_fefo_consumes_in_expiry_order_across_three_lots(dairy: Dairy) -> None:
    late = dairy.lot("TARDE", TODAY + timedelta(days=30))
    soon = dairy.lot("CEDO", TODAY + timedelta(days=2))
    middle = dairy.lot("MEIO", TODAY + timedelta(days=10))
    for lot in (late, soon, middle):
        dairy.record(IN, 5, lot=lot, days_ago=3)
    issued = dairy.record(OUT, 8)
    codes = {lot.id: lot.code for lot in (late, soon, middle)}
    assert taken(issued, codes) == [("CEDO", 5), ("MEIO", 3)]
    assert dairy.by_lot() == {"TARDE": 5, "CEDO": 0, "MEIO": 2}
    assert len({m.recorded_at for m in issued}) == 1
    assert all(m.kind is OUT for m in issued)


def test_fefo_skips_expired_lots_and_says_so(dairy: Dairy) -> None:
    expired = dairy.lot("VENCIDO", TODAY - timedelta(days=1))
    valid = dairy.lot("BOM", TODAY + timedelta(days=5))
    dairy.record(IN, 4, lot=expired, days_ago=10)
    dairy.record(IN, 3, lot=valid, days_ago=10)
    assert taken(dairy.record(OUT, 2), {valid.id: "BOM"}) == [("BOM", 2)]
    with pytest.raises(InsufficientStockError, match=r"faltam 1 un; há 4 un em lote\(s\) vencido"):
        dairy.record(OUT, 2)
    dairy.record(MovementKind.LOSS, 4, lot=expired)
    assert dairy.by_lot() == {"VENCIDO": 0, "BOM": 1}


def test_lot_valid_on_its_expiry_day_is_used(dairy: Dairy) -> None:
    today_lot = dairy.lot("HOJE", TODAY)
    dairy.record(IN, 2, lot=today_lot, days_ago=1)
    assert taken(dairy.record(OUT, 2), {today_lot.id: "HOJE"}) == [("HOJE", 2)]


def test_fefo_uses_the_date_of_the_output(dairy: Dairy) -> None:
    """Saída retroativa: o lote vencido hoje ainda valia naquele dia."""
    lot = dairy.lot("ONTEM", TODAY - timedelta(days=1))
    dairy.record(IN, 3, lot=lot, days_ago=5)
    assert taken(dairy.record(OUT, 1, days_ago=2), {lot.id: "ONTEM"}) == [("ONTEM", 1)]
    with pytest.raises(InsufficientStockError):
        dairy.record(OUT, 1)


def test_fefo_does_not_take_what_a_later_output_needs(dairy: Dairy) -> None:
    soon = dairy.lot("CEDO", TODAY + timedelta(days=5))
    late = dairy.lot("TARDE", TODAY + timedelta(days=9))
    dairy.record(IN, 5, lot=soon, days_ago=10)
    dairy.record(IN, 5, lot=late, days_ago=10)
    dairy.record(OUT, 4, lot=soon, days_ago=1)
    issued = dairy.record(OUT, 3, days_ago=5)
    assert taken(issued, {soon.id: "CEDO", late.id: "TARDE"}) == [("CEDO", 1), ("TARDE", 2)]


def test_fefo_is_per_location(dairy: Dairy) -> None:
    soon = dairy.lot("CEDO", TODAY + timedelta(days=1))
    late = dairy.lot("TARDE", TODAY + timedelta(days=9))
    dairy.record(IN, 5, lot=soon, location=dairy.backroom, days_ago=1)
    dairy.record(IN, 5, lot=late, days_ago=1)
    assert taken(dairy.record(OUT, 2), {late.id: "TARDE"}) == [("TARDE", 2)]


def test_shortage_with_forbid_records_nothing(dairy: Dairy) -> None:
    lot = dairy.lot("L1", TODAY + timedelta(days=3))
    dairy.record(IN, 2, lot=lot, days_ago=1)
    before = list(dairy.state.movements)
    with pytest.raises(InsufficientStockError, match="faltam 3 un"):
        dairy.record(OUT, 5)
    assert dairy.state.movements == before


def test_allow_puts_the_shortage_on_the_last_valid_lot(dairy: Dairy) -> None:
    soon = dairy.lot("CEDO", TODAY + timedelta(days=1))
    late = dairy.lot("TARDE", TODAY + timedelta(days=9))
    dairy.record(IN, 2, lot=soon, days_ago=1)
    dairy.record(IN, 1, lot=late, days_ago=1)
    issued = dairy.record(OUT, 5, policy=NegativeStockPolicy.ALLOW)
    assert taken(issued, {soon.id: "CEDO", late.id: "TARDE"}) == [("CEDO", 2), ("TARDE", 3)]
    only = dairy.record(OUT, 1, policy=NegativeStockPolicy.ALLOW)
    assert taken(only, {late.id: "TARDE"}) == [("TARDE", 1)]
    assert dairy.by_lot() == {"CEDO": 0, "TARDE": -3}


def test_allow_without_any_valid_lot_is_refused(dairy: Dairy) -> None:
    with pytest.raises(InsufficientStockError):
        dairy.record(OUT, 1, policy=NegativeStockPolicy.ALLOW)


def test_lots_without_expiry_follow_code_order(dairy: Dairy) -> None:
    b = dairy.lot("B", None, item=dairy.coffee)
    a = dairy.lot("A", None, item=dairy.coffee)
    dairy.record(IN, 2, lot=b, item=dairy.coffee, days_ago=1)
    dairy.record(IN, 2, lot=a, item=dairy.coffee, days_ago=1)
    assert taken(dairy.record(OUT, 3, item=dairy.coffee), {a.id: "A", b.id: "B"}) == [
        ("A", 2),
        ("B", 1),
    ]


def test_transfer_of_a_lot_item_requires_the_lot(dairy: Dairy) -> None:
    lot = dairy.lot("L1", TODAY + timedelta(days=3))
    dairy.record(IN, 2, lot=lot, days_ago=1)
    command = TransferStock(
        item_id=dairy.milk.id,
        from_location=dairy.shop.id,
        to_location=dairy.backroom.id,
        quantity=Quantity(Decimal(1), UN),
        author="Ana",
    )
    with pytest.raises(ValidationError, match="informe o lote"):
        transfer_stock(dairy.uow(), dairy.clock, command)
    transfer_stock(
        dairy.uow(),
        dairy.clock,
        TransferStock(
            item_id=command.item_id,
            from_location=command.from_location,
            to_location=command.to_location,
            quantity=command.quantity,
            author="Ana",
            lot_id=lot.id,
        ),
    )
    assert dairy.by_lot(dairy.backroom) == {"L1": 1}


# --- propriedade (INV-06) ----------------------------------------------------------------


@given(
    stocks=st.lists(
        st.tuples(st.integers(min_value=-3, max_value=20), st.integers(min_value=0, max_value=6)),
        min_size=1,
        max_size=6,
    ),
    wanted=st.integers(min_value=1, max_value=40),
)
def test_fefo_never_skips_a_valid_lot_that_still_had_stock(
    stocks: list[tuple[int, int]], wanted: int
) -> None:
    """INV-06: só se consome um lote quando todos os válidos que vencem antes ficaram vazios."""
    dairy = Dairy()
    lots = []
    for index, (expires_in, amount) in enumerate(stocks):
        lot = dairy.lot(f"L{index}", TODAY + timedelta(days=expires_in))
        lots.append(lot)
        if amount:
            dairy.record(IN, amount, lot=lot, days_ago=1)
    valid = [lot for lot in fefo_order(lots) if not lot.is_expired_on(TODAY)]
    valid_stock = sum(amount for (expires_in, amount) in stocks if expires_in >= 0)
    try:
        issued = dairy.record(OUT, wanted)
    except InsufficientStockError:
        assert wanted > valid_stock
        return
    assert wanted <= valid_stock
    assert sum(m.quantity.value for m in issued) == wanted
    used = {m.lot_id for m in issued}
    assert used <= {lot.id for lot in valid}, "nenhum lote vencido"
    remaining = dairy.by_lot()
    last_used = max(i for i, lot in enumerate(valid) if lot.id in used)
    for lot in valid[:last_used]:
        assert remaining.get(lot.code, Decimal(0)) == 0, f"{lot.code} ficou com saldo"


def test_fefo_shortage_details(dairy: Dairy) -> None:
    lot = dairy.lot("L1", TODAY + timedelta(days=3))
    dairy.record(IN, 2, lot=lot, days_ago=1)
    with pytest.raises(InsufficientStockError) as error:
        dairy.record(OUT, 5)
    assert error.value.details["missing"] == Quantity(Decimal(3), UN)
    details = error.value.to_dict()["details"]
    assert isinstance(details, dict)
    assert details["missing"] == "3 un"
