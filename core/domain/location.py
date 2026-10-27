"""Locais de estoque e sua hierarquia (RF-002).

Um local só conhece o pai. A ``LocationTree`` junta um conjunto de locais e garante as regras que
dependem do conjunto: todo pai existe, não há ciclo (um local dentro de si mesmo, direta ou
indiretamente) e irmãos não repetem nome. O saldo por local soma no total do item (INV-08, M1.7)
usando ``descendants``.
"""

from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field, replace
from typing import Self
from uuid import UUID

from core.domain.entity import Entity, clean_text, require_type, set_field
from core.domain.errors import HierarchyError, ValidationError
from core.domain.ids import LocationId, new_location_id

PATH_SEPARATOR = " › "


@dataclass(frozen=True, slots=True, kw_only=True, eq=False)
class Location(Entity):
    """Lugar onde há saldo: depósito, corredor, prateleira, caixa… ``parent_id`` vazio = raiz."""

    name: str
    parent_id: LocationId | None = None
    active: bool = True
    id: LocationId = field(default_factory=new_location_id)

    def __post_init__(self) -> None:
        set_field(self, "name", clean_text(self.name, "name", "nome do local", max_length=80))
        require_type(self.id, UUID, "id", "identificador do local")
        require_type(self.active, bool, "active", "active")
        if self.parent_id is not None:
            require_type(self.parent_id, UUID, "parent_id", "local pai")
            if self.parent_id == self.id:
                raise ValidationError(
                    "parent_id", f"o local {self.name!r} não pode ser pai de si mesmo"
                )

    def moved_to(self, parent_id: LocationId | None) -> Self:
        return replace(self, parent_id=parent_id)

    def deactivated(self) -> Self:
        return replace(self, active=False)


class LocationTree:
    """Conjunto de locais validado como árvore (na verdade, floresta: pode haver várias raízes)."""

    __slots__ = ("_by_id", "_children")

    def __init__(self, locations: Iterable[Location] = ()) -> None:
        by_id: dict[LocationId, Location] = {}
        for location in locations:
            if location.id in by_id:
                raise HierarchyError(f"local repetido no conjunto: {location.name!r}")
            by_id[location.id] = location
        self._by_id = by_id
        self._children = self._index_children()
        self._check_no_cycles()

    def _index_children(self) -> dict[LocationId | None, list[Location]]:
        children: dict[LocationId | None, list[Location]] = {}
        for location in self._by_id.values():
            parent = location.parent_id
            if parent is not None and parent not in self._by_id:
                raise HierarchyError(f"o local {location.name!r} aponta para um pai que não existe")
            siblings = children.setdefault(parent, [])
            if any(s.name.casefold() == location.name.casefold() for s in siblings):
                where = "na raiz" if parent is None else f"dentro de {self._by_id[parent].name!r}"
                raise HierarchyError(f"já existe um local chamado {location.name!r} {where}")
            siblings.append(location)
        for siblings in children.values():
            siblings.sort(key=lambda loc: loc.name.casefold())
        return children

    def _check_no_cycles(self) -> None:
        reachable_from_roots: set[LocationId] = set()
        pending = list(self._children.get(None, []))
        while pending:
            location = pending.pop()
            reachable_from_roots.add(location.id)
            pending.extend(self._children.get(location.id, []))
        stuck = [loc for loc in self._by_id.values() if loc.id not in reachable_from_roots]
        if stuck:
            names = ", ".join(sorted(repr(loc.name) for loc in stuck))
            raise HierarchyError(f"ciclo na hierarquia de locais: {names}")

    def __len__(self) -> int:
        return len(self._by_id)

    def __iter__(self) -> Iterator[Location]:
        return iter(self._by_id.values())

    def __contains__(self, location_id: object) -> bool:
        return location_id in self._by_id

    def get(self, location_id: LocationId) -> Location:
        try:
            return self._by_id[location_id]
        except KeyError:
            raise HierarchyError(f"local não encontrado: {location_id}") from None

    def roots(self) -> tuple[Location, ...]:
        return tuple(self._children.get(None, []))

    def children(self, location_id: LocationId) -> tuple[Location, ...]:
        self.get(location_id)
        return tuple(self._children.get(location_id, []))

    def descendants(self, location_id: LocationId) -> tuple[Location, ...]:
        """Todos os locais abaixo deste (sem incluir ele), em profundidade e em ordem de nome."""
        result: list[Location] = []
        for child in self.children(location_id):
            result.append(child)
            result.extend(self.descendants(child.id))
        return tuple(result)

    def path(self, location_id: LocationId) -> tuple[Location, ...]:
        """Da raiz até o local, inclusive."""
        chain = [self.get(location_id)]
        while (parent := chain[-1].parent_id) is not None:
            chain.append(self._by_id[parent])
        return tuple(reversed(chain))

    def full_name(self, location_id: LocationId) -> str:
        return PATH_SEPARATOR.join(loc.name for loc in self.path(location_id))

    def with_location(self, location: Location) -> LocationTree:
        """Nova árvore com o local incluído ou substituído (mesmo ``id``), validada de novo."""
        others = (loc for loc in self._by_id.values() if loc.id != location.id)
        return LocationTree([*others, location])
