"""Campos personalizados: definição, validação e JSON (M1.11, RF-004, ADR-005; caso TP-M1-07)."""

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st

from core.domain.catalog import ItemKind
from core.domain.custom_fields import (
    CustomFieldDefinition,
    CustomFieldType,
    CustomValue,
    decode_values,
    encode_values,
    validate_custom_fields,
)
from core.domain.errors import ValidationError

pytestmark = pytest.mark.req("RF-004")

ALL = frozenset(ItemKind)
CONSUMABLE = frozenset({ItemKind.CONSUMABLE})
T = CustomFieldType


def define(key: str, field_type: CustomFieldType, **extra: Any) -> CustomFieldDefinition:
    extra.setdefault("kinds", ALL)
    if "label" not in extra:
        extra["label"] = key.replace("_", " ").capitalize()
    return CustomFieldDefinition(key=key, field_type=field_type, **extra)


KITCHEN = [
    define(
        "temperatura",
        T.NUMBER,
        min_value=Decimal(-30),
        max_value=Decimal(10),
        required=True,
        kinds=CONSUMABLE,
        label="Temperatura de armazenamento",
    ),
    define("alergenico", T.BOOLEAN, kinds=CONSUMABLE),
    define("fornecedor_preferido", T.TEXT, max_length=20),
    define("abertura", T.DATE),
    define("embalagem", T.CHOICE, choices=("Caixa", "Saco", "Pote")),
]


def check(
    values: dict[str, object], kind: ItemKind = ItemKind.CONSUMABLE
) -> dict[str, CustomValue]:
    return dict(validate_custom_fields(KITCHEN, kind, values))


# --- definição ---------------------------------------------------------------------------


def test_definition_is_normalized() -> None:
    d = define("cor", T.CHOICE, choices=[" Azul ", "Verde"], kinds=[ItemKind.ASSET], label=" Cor ")
    assert (d.label, d.choices, d.kinds) == ("Cor", ("Azul", "Verde"), frozenset({ItemKind.ASSET}))


@pytest.mark.parametrize("key", ["", "Cor", "1cor", "cor-1", "c" * 41, 7])
def test_invalid_keys_are_refused(key: object) -> None:
    with pytest.raises(ValidationError) as error:
        define(key, T.TEXT, label="Campo")  # type: ignore[arg-type]
    assert error.value.field == "key"


@pytest.mark.parametrize(
    ("field_type", "extra", "field"),
    [
        (T.TEXT, {"kinds": frozenset()}, "kinds"),
        (T.TEXT, {"kinds": "consumable"}, "kinds"),
        (T.TEXT, {"kinds": {"consumable"}}, "kinds"),
        (T.NUMBER, {"max_length": 5}, "max_length"),
        (T.TEXT, {"max_length": 0}, "max_length"),
        (T.TEXT, {"max_length": True}, "max_length"),
        (T.TEXT, {"min_value": Decimal(1)}, "min_value"),
        (T.NUMBER, {"max_value": 1.5}, "max_value"),
        (T.NUMBER, {"min_value": Decimal(5), "max_value": Decimal(1)}, "min_value"),
        (T.CHOICE, {"choices": ()}, "choices"),
        (T.CHOICE, {"choices": ("A", " A ")}, "choices"),
        (T.TEXT, {"choices": ("A",)}, "choices"),
        (T.TEXT, {"required": "sim"}, "required"),
        ("texto", {}, "field_type"),
        (T.TEXT, {"label": " "}, "label"),
        (T.TEXT, {"id": "x"}, "id"),
    ],
)
def test_invalid_definitions_are_refused(
    field_type: CustomFieldType, extra: dict[str, Any], field: str
) -> None:
    with pytest.raises(ValidationError) as error:
        define("campo", field_type, **extra)
    assert error.value.field == field


# --- validação (TP-M1-07) ----------------------------------------------------------------


def test_missing_required_field_names_the_field() -> None:
    with pytest.raises(
        ValidationError, match="Temperatura de armazenamento: campo obrigatório"
    ) as e:
        check({"alergenico": True})
    assert e.value.field == "custom_fields.temperatura"


@pytest.mark.parametrize(
    ("key", "value", "message"),
    [
        ("temperatura", "frio", "precisa ser número"),
        ("temperatura", 4.5, "precisa ser número"),
        ("temperatura", True, "precisa ser número"),
        ("temperatura", Decimal("0.0000001"), "mais de 6 casas"),
        ("temperatura", Decimal("NaN"), "inválido"),
        ("temperatura", Decimal(11), "maior que o máximo"),
        ("temperatura", Decimal(-31), "menor que o mínimo"),
        ("alergenico", "sim", "sim ou não"),
        ("fornecedor_preferido", 123, "precisa ser texto"),
        ("fornecedor_preferido", "x" * 21, "passa de 20"),
        ("abertura", "2026-10-01", "precisa ser uma data"),
        ("abertura", datetime(2026, 10, 1, tzinfo=UTC), "precisa ser uma data"),
        ("embalagem", "Lata", "não é uma das opções"),
    ],
)
def test_wrong_values_name_the_field(key: str, value: object, message: str) -> None:
    with pytest.raises(ValidationError, match=message) as error:
        check({"temperatura": Decimal(4)} | {key: value})
    assert error.value.field == f"custom_fields.{key}"


def test_valid_values_are_cleaned() -> None:
    values = check(
        {
            "temperatura": 4,
            "alergenico": False,
            "fornecedor_preferido": "  Laticínios Sul ",
            "abertura": date(2026, 10, 1),
            "embalagem": " Pote ",
        }
    )
    assert values == {
        "temperatura": Decimal(4),
        "alergenico": False,
        "fornecedor_preferido": "Laticínios Sul",
        "abertura": date(2026, 10, 1),
        "embalagem": "Pote",
    }
    assert isinstance(values["temperatura"], Decimal)


def test_blank_values_count_as_missing() -> None:
    assert check({"temperatura": Decimal(2), "fornecedor_preferido": "  ", "abertura": None}) == {
        "temperatura": Decimal(2)
    }
    with pytest.raises(ValidationError, match="obrigatório"):
        check({"temperatura": None})


def test_unknown_field_is_refused() -> None:
    with pytest.raises(ValidationError, match="não existe") as error:
        check({"temperatura": Decimal(1), "cor": "azul"})
    assert error.value.field == "custom_fields.cor"


def test_field_of_another_item_kind_is_refused_and_not_required() -> None:
    with pytest.raises(ValidationError, match="não se aplica") as error:
        check({"temperatura": Decimal(1)}, kind=ItemKind.ASSET)
    assert error.value.field == "custom_fields.temperatura"
    assert check({}, kind=ItemKind.ASSET) == {}, "obrigatório só para consumível"


# --- JSON (ADR-005) ----------------------------------------------------------------------


def test_numbers_and_dates_become_text_in_json() -> None:
    values = check({"temperatura": Decimal("-2.50"), "abertura": date(2026, 1, 5)})
    assert encode_values(values) == {"temperatura": "-2.50", "abertura": "2026-01-05"}


@given(
    st.fixed_dictionaries(
        {"temperatura": st.decimals(min_value=-30, max_value=10, places=6)},
        optional={
            "alergenico": st.booleans(),
            "fornecedor_preferido": st.text(min_size=1, max_size=20)
            .filter(str.strip)
            .map(str.strip),
            "abertura": st.dates(),
            "embalagem": st.sampled_from(["Caixa", "Saco", "Pote"]),
        },
    )
)
def test_json_round_trip_keeps_every_value(values: dict[str, object]) -> None:
    clean = validate_custom_fields(KITCHEN, ItemKind.CONSUMABLE, values)
    encoded = encode_values(clean)
    assert all(isinstance(v, str | bool) for v in encoded.values())
    assert decode_values(KITCHEN, encoded) == dict(clean)


@pytest.mark.parametrize(
    ("raw", "message"),
    [
        ({"cor": "azul"}, "não existe"),
        ({"temperatura": 4}, "tipo errado"),
        ({"temperatura": "quatro"}, "ilegível"),
        ({"abertura": "01/10/2026"}, "ilegível"),
        ({"alergenico": "true"}, "tipo errado"),
    ],
)
def test_decoding_refuses_bad_stored_values(raw: dict[str, Any], message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        decode_values(KITCHEN, raw)
