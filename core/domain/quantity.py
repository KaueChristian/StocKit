"""Quantidades e unidades de medida (value objects imutáveis).

Regras (ADR-006):

- o valor é sempre ``Decimal`` (nunca ``float``), com no máximo ``SCALE`` (6) casas decimais e
  ``MAX_INTEGER_DIGITS`` (12) dígitos inteiros;
- cada unidade pertence a uma grandeza (``Dimension``) e tem um fator: quantas unidades base da
  grandeza cabem em uma dela (1 kg = 1; 1 g = 0,001);
- converter entre unidades da mesma grandeza calcula o valor exato e arredonda **uma vez** para 6
  casas, com ROUND_HALF_EVEN. Ida e volta erra no máximo ½·10⁻⁶·(1 + fB/fA) na unidade de origem, e
  zero quando a unidade de origem cabe um número inteiro de vezes na de destino (INV-04);
- soma, subtração e comparação só entre quantidades da mesma unidade: converter é sempre explícito.

As contas usam ``Fraction`` (exata) e não dependem do contexto global do ``decimal``.
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from fractions import Fraction
from functools import total_ordering
from types import MappingProxyType
from typing import Self

from core.domain.errors import IncompatibleUnitsError, InvalidQuantityError, InvalidUnitError

SCALE = 6
MAX_INTEGER_DIGITS = 12
_STEPS_PER_UNIT = 10**SCALE
_MAX_STEPS = 10 ** (MAX_INTEGER_DIGITS + SCALE)  # |valor| · 10⁶ precisa ficar abaixo disto


class Dimension(StrEnum):
    """Grandeza física de uma unidade. Só unidades da mesma grandeza se convertem."""

    COUNT = "count"
    MASS = "mass"
    VOLUME = "volume"
    LENGTH = "length"

    @property
    def label(self) -> str:
        return _DIMENSION_LABELS[self]


_DIMENSION_LABELS = {
    Dimension.COUNT: "contagem",
    Dimension.MASS: "massa",
    Dimension.VOLUME: "volume",
    Dimension.LENGTH: "comprimento",
}


@dataclass(frozen=True, slots=True)
class UnitOfMeasure:
    """Unidade de medida: símbolo, nome, grandeza e fator para a unidade base da grandeza."""

    symbol: str
    name: str
    dimension: Dimension
    factor: Decimal

    def __post_init__(self) -> None:
        if not self.symbol or self.symbol != self.symbol.strip():
            raise InvalidUnitError(f"símbolo de unidade inválido: {self.symbol!r}")
        if not self.name.strip():
            raise InvalidUnitError(f"a unidade {self.symbol} precisa de um nome")
        if not isinstance(self.dimension, Dimension):
            raise InvalidUnitError(
                f"grandeza desconhecida para a unidade {self.symbol}: {self.dimension!r}"
            )
        if not isinstance(self.factor, Decimal) or not self.factor.is_finite() or self.factor <= 0:
            raise InvalidUnitError(
                f"o fator da unidade {self.symbol} precisa ser um Decimal positivo: {self.factor!r}"
            )

    def __str__(self) -> str:
        return self.symbol


def _to_steps(value: Decimal) -> int:
    """Valor em passos de 10⁻⁶ (inteiro). Rejeita o que não cabe na escala ou no limite."""
    scaled = Fraction(value) * _STEPS_PER_UNIT
    if scaled.denominator != 1:
        raise InvalidQuantityError(f"quantidade com mais de {SCALE} casas decimais: {value}")
    return _check_range(scaled.numerator)


def _check_range(steps: int) -> int:
    if abs(steps) >= _MAX_STEPS:
        raise InvalidQuantityError(
            f"quantidade acima do limite de {MAX_INTEGER_DIGITS} dígitos inteiros"
        )
    return steps


def _from_steps(steps: int) -> Decimal:
    return Decimal(_check_range(steps)).scaleb(-SCALE)


@total_ordering
@dataclass(frozen=True, slots=True)
class Quantity:
    """Quantidade numa unidade. Igualdade é de valor **e** unidade: 1 kg != 1000 g."""

    value: Decimal
    unit: UnitOfMeasure

    def __post_init__(self) -> None:
        if not isinstance(self.value, Decimal):
            raise InvalidQuantityError(
                f"quantidade precisa ser Decimal (nunca float): {self.value!r}"
            )
        if not self.value.is_finite():
            raise InvalidQuantityError(f"quantidade precisa ser um número finito: {self.value}")
        if not isinstance(self.unit, UnitOfMeasure):
            raise InvalidQuantityError(f"quantidade sem unidade de medida válida: {self.unit!r}")
        _to_steps(self.value)

    @classmethod
    def zero(cls, unit: UnitOfMeasure) -> Self:
        return cls(Decimal(0), unit)

    def to(self, unit: UnitOfMeasure) -> Quantity:
        """Converte para outra unidade da mesma grandeza (arredonda uma vez, half-even, 6 casas)."""
        if unit.dimension is not self.unit.dimension:
            raise IncompatibleUnitsError(
                f"não dá para converter {self.unit} ({self.unit.dimension.label}) "
                f"em {unit} ({unit.dimension.label})"
            )
        if unit == self.unit:
            return self
        exact = Fraction(self.value) * Fraction(self.unit.factor) / Fraction(unit.factor)
        return Quantity(_from_steps(round(exact * _STEPS_PER_UNIT)), unit)

    def _same_unit_steps(self, other: Quantity, action: str) -> tuple[int, int]:
        if other.unit != self.unit:
            raise IncompatibleUnitsError(
                f"não dá para {action} {self.unit} com {other.unit}: converta antes"
            )
        return _to_steps(self.value), _to_steps(other.value)

    def __add__(self, other: object) -> Quantity:
        if not isinstance(other, Quantity):
            return NotImplemented
        a, b = self._same_unit_steps(other, "somar")
        return Quantity(_from_steps(a + b), self.unit)

    def __sub__(self, other: object) -> Quantity:
        if not isinstance(other, Quantity):
            return NotImplemented
        a, b = self._same_unit_steps(other, "subtrair")
        return Quantity(_from_steps(a - b), self.unit)

    def __neg__(self) -> Quantity:
        return Quantity(-self.value, self.unit)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Quantity):
            return NotImplemented
        a, b = self._same_unit_steps(other, "comparar")
        return a < b

    def __str__(self) -> str:
        return f"{self.value} {self.unit}"


def _unit(symbol: str, name: str, dimension: Dimension, factor: str) -> UnitOfMeasure:
    return UnitOfMeasure(symbol, name, dimension, Decimal(factor))


STANDARD_UNITS: MappingProxyType[str, UnitOfMeasure] = MappingProxyType(
    {
        unit.symbol: unit
        for unit in (
            _unit("un", "unidade", Dimension.COUNT, "1"),
            _unit("dz", "dúzia", Dimension.COUNT, "12"),
            _unit("kg", "quilograma", Dimension.MASS, "1"),
            _unit("g", "grama", Dimension.MASS, "0.001"),
            _unit("mg", "miligrama", Dimension.MASS, "0.000001"),
            _unit("L", "litro", Dimension.VOLUME, "1"),
            _unit("mL", "mililitro", Dimension.VOLUME, "0.001"),
            _unit("m", "metro", Dimension.LENGTH, "1"),
            _unit("cm", "centímetro", Dimension.LENGTH, "0.01"),
            _unit("mm", "milímetro", Dimension.LENGTH, "0.001"),
        )
    }
)
"""Catálogo padrão. Embalagens (caixa com 12) são unidades de contagem do perfil ou do usuário."""
