"""Entidade Lote e ordem FEFO (M1.9, RF-008, INV-06)."""

from datetime import UTC, date, datetime
from uuid import uuid4

import pytest

from core.domain.errors import ValidationError
from core.domain.ids import ItemId
from core.domain.lot import LOT_CODE_MAX_LENGTH, Lot, fefo_order

pytestmark = pytest.mark.req("RF-008")

ITEM = ItemId(uuid4())


def lot(code: str, expires: date | None = None) -> Lot:
    return Lot(item_id=ITEM, code=code, expires_on=expires)


def test_code_is_trimmed_and_uppercased() -> None:
    assert lot("  l-2026a ").code == "L-2026A"


@pytest.mark.parametrize("code", ["", "  ", "L 1", "X" * (LOT_CODE_MAX_LENGTH + 1), 7])
def test_invalid_codes_are_refused(code: object) -> None:
    with pytest.raises(ValidationError) as error:
        lot(code)  # type: ignore[arg-type]
    assert error.value.field == "code"


@pytest.mark.parametrize(
    "value", [datetime(2026, 12, 1, tzinfo=UTC), "2026-12-01"], ids=["datetime", "texto"]
)
def test_expiry_must_be_a_plain_date(value: object) -> None:
    with pytest.raises(ValidationError) as error:
        lot("L1", value)  # type: ignore[arg-type]
    assert error.value.field == "expires_on"


def test_wrong_ids_are_refused() -> None:
    with pytest.raises(ValidationError):
        Lot(item_id="item", code="L1")  # type: ignore[arg-type]
    with pytest.raises(ValidationError):
        Lot(item_id=ITEM, code="L1", id="x")  # type: ignore[arg-type]


def test_expiry_day_is_still_valid() -> None:
    milk = lot("L1", date(2026, 10, 27))
    assert not milk.is_expired_on(date(2026, 10, 26))
    assert not milk.is_expired_on(date(2026, 10, 27))
    assert milk.is_expired_on(date(2026, 10, 28))
    assert not lot("SEM").is_expired_on(date(2999, 1, 1))


def test_fefo_order_puts_soonest_expiry_first_and_no_expiry_last() -> None:
    late, soon, none_b, none_a, tie_b, tie_a = (
        lot("TARDE", date(2027, 1, 1)),
        lot("CEDO", date(2026, 11, 1)),
        lot("B"),
        lot("A"),
        lot("EMPATE-B", date(2026, 12, 1)),
        lot("EMPATE-A", date(2026, 12, 1)),
    )
    assert fefo_order([late, none_b, soon, tie_b, none_a, tie_a]) == [
        soon,
        tie_a,
        tie_b,
        late,
        none_a,
        none_b,
    ]
