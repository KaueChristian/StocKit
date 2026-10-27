"""Configuração do sistema e leitura de perfis no domínio (M1.12, RF-011; caso TP-M1-08)."""

import copy
from decimal import Decimal
from typing import Any

import pytest

from core.domain.catalog import ItemKind
from core.domain.custom_fields import CustomFieldType
from core.domain.errors import ProfileError, ValidationError
from core.domain.policy import NegativeStockPolicy
from core.domain.profile import parse_profile
from core.domain.quantity import STANDARD_UNITS, Dimension, UnitOfMeasure
from core.domain.settings import SystemSettings

pytestmark = pytest.mark.req("RF-011")

CX12 = UnitOfMeasure("cx12", "caixa com 12", Dimension.COUNT, Decimal(12))

VALID: dict[str, Any] = {
    "schema_version": 1,
    "key": "padaria",
    "name": "Padaria",
    "description": "Exemplo de teste",
    "labels": {"item": "Produto", "location": "Vitrine"},
    "units": [{"symbol": "cx12", "name": "caixa com 12", "dimension": "count", "factor": "12"}],
    "categories": ["Pães", "Doces"],
    "custom_fields": [
        {
            "key": "temperatura",
            "label": "Temperatura",
            "type": "number",
            "kinds": ["consumable"],
            "required": True,
            "min": "-5",
            "max": "8",
        },
        {
            "key": "sabor",
            "label": "Sabor",
            "type": "choice",
            "kinds": ["resale"],
            "choices": ["Doce", "Salgado"],
        },
    ],
    "settings": {"negative_stock_policy": "allow"},
}


def variant(path: str, value: object) -> dict[str, Any]:
    """Cópia do perfil válido com ``value`` em ``path`` (``a.b[0].c``); ``...`` remove a chave."""
    data = copy.deepcopy(VALID)
    target: Any = data
    parts = path.replace("]", "").replace("[", ".").split(".")
    for part in parts[:-1]:
        target = target[int(part)] if part.isdigit() else target[part]
    last = parts[-1]
    if value is ...:
        del target[int(last) if last.isdigit() else last]
    elif last.isdigit():
        target[int(last)] = value
    else:
        target[last] = value
    return data


# Perfis inválidos e onde o núcleo tem de apontar o problema. O teste do adaptador usa a mesma
# lista para conferir que o JSON Schema publicado também recusa cada um.
INVALID: list[tuple[str, dict[str, Any] | object, str]] = [
    ("nao-objeto", [], "$"),
    ("versao", variant("schema_version", 2), "schema_version"),
    ("sem-chave", variant("key", ...), "$"),
    ("chave-maiuscula", variant("key", "Padaria"), "key"),
    ("chave-extra", variant("cor", "azul"), "$"),
    ("nome-vazio", variant("name", "  "), "name"),
    ("termo-desconhecido", variant("labels.produto", "X"), "labels"),
    ("termo-vazio", variant("labels.item", ""), "labels.item"),
    ("unidade-sem-fator", variant("units[0].factor", ...), "units[0]"),
    ("fator-numero-json", variant("units[0].factor", 12.5), "units[0].factor"),
    ("fator-zero", variant("units[0].factor", "0"), "units[0]"),
    ("grandeza", variant("units[0].dimension", "peso"), "units[0].dimension"),
    ("unidades-nao-lista", variant("units", {}), "units"),
    ("nome-numero", variant("name", 7), "name"),
    ("nome-longo", variant("name", "x" * 81), "name"),
    ("fator-por-extenso", variant("units[0].factor", "doze"), "units[0].factor"),
    ("fator-infinito", variant("units[0].factor", "Infinity"), "units[0].factor"),
    ("campo-tipo", variant("custom_fields[0].type", "decimal"), "custom_fields[0].type"),
    ("campo-tipo-item", variant("custom_fields[0].kinds[0]", "food"), "custom_fields[0].kinds[0]"),
    ("campo-sem-tipos", variant("custom_fields[0].kinds", []), "custom_fields[0]"),
    ("campo-min-float", variant("custom_fields[0].min", -5.5), "custom_fields[0].min"),
    ("campo-sem-opcoes", variant("custom_fields[1].choices", []), "custom_fields[1]"),
    ("campo-chave", variant("custom_fields[0].key", "Temp"), "custom_fields[0]"),
    (
        "politica",
        variant("settings.negative_stock_policy", "sempre"),
        "settings.negative_stock_policy",
    ),
]

# Regras de significado que um JSON Schema não expressa: só o núcleo recusa (o schema aceita).
SEMANTIC_ONLY: list[tuple[str, dict[str, Any] | object, str]] = [
    ("unidade-padrao-redefinida", variant("units[0].symbol", "kg"), "units"),
    ("categoria-repetida-sem-caixa", variant("categories[1]", "pães"), "categories"),
    ("campo-repetido", variant("custom_fields[1].key", "temperatura"), "custom_fields"),
]


def test_valid_profile_is_parsed() -> None:
    profile = parse_profile(VALID)
    assert (profile.key, profile.name, profile.description) == (
        "padaria",
        "Padaria",
        "Exemplo de teste",
    )
    assert profile.labels == {"item": "Produto", "location": "Vitrine"}
    assert profile.units == (CX12,)
    assert profile.categories == ("Pães", "Doces")
    temperature, flavor = profile.custom_fields
    assert (temperature.key, temperature.field_type, temperature.required) == (
        "temperatura",
        CustomFieldType.NUMBER,
        True,
    )
    assert (temperature.min_value, temperature.max_value) == (Decimal(-5), Decimal(8))
    assert temperature.kinds == frozenset({ItemKind.CONSUMABLE})
    assert flavor.choices == ("Doce", "Salgado")
    assert profile.negative_stock_policy is NegativeStockPolicy.ALLOW


def test_minimal_profile_uses_defaults() -> None:
    profile = parse_profile({"schema_version": 1, "key": "mini", "name": "Mínimo"})
    assert (profile.units, profile.categories, profile.custom_fields) == ((), (), ())
    assert profile.negative_stock_policy is None
    assert profile.description == ""


@pytest.mark.parametrize(
    ("case", "data", "path"),
    INVALID + SEMANTIC_ONLY,
    ids=[c for c, _, _ in INVALID + SEMANTIC_ONLY],
)
def test_invalid_profile_is_refused_with_the_place_of_the_problem(
    case: str, data: object, path: str
) -> None:
    with pytest.raises(ProfileError) as error:
        parse_profile(data)
    assert error.value.path == path
    assert str(error.value).startswith(f"{path}: ")
    assert error.value.reason


# --- configuração ------------------------------------------------------------------------


def test_default_settings_forbid_negative_stock() -> None:
    settings = SystemSettings()
    assert settings.negative_stock_policy is NegativeStockPolicy.FORBID
    assert settings.profile_key is None
    assert settings.label("item", "Item") == "Item"
    assert settings.unit_catalog() == dict(STANDARD_UNITS)


def test_settings_labels_and_units() -> None:
    source = {"item": "Insumo"}
    settings = SystemSettings(labels=source, units=[CX12])  # type: ignore[arg-type]
    source["item"] = "Outro"
    assert settings.label("item", "Item") == "Insumo"
    assert settings.units == (CX12,)
    assert settings.unit_catalog()["cx12"] == CX12
    assert settings.unit_catalog()["kg"] == STANDARD_UNITS["kg"]
    with pytest.raises(TypeError):
        settings.labels["item"] = "x"  # type: ignore[index]


@pytest.mark.parametrize(
    ("changes", "field"),
    [
        ({"negative_stock_policy": "forbid"}, "negative_stock_policy"),
        ({"labels": {"produto": "X"}}, "labels"),
        ({"units": (CX12, CX12)}, "units"),
        ({"units": (UnitOfMeasure("kg", "quilo", Dimension.MASS, Decimal(2)),)}, "units"),
        ({"units": ("cx12",)}, "units"),
    ],
)
def test_invalid_settings_are_refused(changes: dict[str, Any], field: str) -> None:
    with pytest.raises(ValidationError) as error:
        SystemSettings(**changes)
    assert error.value.field == field


def test_standard_unit_repeated_as_is_is_accepted() -> None:
    assert SystemSettings(units=(STANDARD_UNITS["kg"],)).units == (STANDARD_UNITS["kg"],)
