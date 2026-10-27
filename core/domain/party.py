"""Partes: com quem o estoque troca itens (RF-003)."""

from collections.abc import Iterable
from dataclasses import dataclass, field, replace
from enum import StrEnum
from typing import Self
from uuid import UUID

from core.domain.entity import Entity, clean_text, require_type, set_field
from core.domain.errors import ValidationError
from core.domain.ids import PartyId, new_party_id


class PartyRole(StrEnum):
    """Papel de uma parte. O perfil pode trocar o rótulo exibido (ex.: "setor" → "oficina")."""

    SUPPLIER = "supplier"
    CUSTOMER = "customer"
    DEPARTMENT = "department"


@dataclass(frozen=True, slots=True, kw_only=True, eq=False)
class Party(Entity):
    """Fornecedor, cliente ou setor interno. Uma parte pode ter mais de um papel."""

    name: str
    roles: frozenset[PartyRole]
    active: bool = True
    id: PartyId = field(default_factory=new_party_id)

    def __post_init__(self) -> None:
        set_field(self, "name", clean_text(self.name, "name", "nome da parte", max_length=120))
        set_field(self, "roles", _clean_roles(self.roles, self.name))
        require_type(self.id, UUID, "id", "identificador da parte")
        require_type(self.active, bool, "active", "active")

    def has_role(self, role: PartyRole) -> bool:
        return role in self.roles

    def deactivated(self) -> Self:
        return replace(self, active=False)


def _clean_roles(roles: object, name: str) -> frozenset[PartyRole]:
    if isinstance(roles, str) or not isinstance(roles, Iterable):
        raise ValidationError("roles", f"os papéis de {name!r} precisam ser uma coleção")
    cleaned = frozenset(roles)
    invalid = [r for r in cleaned if not isinstance(r, PartyRole)]
    if invalid:
        raise ValidationError("roles", f"papel inválido para {name!r}: {invalid[0]!r}")
    if not cleaned:
        raise ValidationError("roles", f"a parte {name!r} precisa de pelo menos um papel")
    return cleaned
