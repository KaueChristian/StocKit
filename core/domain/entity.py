"""Base das entidades e validação de texto compartilhada.

Entidades são imutáveis (``frozen``) e têm identidade: duas instâncias com o mesmo ``id`` são a
mesma entidade, mesmo com outros campos diferentes (uma é a versão editada da outra). Editar é criar
uma cópia com ``dataclasses.replace``, que roda a validação de novo.
"""

from typing import Any
from uuid import UUID

from core.domain.errors import ValidationError


class Entity:
    """Igualdade e hash pelo tipo e pelo ``id``."""

    __slots__ = ()

    id: UUID

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Entity):
            return NotImplemented
        return type(other) is type(self) and other.id == self.id

    def __hash__(self) -> int:
        return hash((type(self), self.id))


def clean_text(value: object, field: str, label: str, *, max_length: int) -> str:
    """Tira espaços das pontas e junta espaços repetidos; recusa vazio e texto longo demais."""
    if not isinstance(value, str):
        raise ValidationError(field, f"{label} precisa ser texto")
    cleaned = " ".join(value.split())
    if not cleaned:
        raise ValidationError(field, f"{label} não pode ficar vazio")
    if len(cleaned) > max_length:
        raise ValidationError(field, f"{label} passa de {max_length} caracteres")
    return cleaned


def require_type(value: object, expected: type[Any], field: str, label: str) -> None:
    if not isinstance(value, expected):
        raise ValidationError(field, f"{label} inválido: {value!r}")


def set_field(entity: object, name: str, value: object) -> None:
    """Grava um campo já normalizado numa dataclass congelada (só dentro do ``__post_init__``)."""
    object.__setattr__(entity, name, value)
