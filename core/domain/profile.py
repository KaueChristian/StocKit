"""Perfis de negócio (M1.12, RF-011).

Um perfil pré-configura o StocKit para um tipo de negócio (varejo, cozinha, oficina, TI) sem mexer
em código: vocabulário das telas, unidades extras, categorias iniciais, campos personalizados e
políticas. O formato é JSON, descrito pelo JSON Schema publicado em
``adapters/profiles/profile.schema.json``; aqui está a validação que vale (o núcleo não depende de
biblioteca de schema), e um teste garante que as duas concordam.

``parse_profile`` recebe o JSON **já lido** (ler arquivo é do adaptador) e devolve um ``Profile``
ou levanta ``ProfileError`` dizendo onde está o problema (``custom_fields[1].type``).
"""

import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from types import MappingProxyType
from typing import Any

from core.domain.catalog import ItemKind
from core.domain.custom_fields import CustomFieldDefinition, CustomFieldType
from core.domain.errors import DomainError, ProfileError
from core.domain.policy import NegativeStockPolicy
from core.domain.quantity import Dimension, UnitOfMeasure
from core.domain.settings import LABEL_KEYS, check_units

SCHEMA_VERSION = 1
PROFILE_KEY = re.compile(r"[a-z][a-z0-9-]{1,39}")
_TOP_KEYS = {
    "schema_version",
    "key",
    "name",
    "description",
    "labels",
    "units",
    "categories",
    "custom_fields",
    "settings",
}
_UNIT_KEYS = {"symbol", "name", "dimension", "factor"}
_FIELD_KEYS = {"key", "label", "type", "kinds", "required", "max_length", "min", "max", "choices"}
_SETTINGS_KEYS = {"negative_stock_policy"}


@dataclass(frozen=True, slots=True)
class Profile:
    key: str
    name: str
    description: str
    labels: Mapping[str, str]
    units: tuple[UnitOfMeasure, ...]
    categories: tuple[str, ...]
    custom_fields: tuple[CustomFieldDefinition, ...]
    negative_stock_policy: NegativeStockPolicy | None


def parse_profile(data: object) -> Profile:
    root = _object(data, "$", required={"schema_version", "key", "name"}, allowed=_TOP_KEYS)
    if root["schema_version"] != SCHEMA_VERSION or isinstance(root["schema_version"], bool):
        raise ProfileError(
            "schema_version", f"versão de perfil não suportada (use {SCHEMA_VERSION})"
        )
    key = root["key"]
    if not isinstance(key, str) or not PROFILE_KEY.fullmatch(key):
        raise ProfileError("key", "chave do perfil: minúsculas, dígitos e -, de 2 a 40 caracteres")
    name = _text(root["name"], "name", 80)
    description = _text(root.get("description", ""), "description", 500, allow_empty=True)
    labels = _labels(root.get("labels", {}))
    units = tuple(
        _unit(u, f"units[{i}]") for i, u in enumerate(_array(root.get("units", []), "units"))
    )
    _domain("units", lambda: check_units(units))
    categories = tuple(
        _text(c, f"categories[{i}]", 80)
        for i, c in enumerate(_array(root.get("categories", []), "categories"))
    )
    if len({c.casefold() for c in categories}) != len(categories):
        raise ProfileError("categories", "categoria repetida")
    fields = tuple(
        _field(f, f"custom_fields[{i}]")
        for i, f in enumerate(_array(root.get("custom_fields", []), "custom_fields"))
    )
    if len({f.key for f in fields}) != len(fields):
        raise ProfileError("custom_fields", "chave de campo repetida")
    settings = _object(root.get("settings", {}), "settings", required=set(), allowed=_SETTINGS_KEYS)
    policy = None
    if "negative_stock_policy" in settings:
        policy = _enum(
            NegativeStockPolicy, settings["negative_stock_policy"], "settings.negative_stock_policy"
        )
    return Profile(
        key=key,
        name=name,
        description=description,
        labels=labels,
        units=units,
        categories=categories,
        custom_fields=fields,
        negative_stock_policy=policy,
    )


# --- partes ------------------------------------------------------------------------------


def _object(value: object, path: str, *, required: set[str], allowed: set[str]) -> dict[str, Any]:
    if not isinstance(value, Mapping) or not all(isinstance(k, str) for k in value):
        raise ProfileError(path, "precisa ser um objeto")
    missing = sorted(required - set(value))
    if missing:
        raise ProfileError(path, f"falta {', '.join(missing)}")
    extra = sorted(set(value) - allowed)
    if extra:
        raise ProfileError(path, f"chave desconhecida: {', '.join(extra)}")
    return dict(value)


def _array(value: object, path: str) -> Sequence[object]:
    if not isinstance(value, list):
        raise ProfileError(path, "precisa ser uma lista")
    return value


def _text(value: object, path: str, limit: int, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise ProfileError(path, "precisa ser texto")
    text = " ".join(value.split())
    if not text and not allow_empty:
        raise ProfileError(path, "não pode ficar vazio")
    if len(text) > limit:
        raise ProfileError(path, f"passa de {limit} caracteres")
    return text


def _decimal(value: object, path: str) -> Decimal:
    """Números do perfil vêm como texto decimal (ADR-005), nunca como número JSON (float)."""
    if not isinstance(value, str):
        raise ProfileError(path, 'número precisa vir como texto decimal (ex.: "12")')
    try:
        number = Decimal(value)
    except InvalidOperation:
        raise ProfileError(path, f"número inválido: {value!r}") from None
    if not number.is_finite():
        raise ProfileError(path, f"número inválido: {value!r}")
    return number


def _enum[E](kind: type[E], value: object, path: str) -> E:
    try:
        return kind(value)  # type: ignore[call-arg]
    except ValueError:
        options = ", ".join(str(getattr(e, "value", e)) for e in kind)  # type: ignore[attr-defined]
        raise ProfileError(path, f"valor inválido {value!r} (use: {options})") from None


def _domain[T](path: str, build: Callable[[], T]) -> T:
    """Roda uma validação do domínio e devolve o erro dela com o caminho do perfil."""
    try:
        result: T = build()
    except ProfileError:
        raise  # já traz o caminho exato
    except DomainError as error:
        raise ProfileError(path, str(error)) from None
    return result


def _labels(value: object) -> Mapping[str, str]:
    labels = _object(value, "labels", required=set(), allowed=set(LABEL_KEYS))
    return MappingProxyType({k: _text(v, f"labels.{k}", 40) for k, v in labels.items()})


def _unit(value: object, path: str) -> UnitOfMeasure:
    unit = _object(value, path, required=_UNIT_KEYS, allowed=_UNIT_KEYS)
    dimension = _enum(Dimension, unit["dimension"], f"{path}.dimension")
    factor = _decimal(unit["factor"], f"{path}.factor")
    return _domain(path, lambda: UnitOfMeasure(unit["symbol"], unit["name"], dimension, factor))


def _field(value: object, path: str) -> CustomFieldDefinition:
    spec = _object(value, path, required={"key", "label", "type", "kinds"}, allowed=_FIELD_KEYS)
    field_type = _enum(CustomFieldType, spec["type"], f"{path}.type")
    kinds = frozenset(
        _enum(ItemKind, k, f"{path}.kinds[{i}]")
        for i, k in enumerate(_array(spec["kinds"], f"{path}.kinds"))
    )
    choices = tuple(_array(spec.get("choices", []), f"{path}.choices"))
    return _domain(
        path,
        lambda: CustomFieldDefinition(
            key=spec["key"],
            label=spec["label"],
            field_type=field_type,
            kinds=kinds,
            required=spec.get("required", False),
            max_length=spec.get("max_length"),
            min_value=_decimal(spec["min"], f"{path}.min") if "min" in spec else None,
            max_value=_decimal(spec["max"], f"{path}.max") if "max" in spec else None,
            choices=choices,  # type: ignore[arg-type]
        ),
    )
