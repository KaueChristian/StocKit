"""Configuração do sistema (M1.12, RF-007, RF-011).

Uma por instalação (um arquivo .db no desktop, um banco na web). Guarda as políticas e o que veio
do perfil aplicado: vocabulário das telas e unidades extras. Imutável: mudar é gravar outra.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.domain.errors import ValidationError
from core.domain.policy import NegativeStockPolicy
from core.domain.quantity import STANDARD_UNITS, UnitOfMeasure

LABEL_KEYS = frozenset(
    {
        "item",
        "items",
        "location",
        "locations",
        "category",
        "party",
        "lot",
        "serial",
        "kind.resale",
        "kind.consumable",
        "kind.asset",
        "kind.serialized",
        "role.supplier",
        "role.customer",
        "role.department",
    }
)
"""Termos das telas que um perfil pode trocar (ex.: ``item`` → "Ingrediente")."""


@dataclass(frozen=True, slots=True, kw_only=True)
class SystemSettings:
    negative_stock_policy: NegativeStockPolicy = NegativeStockPolicy.FORBID
    profile_key: str | None = None
    labels: Mapping[str, str] = field(default_factory=lambda: MappingProxyType({}))
    units: tuple[UnitOfMeasure, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.negative_stock_policy, NegativeStockPolicy):
            raise ValidationError("negative_stock_policy", "política de saldo negativo inválida")
        unknown = set(self.labels) - LABEL_KEYS
        if unknown:
            raise ValidationError("labels", f"termos desconhecidos: {', '.join(sorted(unknown))}")
        object.__setattr__(self, "labels", MappingProxyType(dict(self.labels)))
        object.__setattr__(self, "units", tuple(self.units))
        check_units(self.units)

    def label(self, key: str, default: str) -> str:
        return self.labels.get(key, default)

    def unit_catalog(self) -> dict[str, UnitOfMeasure]:
        """Unidades padrão + as do perfil, por símbolo."""
        return {**STANDARD_UNITS, **{u.symbol: u for u in self.units}}


def check_units(units: tuple[UnitOfMeasure, ...]) -> None:
    """Unidades extras: símbolos únicos e sem redefinir uma unidade padrão de outro jeito."""
    seen: set[str] = set()
    for unit in units:
        if not isinstance(unit, UnitOfMeasure):
            raise ValidationError("units", f"unidade inválida: {unit!r}")
        if unit.symbol in seen:
            raise ValidationError("units", f"unidade {unit.symbol} repetida")
        standard = STANDARD_UNITS.get(unit.symbol)
        if standard is not None and standard != unit:
            raise ValidationError(
                "units", f"{unit.symbol} já é uma unidade padrão, com outro fator"
            )
        seen.add(unit.symbol)
