"""Movimentações imutáveis e seus tipos (M1.3, RF-005, INV-02, INV-03)."""

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from hypothesis import given
from hypothesis import strategies as st

from core.domain.errors import ValidationError
from core.domain.ids import ItemId, LocationId, LotId, PartyId, TransferId
from core.domain.movement import (
    Direction,
    Movement,
    MovementKind,
    check_transfer_pair,
    make_transfer,
)
from core.domain.quantity import SCALE, STANDARD_UNITS, Quantity

pytestmark = pytest.mark.req("RF-005")

UN = STANDARD_UNITS["un"]
ITEM = ItemId(uuid4())
SHOP = LocationId(uuid4())
BACKROOM = LocationId(uuid4())
WHEN = datetime(2026, 10, 27, 13, 30, tzinfo=UTC)

NON_TRANSFER_KINDS = [k for k in MovementKind if not k.is_transfer]


def qty(value: str) -> Quantity:
    return Quantity(Decimal(value), UN)


def make(kind: MovementKind = MovementKind.RECEIPT, **changes: object) -> Movement:
    data: dict[str, object] = {
        "kind": kind,
        "item_id": ITEM,
        "location_id": SHOP,
        "quantity": qty("5"),
        "occurred_at": WHEN,
        "author": "Ana",
    }
    if kind.requires_reason:
        data["reason"] = "contagem"
    if kind.is_transfer:
        data["transfer_id"] = TransferId(uuid4())
    data |= changes
    return Movement(**data)  # type: ignore[arg-type]


# --- tipos -------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("kind", "direction"),
    [
        (MovementKind.RECEIPT, Direction.IN),
        (MovementKind.ISSUE, Direction.OUT),
        (MovementKind.TRANSFER_OUT, Direction.OUT),
        (MovementKind.TRANSFER_IN, Direction.IN),
        (MovementKind.ADJUSTMENT_IN, Direction.IN),
        (MovementKind.ADJUSTMENT_OUT, Direction.OUT),
        (MovementKind.LOSS, Direction.OUT),
        (MovementKind.CUSTOMER_RETURN, Direction.IN),
        (MovementKind.SUPPLIER_RETURN, Direction.OUT),
    ],
)
def test_each_kind_has_a_fixed_direction(kind: MovementKind, direction: Direction) -> None:
    movement = make(kind)
    assert movement.direction is direction
    expected = movement.quantity if direction is Direction.IN else -movement.quantity
    assert movement.signed_quantity == expected


def test_kind_codes_are_unique_and_round_trip() -> None:
    codes = [k.code for k in MovementKind]
    assert len(codes) == len(set(codes)) == 9
    assert all(MovementKind.from_code(k.code) is k for k in MovementKind)
    with pytest.raises(ValidationError, match="desconhecido"):
        MovementKind.from_code("venda")


@given(
    st.sampled_from(list(MovementKind)),
    st.decimals(min_value="0.000001", max_value=10**6, places=SCALE),
)
def test_signed_quantity_has_the_size_of_the_quantity(kind: MovementKind, value: Decimal) -> None:
    movement = make(kind, quantity=qty(str(value)))
    signed = movement.signed_quantity
    assert abs(signed.value) == value
    assert (signed.value > 0) == (kind.direction is Direction.IN)


# --- imutabilidade (INV-02) --------------------------------------------------------------


def test_movement_cannot_be_changed() -> None:
    movement = make()
    with pytest.raises(FrozenInstanceError):
        movement.quantity = qty("50")  # type: ignore[misc]
    assert not any(name.startswith(("set", "update", "edit")) for name in dir(movement))


def test_a_copy_with_another_id_is_another_movement() -> None:
    movement = make()
    assert replace(movement) == movement
    assert make() != movement


# --- validação ---------------------------------------------------------------------------


@pytest.mark.parametrize("value", ["0", "-1", "-0.000001"])
def test_quantity_must_be_positive(value: str) -> None:
    with pytest.raises(ValidationError, match="positiva") as error:
        make(quantity=qty(value))
    assert error.value.field == "quantity"


@pytest.mark.parametrize("kind", [k for k in MovementKind if k.requires_reason])
@pytest.mark.parametrize("reason", [None, "", "   "])
def test_adjustment_and_loss_need_a_reason(kind: MovementKind, reason: str | None) -> None:
    with pytest.raises(ValidationError, match="motivo") as error:
        make(kind, reason=reason)
    assert error.value.field == "reason"


def test_requires_reason_is_exactly_adjustments_and_loss() -> None:
    assert {k for k in MovementKind if k.requires_reason} == {
        MovementKind.ADJUSTMENT_IN,
        MovementKind.ADJUSTMENT_OUT,
        MovementKind.LOSS,
    }


def test_reason_is_optional_elsewhere_and_cleaned() -> None:
    assert make(MovementKind.RECEIPT, reason="  ").reason is None
    assert make(MovementKind.ISSUE, reason="  pedido   42 ").reason == "pedido 42"
    with pytest.raises(ValidationError):
        make(MovementKind.ISSUE, reason="x" * 501)


@pytest.mark.parametrize("author", ["", "   ", None, "x" * 121])
def test_author_is_required(author: object) -> None:
    with pytest.raises(ValidationError) as error:
        make(author=author)
    assert error.value.field == "author"


def test_occurred_at_is_stored_in_utc() -> None:
    sao_paulo = timezone(timedelta(hours=-3))
    movement = make(occurred_at=datetime(2026, 10, 27, 10, 30, tzinfo=sao_paulo))
    assert movement.occurred_at == WHEN
    assert movement.occurred_at.tzinfo is UTC


@pytest.mark.parametrize(
    "value",
    [datetime(2026, 10, 27, 13, 30), "2026-10-27T13:30Z", 1_790_000_000],  # noqa: DTZ001
    ids=["sem-fuso", "texto", "numero"],
)
def test_occurred_at_must_be_an_aware_datetime(value: object) -> None:
    with pytest.raises(ValidationError) as error:
        make(occurred_at=value)
    assert error.value.field == "occurred_at"


@pytest.mark.parametrize("cost", ["0", "12.5", "0.000001", "12.500000000"])
def test_valid_unit_costs(cost: str) -> None:
    assert make(unit_cost=Decimal(cost)).unit_cost == Decimal(cost)


@pytest.mark.parametrize(
    "cost",
    [Decimal("-0.01"), Decimal("NaN"), Decimal("Infinity"), Decimal("0.0000001"), 12.5, "10"],
    ids=["negativo", "nan", "inf", "7-casas", "float", "texto"],
)
def test_invalid_unit_costs(cost: object) -> None:
    with pytest.raises(ValidationError) as error:
        make(unit_cost=cost)
    assert error.value.field == "unit_cost"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("kind", "receipt"),
        ("item_id", "PAR-001"),
        ("location_id", None),
        ("id", 7),
        ("lot_id", "L1"),
        ("party_id", "fornecedor"),
        ("quantity", Decimal(5)),
    ],
)
def test_wrong_types_are_refused(field: str, value: object) -> None:
    with pytest.raises(ValidationError) as error:
        replace(make(), **{field: value})  # type: ignore[arg-type]
    assert error.value.field == field


def test_optional_references_are_kept() -> None:
    lot, party = LotId(uuid4()), PartyId(uuid4())
    movement = make(lot_id=lot, party_id=party)
    assert (movement.lot_id, movement.party_id) == (lot, party)


@pytest.mark.parametrize("kind", NON_TRANSFER_KINDS)
def test_only_transfers_carry_a_transfer_id(kind: MovementKind) -> None:
    with pytest.raises(ValidationError, match="só transferência"):
        make(kind, transfer_id=TransferId(uuid4()))


@pytest.mark.parametrize("kind", [MovementKind.TRANSFER_IN, MovementKind.TRANSFER_OUT])
def test_transfer_side_needs_its_pair(kind: MovementKind) -> None:
    with pytest.raises(ValidationError, match="par"):
        make(kind, transfer_id=None)


# --- transferência (INV-03) --------------------------------------------------------------


def transfer(**changes: object) -> tuple[Movement, Movement]:
    data: dict[str, object] = {
        "item_id": ITEM,
        "from_location": SHOP,
        "to_location": BACKROOM,
        "quantity": qty("3"),
        "occurred_at": WHEN,
        "author": "Ana",
    }
    data |= changes
    return make_transfer(**data)  # type: ignore[arg-type]


def test_transfer_is_an_outgoing_and_an_incoming_pair() -> None:
    outgoing, incoming = transfer(lot_id=LotId(uuid4()), reason="reposição da loja")
    assert (outgoing.kind, outgoing.location_id) == (MovementKind.TRANSFER_OUT, SHOP)
    assert (incoming.kind, incoming.location_id) == (MovementKind.TRANSFER_IN, BACKROOM)
    assert outgoing.transfer_id == incoming.transfer_id is not None
    assert outgoing.id != incoming.id
    check_transfer_pair(outgoing, incoming)
    check_transfer_pair(incoming, outgoing)


def test_transfer_to_the_same_location_is_refused() -> None:
    with pytest.raises(ValidationError, match="locais diferentes"):
        transfer(to_location=SHOP)


def test_each_transfer_gets_its_own_pair_id() -> None:
    assert transfer()[0].transfer_id != transfer()[0].transfer_id


@given(st.decimals(min_value="0.000001", max_value=10**9, places=SCALE))
def test_transfer_conserves_the_total_quantity(value: Decimal) -> None:
    """INV-03: a soma assinada do par é zero; o item só muda de lugar."""
    outgoing, incoming = transfer(quantity=qty(str(value)))
    assert outgoing.signed_quantity + incoming.signed_quantity == Quantity.zero(UN)


@pytest.mark.parametrize(
    ("change", "field"),
    [
        ({"transfer_id": TransferId(uuid4())}, "transfer_id"),
        ({"item_id": ItemId(uuid4())}, "item_id"),
        ({"quantity": qty("4")}, "quantity"),
        ({"lot_id": LotId(uuid4())}, "lot_id"),
        ({"occurred_at": WHEN + timedelta(seconds=1)}, "occurred_at"),
    ],
)
def test_pair_check_finds_any_divergence(change: dict[str, object], field: str) -> None:
    outgoing, incoming = transfer()
    with pytest.raises(ValidationError, match="diverge") as error:
        check_transfer_pair(outgoing, replace(incoming, **change))  # type: ignore[arg-type]
    assert error.value.field == field


def test_pair_check_needs_one_out_and_one_in() -> None:
    outgoing, _ = transfer()
    with pytest.raises(ValidationError, match="uma saída e uma entrada"):
        check_transfer_pair(outgoing, outgoing)
    with pytest.raises(ValidationError, match="uma saída e uma entrada"):
        check_transfer_pair(make(), make(MovementKind.ISSUE))


def test_pair_check_refuses_same_location() -> None:
    outgoing, incoming = transfer()
    with pytest.raises(ValidationError, match="origem igual"):
        check_transfer_pair(outgoing, replace(incoming, location_id=SHOP))


def test_recorded_at_is_optional_utc_and_not_before_occurrence() -> None:
    assert make().recorded_at is None
    sao_paulo = timezone(timedelta(hours=-3))
    later = make(recorded_at=datetime(2026, 10, 27, 11, tzinfo=sao_paulo))
    assert later.recorded_at == WHEN + timedelta(minutes=30)
    assert later.recorded_at is not None
    assert later.recorded_at.tzinfo is UTC
    with pytest.raises(ValidationError, match="depois de ser registrada") as error:
        make(recorded_at=WHEN - timedelta(seconds=1))
    assert error.value.field == "occurred_at"
    with pytest.raises(ValidationError) as naive:
        make(recorded_at=datetime(2026, 10, 27, 14))  # noqa: DTZ001
    assert naive.value.field == "recorded_at"
