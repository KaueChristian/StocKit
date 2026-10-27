"""Cálculos sobre o livro (M1.6: saldo e primeiro ponto negativo; INV-01, INV-05)."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from core.domain.ids import ItemId, LocationId
from core.domain.ledger import available_at, balance, first_negative_from, in_ledger_order
from core.domain.movement import Movement, MovementKind
from core.domain.quantity import STANDARD_UNITS, Quantity

UN = STANDARD_UNITS["un"]
T0 = datetime(2026, 10, 1, tzinfo=UTC)
ITEM, SHOP = ItemId(uuid4()), LocationId(uuid4())


def mov(kind: MovementKind, value: str, day: int) -> Movement:
    return Movement(
        kind=kind,
        item_id=ITEM,
        location_id=SHOP,
        quantity=Quantity(Decimal(value), UN),
        occurred_at=T0 + timedelta(days=day),
        author="Ana",
        reason="teste" if kind.requires_reason else None,
    )


IN, OUT = MovementKind.RECEIPT, MovementKind.ISSUE


@pytest.mark.req("RF-006")
def test_balance_is_the_signed_sum() -> None:
    movements = [mov(IN, "10", 0), mov(OUT, "3", 1), mov(MovementKind.LOSS, "1.5", 2)]
    assert balance(movements, UN) == Quantity(Decimal("5.5"), UN)
    assert balance([], UN) == Quantity.zero(UN)


def test_ledger_order_is_by_date_then_arrival() -> None:
    a, b, c = mov(IN, "1", 2), mov(IN, "2", 1), mov(IN, "3", 1)
    assert in_ledger_order([a, b, c]) == [b, c, a]


@pytest.mark.req("RF-007")
def test_covered_output_has_no_negative_point() -> None:
    history = [mov(IN, "10", 0)]
    assert first_negative_from(history, mov(OUT, "10", 1), UN) is None


@pytest.mark.req("RF-007")
def test_output_above_balance_is_found_at_its_own_date() -> None:
    history = [mov(IN, "5", 0)]
    point = first_negative_from(history, mov(OUT, "7", 1), UN)
    assert point is not None
    assert point.at == T0 + timedelta(days=1)
    assert point.balance == Quantity(Decimal(-2), UN)


@pytest.mark.req("RF-007")
def test_backdated_output_can_break_a_later_point() -> None:
    """Dia 0 entra 10; dia 5 sai 8. Uma saída de 5 no dia 2 cabe no dia 2, mas o dia 5 fica -3."""
    history = [mov(IN, "10", 0), mov(OUT, "8", 5)]
    point = first_negative_from(history, mov(OUT, "5", 2), UN)
    assert point is not None
    assert point.at == T0 + timedelta(days=5)
    assert point.balance == Quantity(Decimal(-3), UN)


@pytest.mark.req("RF-007")
def test_negative_points_before_the_new_movement_are_not_its_fault() -> None:
    """Saldo já negativo no passado (política antiga permitia) não bloqueia uma entrada nova."""
    history = [mov(OUT, "4", 0)]
    assert first_negative_from(history, mov(IN, "1", 1), UN) is not None, "ainda -3 depois dela"
    assert first_negative_from(history, mov(IN, "4", 1), UN) is None


@pytest.mark.req("RF-007")
def test_new_movement_goes_after_others_at_the_same_instant() -> None:
    """Entrada e saída no mesmo instante: a nova entra depois, como no repositório."""
    history = [mov(IN, "5", 1)]
    assert first_negative_from(history, mov(OUT, "5", 1), UN) is None
    history = [mov(OUT, "5", 1)]
    assert first_negative_from(history, mov(IN, "5", 1), UN) is None, "termina em 0"


@pytest.mark.req("RF-008")
def test_available_at_is_the_balance_when_nothing_happens_later() -> None:
    history = [mov(IN, "10", 0), mov(OUT, "3", 1)]
    assert available_at(history, T0 + timedelta(days=2), UN) == Quantity(Decimal(7), UN)
    assert available_at([], T0, UN) == Quantity.zero(UN)


@pytest.mark.req("RF-008")
def test_available_at_respects_later_outputs() -> None:
    """Dia 0 entra 10; dia 5 sai 8. No dia 2 só dá para tirar 2 sem estourar o dia 5."""
    history = [mov(IN, "10", 0), mov(OUT, "8", 5)]
    assert available_at(history, T0 + timedelta(days=2), UN) == Quantity(Decimal(2), UN)
    assert available_at(history, T0 + timedelta(days=6), UN) == Quantity(Decimal(2), UN)


@pytest.mark.req("RF-008")
def test_available_at_counts_movements_at_the_same_instant_and_never_goes_below_zero() -> None:
    history = [mov(IN, "4", 1), mov(OUT, "6", 3)]
    assert available_at(history, T0 + timedelta(days=1), UN) == Quantity.zero(UN)
    assert available_at([mov(IN, "4", 1)], T0 + timedelta(days=1), UN) == Quantity(Decimal(4), UN)
    assert available_at([mov(IN, "4", 1)], T0, UN) == Quantity.zero(UN), "ainda não tinha chegado"


@pytest.mark.req("RF-008")
def test_available_at_is_the_lowest_point_even_if_stock_comes_back() -> None:
    """Dia 0: +10; dia 5: -8; dia 6: +5. No dia 2, o ponto mais baixo depois dele é 2."""
    history = [mov(IN, "10", 0), mov(OUT, "8", 5), mov(IN, "5", 6)]
    assert available_at(history, T0 + timedelta(days=2), UN) == Quantity(Decimal(2), UN)
