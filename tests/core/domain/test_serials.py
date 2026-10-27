"""Números de série na movimentação e na linha do tempo (M1.10, RF-009, INV-07)."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from core.domain.errors import ValidationError
from core.domain.ids import ItemId, LocationId
from core.domain.movement import SERIAL_MAX_LENGTH, Movement, MovementKind, make_transfer
from core.domain.quantity import STANDARD_UNITS, Quantity
from core.domain.serials import SerialProblem, first_serial_conflict, serial_positions

pytestmark = pytest.mark.req("RF-009")

UN = STANDARD_UNITS["un"]
T0 = datetime(2026, 10, 1, tzinfo=UTC)
ITEM = ItemId(uuid4())
SHOP, BACK = LocationId(uuid4()), LocationId(uuid4())
IN, OUT = MovementKind.RECEIPT, MovementKind.ISSUE


def mov(kind: MovementKind, *serials: str, day: int = 0, at: LocationId = SHOP) -> Movement:
    return Movement(
        kind=kind,
        item_id=ITEM,
        location_id=at,
        quantity=Quantity(Decimal(len(serials)), UN),
        occurred_at=T0 + timedelta(days=day),
        author="Ana",
        serials=frozenset(serials),
        reason="teste" if kind.requires_reason else None,
    )


# --- na movimentação ---------------------------------------------------------------------


def test_serials_are_normalized() -> None:
    assert mov(IN, " sn-1 ", "Sn-2").serials == {"SN-1", "SN-2"}
    plain = Movement(
        kind=IN,
        item_id=ITEM,
        location_id=SHOP,
        quantity=Quantity(Decimal("2.5"), UN),
        occurred_at=T0,
        author="Ana",
    )
    assert plain.serials == frozenset(), "sem séries, a quantidade é livre"


@pytest.mark.parametrize(
    "serials",
    [["SN 1"], [""], ["X" * (SERIAL_MAX_LENGTH + 1)], [1], "SN-1", None],
    ids=["espaco", "vazio", "longo", "numero", "texto-solto", "nada"],
)
def test_invalid_serials_are_refused(serials: object) -> None:
    with pytest.raises(ValidationError) as error:
        Movement(
            kind=IN,
            item_id=ITEM,
            location_id=SHOP,
            quantity=Quantity(Decimal(1), UN),
            occurred_at=T0,
            author="Ana",
            serials=serials,  # type: ignore[arg-type]
        )
    assert error.value.field == "serials"


def test_repeated_serial_in_one_movement_is_refused() -> None:
    with pytest.raises(ValidationError, match="repetido"):
        Movement(
            kind=IN,
            item_id=ITEM,
            location_id=SHOP,
            quantity=Quantity(Decimal(2), UN),
            occurred_at=T0,
            author="Ana",
            serials=["SN-1", "sn-1"],  # type: ignore[arg-type]
        )


@pytest.mark.parametrize("value", ["1", "3", "2.5"])
def test_quantity_must_match_the_number_of_serials(value: str) -> None:
    with pytest.raises(ValidationError, match="igual ao número de séries") as error:
        Movement(
            kind=IN,
            item_id=ITEM,
            location_id=SHOP,
            quantity=Quantity(Decimal(value), UN),
            occurred_at=T0,
            author="Ana",
            serials=frozenset({"A", "B"}),
        )
    assert error.value.field == "quantity"


def test_transfer_pair_carries_the_serials() -> None:
    outgoing, incoming = make_transfer(
        item_id=ITEM,
        from_location=SHOP,
        to_location=BACK,
        quantity=Quantity(Decimal(1), UN),
        occurred_at=T0,
        author="Ana",
        serials=frozenset({"SN-1"}),
    )
    assert outgoing.serials == incoming.serials == {"SN-1"}


# --- linha do tempo ----------------------------------------------------------------------


def test_positions_follow_the_last_movement_of_each_serial() -> None:
    history = [mov(IN, "A", "B", day=0), mov(OUT, "A", day=1), mov(IN, "C", day=2, at=BACK)]
    assert serial_positions(history) == {"A": None, "B": SHOP, "C": BACK}


def test_receiving_a_serial_already_in_stock_is_a_conflict() -> None:
    conflict = first_serial_conflict([mov(IN, "A", day=0)], [mov(IN, "A", day=1, at=BACK)])
    assert conflict is not None
    assert (conflict.serial, conflict.problem) == ("A", SerialProblem.ALREADY_IN_STOCK)
    assert (conflict.location_id, conflict.current) == (BACK, SHOP)


def test_issuing_a_serial_from_where_it_is_not_is_a_conflict() -> None:
    history = [mov(IN, "A", day=0, at=BACK)]
    conflict = first_serial_conflict(history, [mov(OUT, "A", day=1)])
    assert conflict is not None
    assert (conflict.problem, conflict.current) == (SerialProblem.NOT_HERE, BACK)
    never = first_serial_conflict([], [mov(OUT, "Z")])
    assert never is not None
    assert never.current is None


def test_a_serial_can_leave_and_come_back() -> None:
    history = [mov(IN, "A", day=0), mov(OUT, "A", day=1)]
    assert first_serial_conflict(history, [mov(MovementKind.CUSTOMER_RETURN, "A", day=2)]) is None


def test_backdated_entry_conflicts_with_a_later_one() -> None:
    """A entrou no dia 5. Lançar outra entrada de A no dia 2 deixaria A em dois lugares."""
    conflict = first_serial_conflict([mov(IN, "A", day=5)], [mov(IN, "A", day=2, at=BACK)])
    assert conflict is not None
    assert conflict.at == T0 + timedelta(days=5)


def test_transfer_pair_at_the_same_instant_is_consistent() -> None:
    outgoing, incoming = make_transfer(
        item_id=ITEM,
        from_location=SHOP,
        to_location=BACK,
        quantity=Quantity(Decimal(1), UN),
        occurred_at=T0 + timedelta(days=1),
        author="Ana",
        serials=frozenset({"A"}),
    )
    assert first_serial_conflict([mov(IN, "A", day=0)], [outgoing, incoming]) is None


def test_other_serials_in_history_are_ignored() -> None:
    broken = [mov(IN, "X", day=0), mov(IN, "X", day=1)]
    assert first_serial_conflict(broken, [mov(IN, "A", day=2)]) is None
