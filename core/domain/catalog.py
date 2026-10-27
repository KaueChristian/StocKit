"""Catálogo: itens e categorias (RF-001)."""

import re
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from datetime import date
from decimal import Decimal
from enum import StrEnum
from types import MappingProxyType
from typing import Self
from uuid import UUID

from core.domain.entity import Entity, clean_text, require_type, set_field
from core.domain.errors import ValidationError
from core.domain.ids import CategoryId, ItemId, new_category_id, new_item_id
from core.domain.quantity import Dimension, UnitOfMeasure

SKU_MAX_LENGTH = 64
_SKU_PATTERN = re.compile(r"[A-Z0-9][A-Z0-9._/-]*")
_CUSTOM_KEY = re.compile(r"[a-z][a-z0-9_]{0,39}")


class ItemKind(StrEnum):
    """Tipo de item. O rótulo exibido vem do perfil; o valor é o que se grava."""

    RESALE = "resale"
    CONSUMABLE = "consumable"
    ASSET = "asset"
    SERIALIZED = "serialized"


@dataclass(frozen=True, slots=True, kw_only=True, eq=False)
class Category(Entity):
    """Agrupamento de itens (lista simples, sem hierarquia)."""

    name: str
    id: CategoryId = field(default_factory=new_category_id)

    def __post_init__(self) -> None:
        set_field(self, "name", clean_text(self.name, "name", "nome da categoria", max_length=80))
        require_type(self.id, UUID, "id", "identificador da categoria")


def normalize_sku(value: object) -> str:
    """SKU sem espaços nas pontas, em maiúsculas; só letras, dígitos e ``. _ / -``."""
    if not isinstance(value, str):
        raise ValidationError("sku", "SKU precisa ser texto")
    sku = value.strip().upper()
    if not sku:
        raise ValidationError("sku", "SKU não pode ficar vazio")
    if len(sku) > SKU_MAX_LENGTH:
        raise ValidationError("sku", f"SKU passa de {SKU_MAX_LENGTH} caracteres")
    if not _SKU_PATTERN.fullmatch(sku):
        raise ValidationError(
            "sku", f"SKU {sku!r} só pode ter letras, dígitos e . _ / - (sem espaços)"
        )
    return sku


@dataclass(frozen=True, slots=True, kw_only=True, eq=False)
class Item(Entity):
    """Qualquer coisa controlada em estoque. Saldo não fica aqui: vem do livro de movimentações."""

    sku: str
    name: str
    kind: ItemKind
    base_unit: UnitOfMeasure
    category_id: CategoryId | None = None
    tracks_lots: bool = False
    tracks_expiry: bool = False
    active: bool = True
    custom_fields: Mapping[str, object] = field(default_factory=lambda: MappingProxyType({}))
    id: ItemId = field(default_factory=new_item_id)

    def __post_init__(self) -> None:
        set_field(self, "sku", normalize_sku(self.sku))
        set_field(self, "custom_fields", _freeze_custom_fields(self.custom_fields))
        set_field(self, "name", clean_text(self.name, "name", "nome do item", max_length=200))
        require_type(self.kind, ItemKind, "kind", "tipo de item")
        require_type(self.base_unit, UnitOfMeasure, "base_unit", "unidade base")
        require_type(self.id, UUID, "id", "identificador do item")
        if self.category_id is not None:
            require_type(self.category_id, UUID, "category_id", "categoria")
        for flag in ("tracks_lots", "tracks_expiry", "active"):
            require_type(getattr(self, flag), bool, flag, flag)

        if self.tracks_expiry and not self.tracks_lots:
            raise ValidationError(
                "tracks_expiry",
                f"o item {self.sku} controla validade, então precisa controlar lote "
                "(a validade fica no lote)",
            )
        if self.kind is ItemKind.SERIALIZED and not _is_single_count_unit(self.base_unit):
            raise ValidationError(
                "base_unit",
                f"item serializado ({self.sku}) precisa de unidade de contagem com fator 1, "
                f"não {self.base_unit}",
            )
        if self.kind is ItemKind.SERIALIZED and self.tracks_lots:
            raise ValidationError(
                "tracks_lots",
                f"item serializado ({self.sku}) é controlado por número de série, não por lote",
            )

    def deactivated(self) -> Self:
        """Inativa o item (RF-001). O histórico continua; nada é apagado."""
        return replace(self, active=False)

    def activated(self) -> Self:
        return replace(self, active=True)


def _freeze_custom_fields(values: object) -> Mapping[str, object]:
    """Só a forma: mapa de chave válida para texto, número, data ou sim/não. Conferir contra as
    definições (tipo certo, obrigatórios, regras) é do serviço, que conhece as definições."""
    if not isinstance(values, Mapping):
        raise ValidationError("custom_fields", "campos personalizados precisam ser um mapa")
    frozen: dict[str, object] = {}
    for key, value in values.items():
        if not isinstance(key, str) or not _CUSTOM_KEY.fullmatch(key):
            raise ValidationError("custom_fields", f"chave de campo inválida: {key!r}")
        if isinstance(value, float) or not isinstance(value, str | int | Decimal | date):
            raise ValidationError(f"custom_fields.{key}", f"valor de tipo não aceito: {value!r}")
        frozen[key] = value
    return MappingProxyType(frozen)


def _is_single_count_unit(unit: UnitOfMeasure) -> bool:
    return unit.dimension is Dimension.COUNT and unit.factor == 1
