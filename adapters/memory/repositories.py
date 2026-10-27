"""Repositórios em memória (M1.5).

Implementam as portas de ``core.ports.repositories`` sobre dicionários de um ``MemoryState``. Não
gravam nada sozinhos: quem dá vida a eles é a ``MemoryUnitOfWork``, que entrega uma cópia de
trabalho do estado e só a torna definitiva no ``commit``.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import datetime

from core.domain.catalog import Category, Item, ItemKind
from core.domain.custom_fields import CustomFieldDefinition
from core.domain.entity import Entity
from core.domain.errors import ConflictError, NotFoundError
from core.domain.ids import (
    CategoryId,
    CustomFieldId,
    ItemId,
    LocationId,
    LotId,
    MovementId,
    PartyId,
    TransferId,
)
from core.domain.location import Location
from core.domain.lot import Lot, fefo_order
from core.domain.movement import Movement, MovementKind
from core.domain.party import Party


@dataclass
class MemoryState:
    """Tudo o que o armazenamento em memória guarda. Entidades são imutáveis: copiar o estado é
    copiar os contêineres, nunca as entidades."""

    items: dict[ItemId, Item] = field(default_factory=dict)
    categories: dict[CategoryId, Category] = field(default_factory=dict)
    locations: dict[LocationId, Location] = field(default_factory=dict)
    parties: dict[PartyId, Party] = field(default_factory=dict)
    lots: dict[LotId, Lot] = field(default_factory=dict)
    custom_fields: dict[CustomFieldId, CustomFieldDefinition] = field(default_factory=dict)
    movements: list[Movement] = field(default_factory=list)

    def copy(self) -> MemoryState:
        return MemoryState(
            items=dict(self.items),
            categories=dict(self.categories),
            locations=dict(self.locations),
            parties=dict(self.parties),
            lots=dict(self.lots),
            custom_fields=dict(self.custom_fields),
            movements=list(self.movements),
        )


class _Registry[E: Entity, K]:
    """Cadastro genérico: ``get``/``add``/``update``/``list`` com as regras comuns das portas."""

    def __init__(self, data: dict[K, E], label: str, sort_key: Callable[[E], str]) -> None:
        self._data = data
        self._label = label
        self._sort_key = sort_key

    def get(self, entity_id: K) -> E:
        try:
            return self._data[entity_id]
        except KeyError:
            raise NotFoundError(f"{self._label} não encontrado(a): {entity_id}") from None

    def add(self, entity: E) -> None:
        key = self._key(entity)
        if key in self._data:
            raise ConflictError(f"{self._label} já cadastrado(a): {key}")
        self._check_unique(entity)
        self._data[key] = entity

    def update(self, entity: E) -> None:
        key = self._key(entity)
        if key not in self._data:
            raise NotFoundError(f"{self._label} não encontrado(a) para atualizar: {key}")
        self._check_unique(entity)
        self._data[key] = entity

    def list(self) -> Sequence[E]:
        return tuple(sorted(self._data.values(), key=self._sort_key))

    def _key(self, entity: E) -> K:
        return entity.id  # type: ignore[return-value]  # o id de cada entidade é do tipo K

    def _check_unique(self, entity: E) -> None:
        """Regras de unicidade além do ``id`` (sobrescrito por quem precisa)."""


class MemoryItemRepository(_Registry[Item, ItemId]):
    def __init__(self, data: dict[ItemId, Item]) -> None:
        super().__init__(data, "item", lambda item: item.sku)

    def find_by_sku(self, sku: str) -> Item | None:
        return next((item for item in self._data.values() if item.sku == sku), None)

    def _check_unique(self, entity: Item) -> None:
        other = self.find_by_sku(entity.sku)
        if other is not None and other.id != entity.id:
            raise ConflictError(f"SKU {entity.sku} já pertence a outro item ({other.name})")


def _by_name(entity: Category | Location | Party) -> str:
    return entity.name.casefold()


class MemoryCategoryRepository(_Registry[Category, CategoryId]):
    def __init__(self, data: dict[CategoryId, Category]) -> None:
        super().__init__(data, "categoria", _by_name)


class MemoryLocationRepository(_Registry[Location, LocationId]):
    def __init__(self, data: dict[LocationId, Location]) -> None:
        super().__init__(data, "local", _by_name)


class MemoryPartyRepository(_Registry[Party, PartyId]):
    def __init__(self, data: dict[PartyId, Party]) -> None:
        super().__init__(data, "parte", _by_name)


class MemoryLotRepository(_Registry[Lot, LotId]):
    def __init__(self, data: dict[LotId, Lot]) -> None:
        super().__init__(data, "lote", lambda lot: lot.code)

    def list(self) -> Sequence[Lot]:
        by_item: dict[ItemId, list[Lot]] = {}
        for lot in self._data.values():
            by_item.setdefault(lot.item_id, []).append(lot)
        return tuple(lot for item_id in sorted(by_item) for lot in fefo_order(by_item[item_id]))

    def find_by_code(self, item_id: ItemId, code: str) -> Lot | None:
        return next(
            (lot for lot in self._data.values() if lot.item_id == item_id and lot.code == code),
            None,
        )

    def list_for_item(self, item_id: ItemId) -> Sequence[Lot]:
        return tuple(fefo_order(lot for lot in self._data.values() if lot.item_id == item_id))

    def _check_unique(self, entity: Lot) -> None:
        other = self.find_by_code(entity.item_id, entity.code)
        if other is not None and other.id != entity.id:
            raise ConflictError(f"o item já tem um lote com o código {entity.code}")


class MemoryCustomFieldRepository(_Registry[CustomFieldDefinition, CustomFieldId]):
    def __init__(self, data: dict[CustomFieldId, CustomFieldDefinition]) -> None:
        super().__init__(data, "campo personalizado", lambda d: d.key)

    def find_by_key(self, key: str) -> CustomFieldDefinition | None:
        return next((d for d in self._data.values() if d.key == key), None)

    def list_for_kind(self, kind: ItemKind) -> Sequence[CustomFieldDefinition]:
        return tuple(d for d in self.list() if kind in d.kinds)

    def _check_unique(self, entity: CustomFieldDefinition) -> None:
        other = self.find_by_key(entity.key)
        if other is not None and other.id != entity.id:
            raise ConflictError(f"já existe um campo com a chave {entity.key}")


class MemoryMovementRepository:
    """Livro em memória: lista na ordem de lançamento; só cresce (INV-02)."""

    def __init__(self, data: list[Movement]) -> None:
        self._data = data

    def append(self, movement: Movement) -> None:
        if any(existing.id == movement.id for existing in self._data):
            raise ConflictError(f"movimentação já lançada: {movement.id}")
        self._data.append(movement)

    def get(self, movement_id: MovementId) -> Movement:
        for movement in self._data:
            if movement.id == movement_id:
                return movement
        raise NotFoundError(f"movimentação não encontrada: {movement_id}")

    def list(
        self,
        *,
        item_id: ItemId | None = None,
        location_id: LocationId | None = None,
        lot_id: LotId | None = None,
        until: datetime | None = None,
    ) -> Sequence[Movement]:
        selected = [
            m
            for m in self._data
            if (item_id is None or m.item_id == item_id)
            and (location_id is None or m.location_id == location_id)
            and (lot_id is None or m.lot_id == lot_id)
            and (until is None or m.occurred_at <= until)
        ]
        # sorted é estável: no empate de occurred_at fica a ordem de lançamento.
        return tuple(sorted(selected, key=lambda m: m.occurred_at))

    def transfer_pair(self, transfer_id: TransferId) -> tuple[Movement, Movement]:
        sides = {m.kind: m for m in self._data if m.transfer_id == transfer_id}
        try:
            return sides[MovementKind.TRANSFER_OUT], sides[MovementKind.TRANSFER_IN]
        except KeyError:
            raise NotFoundError(f"par de transferência incompleto: {transfer_id}") from None
