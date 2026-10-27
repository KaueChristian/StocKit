"""Quantidades e unidades de medida (M1.1, RF-010, INV-04, ADR-006)."""

from collections.abc import Callable
from decimal import Decimal
from fractions import Fraction

import pytest
from hypothesis import assume, given
from hypothesis import strategies as st

from core.domain.errors import (
    DomainError,
    IncompatibleUnitsError,
    InvalidQuantityError,
    InvalidUnitError,
)
from core.domain.quantity import (
    MAX_INTEGER_DIGITS,
    SCALE,
    STANDARD_UNITS,
    Dimension,
    Quantity,
    UnitOfMeasure,
)

UN = STANDARD_UNITS["un"]
DZ = STANDARD_UNITS["dz"]
KG = STANDARD_UNITS["kg"]
G = STANDARD_UNITS["g"]
L = STANDARD_UNITS["L"]
ML = STANDARD_UNITS["mL"]
CX12 = UnitOfMeasure("cx12", "caixa com 12", Dimension.COUNT, Decimal(12))

LIMIT = Decimal(10) ** MAX_INTEGER_DIGITS
ULP = Decimal(1).scaleb(-SCALE)


def q(value: str, unit: UnitOfMeasure) -> Quantity:
    return Quantity(Decimal(value), unit)


# --- estratégias -------------------------------------------------------------------------

values = st.decimals(
    min_value=-LIMIT + ULP,
    max_value=LIMIT - ULP,
    places=SCALE,
    allow_nan=False,
    allow_infinity=False,
)
factors = st.decimals(
    min_value=Decimal("0.000001"), max_value=Decimal(1_000_000), places=6, allow_nan=False
).filter(lambda f: f > 0)


@st.composite
def unit_pairs(draw: st.DrawFn) -> tuple[UnitOfMeasure, UnitOfMeasure]:
    """Duas unidades da mesma grandeza: do catálogo padrão ou com fatores aleatórios."""
    if draw(st.booleans()):
        dimension = draw(st.sampled_from(list(Dimension)))
        same = [u for u in STANDARD_UNITS.values() if u.dimension is dimension]
        return draw(st.sampled_from(same)), draw(st.sampled_from(same))
    dimension = draw(st.sampled_from(list(Dimension)))
    return (
        UnitOfMeasure("a", "unidade A", dimension, draw(factors)),
        UnitOfMeasure("b", "unidade B", dimension, draw(factors)),
    )


def convert_or_skip(quantity: Quantity, unit: UnitOfMeasure) -> Quantity:
    """Converte; descarta o exemplo se o resultado sair da faixa (caso testado à parte)."""
    try:
        return quantity.to(unit)
    except InvalidQuantityError:
        assume(False)
        raise  # pragma: no cover - assume(False) já interrompe o exemplo


# --- conversão (INV-04) ------------------------------------------------------------------


@pytest.mark.req("RF-010")
@pytest.mark.parametrize(
    ("source", "target", "expected"),
    [
        (q("2.5", KG), G, q("2500", G)),
        (q("750", ML), L, q("0.75", L)),
        (q("3", DZ), UN, q("36", UN)),
        (q("30", UN), DZ, q("2.5", DZ)),
        (q("1", UN), CX12, q("0.083333", CX12)),
        (q("2", UN), CX12, q("0.166667", CX12)),
        (q("1.5", L), L, q("1.5", L)),
    ],
)
def test_conversion_examples(source: Quantity, target: UnitOfMeasure, expected: Quantity) -> None:
    assert source.to(target) == expected


@pytest.mark.req("RF-010")
def test_conversion_rounds_half_even_at_the_sixth_place() -> None:
    half_up = UnitOfMeasure("x", "x", Dimension.COUNT, Decimal("0.0000005"))
    # 1 x = 0,0000005 un: exatamente no meio entre 0,000000 e 0,000001 → par (0)
    assert q("1", half_up).to(UN).value == 0
    # 3 x = 0,0000015 un: meio entre 0,000001 e 0,000002 → par (0,000002)
    assert q("3", half_up).to(UN).value == Decimal("0.000002")


@pytest.mark.req("RF-010")
@given(value=values, pair=unit_pairs())
def test_round_trip_stays_within_the_defined_rounding(
    value: Decimal, pair: tuple[UnitOfMeasure, UnitOfMeasure]
) -> None:
    """INV-04: ida e volta erra no máximo ½·10⁻⁶·(1 + fB/fA), na unidade de origem."""
    source, target = pair
    original = Quantity(value, source)
    back = convert_or_skip(convert_or_skip(original, target), source)
    bound = Fraction(1, 2 * 10**SCALE) * (1 + Fraction(target.factor) / Fraction(source.factor))
    assert abs(Fraction(back.value) - Fraction(value)) <= bound


@pytest.mark.req("RF-010")
@given(value=values, pair=unit_pairs())
def test_round_trip_to_a_divisible_finer_unit_is_exact(
    value: Decimal, pair: tuple[UnitOfMeasure, UnitOfMeasure]
) -> None:
    """INV-04: indo para uma unidade em que a de origem cabe um número inteiro de vezes, é exato."""
    source, target = pair
    assume((Fraction(source.factor) / Fraction(target.factor)).denominator == 1)
    original = Quantity(value, source)
    assert convert_or_skip(convert_or_skip(original, target), source) == original


@pytest.mark.req("RF-010")
@given(value=values, pair=unit_pairs())
def test_conversion_result_is_the_exact_value_rounded_once(
    value: Decimal, pair: tuple[UnitOfMeasure, UnitOfMeasure]
) -> None:
    source, target = pair
    converted = convert_or_skip(Quantity(value, source), target)
    exact = Fraction(value) * Fraction(source.factor) / Fraction(target.factor)
    assert abs(Fraction(converted.value) - exact) <= Fraction(1, 2 * 10**SCALE)


@pytest.mark.req("RF-010")
def test_conversion_between_dimensions_is_refused() -> None:
    with pytest.raises(IncompatibleUnitsError, match=r"kg \(massa\) em L \(volume\)"):
        q("1", KG).to(L)


@pytest.mark.req("RF-010")
def test_conversion_out_of_range_is_refused() -> None:
    huge = Quantity(LIMIT - 1, KG)
    with pytest.raises(InvalidQuantityError, match="limite"):
        huge.to(G)


# --- construção --------------------------------------------------------------------------


@pytest.mark.req("RF-010")
@pytest.mark.parametrize(
    "bad",
    [1.5, 2, "3", Decimal("NaN"), Decimal("Infinity"), Decimal("-Infinity"), Decimal("0.0000001")],
    ids=["float", "int", "str", "nan", "inf", "-inf", "7-casas"],
)
def test_quantity_rejects_invalid_values(bad: object) -> None:
    with pytest.raises(InvalidQuantityError):
        Quantity(bad, UN)  # type: ignore[arg-type]


@pytest.mark.req("RF-010")
@pytest.mark.parametrize("value", [LIMIT, -LIMIT, LIMIT * 10])
def test_quantity_rejects_values_beyond_twelve_integer_digits(value: Decimal) -> None:
    with pytest.raises(InvalidQuantityError, match="limite"):
        Quantity(value, UN)


@pytest.mark.req("RF-010")
@pytest.mark.parametrize(
    "value", ["0", "-5", "0.000001", "999999999999.999999", "-999999999999.999999", "1.500000000"]
)
def test_quantity_accepts_values_within_scale_and_range(value: str) -> None:
    assert Quantity(Decimal(value), UN).value == Decimal(value)


def test_quantity_requires_a_unit() -> None:
    with pytest.raises(InvalidQuantityError, match="unidade"):
        Quantity(Decimal(1), "un")  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("symbol", "name", "factor"),
    [
        ("", "vazio", Decimal(1)),
        (" kg", "espaço", Decimal(1)),
        ("kg", " ", Decimal(1)),
        ("kg", "zero", Decimal(0)),
        ("kg", "negativo", Decimal(-1)),
        ("kg", "infinito", Decimal("Infinity")),
        ("kg", "float", 1.0),
    ],
)
def test_unit_rejects_invalid_definitions(symbol: str, name: str, factor: Decimal) -> None:
    with pytest.raises(InvalidUnitError):
        UnitOfMeasure(symbol, name, Dimension.MASS, factor)


def test_unit_rejects_unknown_dimension() -> None:
    with pytest.raises(InvalidUnitError, match="grandeza"):
        UnitOfMeasure("x", "x", "massa", Decimal(1))  # type: ignore[arg-type]


def test_standard_units_are_consistent() -> None:
    assert all(symbol == unit.symbol for symbol, unit in STANDARD_UNITS.items())
    bases = {u.dimension for u in STANDARD_UNITS.values() if u.factor == 1}
    assert bases == set(Dimension), "toda grandeza precisa de uma unidade base no catálogo"
    with pytest.raises(TypeError):
        STANDARD_UNITS["kg"] = KG  # type: ignore[index]


def test_errors_share_the_domain_base() -> None:
    for error in (InvalidQuantityError, InvalidUnitError, IncompatibleUnitsError):
        assert issubclass(error, DomainError)


# --- aritmética e comparação -------------------------------------------------------------


def test_add_and_subtract_in_the_same_unit() -> None:
    assert q("1.25", KG) + q("0.75", KG) == q("2", KG)
    assert q("1", KG) - q("1.5", KG) == q("-0.5", KG)
    assert -q("2", L) == q("-2", L)
    assert Quantity.zero(UN) == q("0", UN)


@pytest.mark.parametrize("operation", ["+", "-", "<", "<=", ">", ">="])
def test_operations_across_different_units_are_refused(operation: str) -> None:
    a, b = q("1", KG), q("1000", G)
    actions: dict[str, Callable[[], object]] = {
        "+": lambda: a + b,
        "-": lambda: a - b,
        "<": lambda: a < b,
        "<=": lambda: a <= b,
        ">": lambda: a > b,
        ">=": lambda: a >= b,
    }
    with pytest.raises(IncompatibleUnitsError, match="converta"):
        actions[operation]()


def test_same_amount_in_different_units_is_not_equal() -> None:
    """Igualdade é de valor e unidade; para comparar grandezas, converta antes."""
    assert q("1", KG) != q("1000", G)
    assert q("1", KG).to(G) == q("1000", G)


def test_equal_quantities_have_equal_hashes() -> None:
    assert hash(q("1.50", KG)) == hash(q("1.5", KG))
    assert len({q("1.50", KG), q("1.5", KG)}) == 1


def test_operations_with_other_types_are_not_supported() -> None:
    with pytest.raises(TypeError):
        _ = q("1", UN) + Decimal(1)
    with pytest.raises(TypeError):
        _ = q("1", UN) - Decimal(1)
    with pytest.raises(TypeError):
        _ = q("1", UN) < 1
    assert q("1", UN) != Decimal(1)


@given(a=values, b=values)
def test_subtraction_undoes_addition(a: Decimal, b: Decimal) -> None:
    assume(abs(a + b) < LIMIT)
    total = Quantity(a, UN) + Quantity(b, UN)
    assert total - Quantity(b, UN) == Quantity(a, UN)


@given(a=values, b=values)
def test_ordering_follows_the_values(a: Decimal, b: Decimal) -> None:
    x, y = Quantity(a, KG), Quantity(b, KG)
    assert (x < y) == (a < b)
    assert (x <= y) == (a <= b)
    assert (x > y) == (a > b)
    assert (x >= y) == (a >= b)


def test_sum_beyond_the_limit_is_refused() -> None:
    almost = Quantity(LIMIT - ULP, UN)
    with pytest.raises(InvalidQuantityError, match="limite"):
        _ = almost + Quantity(ULP, UN)


@pytest.mark.parametrize(
    ("quantity", "text"),
    [
        (q("2.5", KG), "2.5 kg"),
        (q("2.000000", KG), "2 kg"),
        (q("100", G), "100 g"),
        (q("1", KG) - q("3", KG), "-2 kg"),
        (q("0.000001", KG), "0.000001 kg"),
        (q("-0", KG), "-0 kg"),
    ],
)
def test_str_shows_value_without_trailing_zeros(quantity: Quantity, text: str) -> None:
    assert str(quantity) == text
