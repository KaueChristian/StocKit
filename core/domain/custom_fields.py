"""Campos personalizados (M1.11, RF-004, ADR-005).

Uma **definição** diz que itens de certos tipos têm um campo extra (chave, rótulo, tipo, se é
obrigatório e regras). Os **valores** ficam no próprio item, num mapa ``{chave: valor}``. A
validação dos valores contra as definições é feita aqui, no núcleo, igual nas duas plataformas;
todo erro cita o campo como ``custom_fields.<chave>`` (TP-M1-07).

Tipos de valor no domínio: texto (``str``), número (``Decimal``), data (``date``), sim/não
(``bool``) e opção (``str`` de uma lista). No JSON gravado, número vira texto decimal e data vira
AAAA-MM-DD (``encode_values`` / ``decode_values``).
"""

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from fractions import Fraction
from types import MappingProxyType
from uuid import UUID

from core.domain.catalog import ItemKind
from core.domain.entity import Entity, clean_text, require_type, set_field
from core.domain.errors import ValidationError
from core.domain.ids import CustomFieldId, new_custom_field_id

type CustomValue = str | Decimal | date | bool
type JsonValue = str | bool

KEY_PATTERN = re.compile(r"[a-z][a-z0-9_]{0,39}")
TEXT_DEFAULT_MAX_LENGTH = 200


class CustomFieldType(StrEnum):
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    BOOLEAN = "boolean"
    CHOICE = "choice"


def check_key(key: object, field_name: str = "key") -> str:
    """Chave de campo: minúsculas, dígitos e ``_``, começando por letra, até 40 caracteres."""
    if not isinstance(key, str) or not KEY_PATTERN.fullmatch(key):
        raise ValidationError(
            field_name,
            f"chave de campo inválida: {key!r} (minúsculas, dígitos e _, começando por letra)",
        )
    return key


@dataclass(frozen=True, slots=True, kw_only=True, eq=False)
class CustomFieldDefinition(Entity):
    """Definição de um campo personalizado. ``kinds``: tipos de item que têm o campo."""

    key: str
    label: str
    field_type: CustomFieldType
    kinds: frozenset[ItemKind]
    required: bool = False
    max_length: int | None = None
    min_value: Decimal | None = None
    max_value: Decimal | None = None
    choices: tuple[str, ...] = ()
    id: CustomFieldId = field(default_factory=new_custom_field_id)

    def __post_init__(self) -> None:
        check_key(self.key)
        set_field(self, "label", clean_text(self.label, "label", "rótulo do campo", max_length=80))
        require_type(self.field_type, CustomFieldType, "field_type", "tipo do campo")
        require_type(self.required, bool, "required", "obrigatório")
        require_type(self.id, UUID, "id", "identificador do campo")
        set_field(self, "kinds", _clean_kinds(self.kinds, self.key))
        self._check_rules()

    def _check_rules(self) -> None:
        kind = self.field_type
        if self.max_length is not None and (
            kind is not CustomFieldType.TEXT
            or isinstance(self.max_length, bool)
            or not isinstance(self.max_length, int)
            or self.max_length < 1
        ):
            raise ValidationError("max_length", "tamanho máximo só vale para texto, maior que 0")
        for name in ("min_value", "max_value"):
            value = getattr(self, name)
            if value is not None and (
                kind is not CustomFieldType.NUMBER
                or not isinstance(value, Decimal)
                or not value.is_finite()
            ):
                raise ValidationError(name, "mínimo e máximo só valem para número (Decimal)")
        if (
            self.min_value is not None
            and self.max_value is not None
            and self.min_value > self.max_value
        ):
            raise ValidationError("min_value", f"mínimo maior que o máximo no campo {self.key}")
        choices = tuple(self.choices)
        if kind is CustomFieldType.CHOICE:
            cleaned = tuple(clean_text(c, "choices", "opção", max_length=80) for c in choices)
            if not cleaned or len(set(cleaned)) != len(cleaned):
                raise ValidationError(
                    "choices", f"o campo {self.key} precisa de opções sem repetir"
                )
            set_field(self, "choices", cleaned)
        elif choices:
            raise ValidationError("choices", "opções só valem para campo de lista")


def _clean_kinds(value: object, key: str) -> frozenset[ItemKind]:
    kinds = frozenset(value) if isinstance(value, Iterable) and not isinstance(value, str) else None
    if not kinds or not all(isinstance(k, ItemKind) for k in kinds):
        raise ValidationError("kinds", f"o campo {key} precisa de tipos de item válidos")
    return kinds


def _error(key: str, message: str) -> ValidationError:
    return ValidationError(f"custom_fields.{key}", message)


def _check_value(definition: CustomFieldDefinition, value: object) -> CustomValue:
    key, label, kind = definition.key, definition.label, definition.field_type
    if kind is CustomFieldType.TEXT:
        if not isinstance(value, str):
            raise _error(key, f"{label}: precisa ser texto")
        limit = definition.max_length or TEXT_DEFAULT_MAX_LENGTH
        if len(value) > limit:
            raise _error(key, f"{label}: passa de {limit} caracteres")
        return value
    if kind is CustomFieldType.NUMBER:
        if isinstance(value, bool) or not isinstance(value, int | Decimal):
            raise _error(key, f"{label}: precisa ser número (Decimal), não {value!r}")
        number = Decimal(value)
        if not number.is_finite() or (Fraction(number) * 10**6).denominator != 1:
            raise _error(key, f"{label}: número inválido ou com mais de 6 casas: {value}")
        if definition.min_value is not None and number < definition.min_value:
            raise _error(key, f"{label}: menor que o mínimo {definition.min_value}")
        if definition.max_value is not None and number > definition.max_value:
            raise _error(key, f"{label}: maior que o máximo {definition.max_value}")
        return number
    if kind is CustomFieldType.DATE:
        if not isinstance(value, date) or isinstance(value, datetime):
            raise _error(key, f"{label}: precisa ser uma data (dia), não {value!r}")
        return value
    if kind is CustomFieldType.BOOLEAN:
        if not isinstance(value, bool):
            raise _error(key, f"{label}: precisa ser sim ou não, não {value!r}")
        return value
    if not isinstance(value, str) or value not in definition.choices:
        options = ", ".join(definition.choices)
        raise _error(key, f"{label}: {value!r} não é uma das opções ({options})")
    return value


def _is_blank(value: object) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def validate_custom_fields(
    definitions: Iterable[CustomFieldDefinition],
    kind: ItemKind,
    values: Mapping[str, object],
) -> Mapping[str, CustomValue]:
    """Confere os valores de um item do tipo ``kind`` contra as definições e devolve o mapa limpo.

    Recusa: campo sem definição, campo que não é deste tipo de item, obrigatório ausente e valor
    do tipo errado ou fora das regras. Texto vazio conta como ausente e não é guardado.
    """
    by_key = {d.key: d for d in definitions}
    cleaned: dict[str, CustomValue] = {}
    for key, value in values.items():
        definition = by_key.get(key)
        if definition is None:
            raise _error(key, f"campo personalizado {key!r} não existe")
        if kind not in definition.kinds:
            raise _error(key, f"{definition.label}: não se aplica a itens do tipo {kind.value}")
        if _is_blank(value):
            continue
        if isinstance(value, str) and definition.field_type in (
            CustomFieldType.TEXT,
            CustomFieldType.CHOICE,
        ):
            value = value.strip()
        cleaned[key] = _check_value(definition, value)
    for definition in by_key.values():
        if definition.required and kind in definition.kinds and definition.key not in cleaned:
            raise _error(definition.key, f"{definition.label}: campo obrigatório")
    return MappingProxyType(cleaned)


def encode_values(values: Mapping[str, CustomValue]) -> dict[str, JsonValue]:
    """Valores para JSON: número como texto decimal, data como AAAA-MM-DD (ADR-005)."""
    encoded: dict[str, JsonValue] = {}
    for key, value in values.items():
        if isinstance(value, bool | str):
            encoded[key] = value
        elif isinstance(value, Decimal):
            encoded[key] = str(value)
        else:
            encoded[key] = value.isoformat()
    return encoded


def decode_values(
    definitions: Iterable[CustomFieldDefinition], raw: Mapping[str, JsonValue]
) -> dict[str, CustomValue]:
    """Volta do JSON para os tipos do domínio, usando as definições para saber o tipo."""
    by_key = {d.key: d for d in definitions}
    decoded: dict[str, CustomValue] = {}
    for key, value in raw.items():
        definition = by_key.get(key)
        if definition is None:
            raise _error(key, f"campo personalizado {key!r} não existe")
        kind = definition.field_type
        try:
            if kind is CustomFieldType.NUMBER and isinstance(value, str):
                decoded[key] = Decimal(value)
            elif kind is CustomFieldType.DATE and isinstance(value, str):
                decoded[key] = date.fromisoformat(value)
            elif (kind is CustomFieldType.BOOLEAN and isinstance(value, bool)) or (
                kind in (CustomFieldType.TEXT, CustomFieldType.CHOICE) and isinstance(value, str)
            ):
                decoded[key] = value
            else:
                raise _error(key, f"{definition.label}: valor gravado com tipo errado: {value!r}")
        except InvalidOperation, ValueError:
            raise _error(key, f"{definition.label}: valor gravado ilegível: {value!r}") from None
    return decoded
