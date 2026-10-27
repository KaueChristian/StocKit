"""Portas de repositório: o que o núcleo precisa de qualquer armazenamento.

Regras comuns, que a suíte de contrato (M2.6) cobra de todo adaptador (memória, SQLite, Django ORM):

- ``get`` devolve a entidade ou levanta ``NotFoundError``; nunca devolve ``None``.
- ``add`` grava uma entidade nova; ``id`` já gravado levanta ``ConflictError``.
- ``update`` grava uma nova versão de uma entidade existente (mesmo ``id``); se não existe,
  levanta ``NotFoundError``. Entidades são imutáveis: a versão nova é outro objeto
  (``dataclasses.replace``).
- ``list`` devolve uma tupla em ordem estável e documentada em cada porta.
- Nada é gravado de fato antes do ``commit`` da ``UnitOfWork`` em que o repositório foi obtido.

O livro de movimentações é diferente: só tem ``append`` (INV-02); não existe ``update`` nem
``delete``. Nenhum repositório tem ``delete``: cadastro se inativa, porque o histórico aponta para
ele.
"""

from collections.abc import Sequence
from datetime import datetime
from typing import Protocol

from core.domain.catalog import Category, Item
from core.domain.ids import (
    CategoryId,
    ItemId,
    LocationId,
    LotId,
    MovementId,
    PartyId,
    TransferId,
)
from core.domain.location import Location
from core.domain.movement import Movement
from core.domain.party import Party


class Repository[E, K](Protocol):
    """Operações comuns de cadastro (entidade ``E`` com identificador ``K``)."""

    def get(self, entity_id: K) -> E: ...

    def add(self, entity: E) -> None: ...

    def update(self, entity: E) -> None: ...

    def list(self) -> Sequence[E]: ...


class ItemRepository(Repository[Item, ItemId], Protocol):
    """Itens. ``list`` em ordem de SKU. SKU é único (``add``/``update`` com SKU de outro item:
    ``ConflictError``)."""

    def find_by_sku(self, sku: str) -> Item | None:
        """Busca exata pelo SKU já normalizado (maiúsculas, sem espaços nas pontas)."""
        ...


class CategoryRepository(Repository[Category, CategoryId], Protocol):
    """Categorias. ``list`` em ordem de nome, sem diferenciar maiúsculas."""


class LocationRepository(Repository[Location, LocationId], Protocol):
    """Locais. ``list`` devolve todos (ativos e inativos), em ordem de nome, sem diferenciar
    maiúsculas. Ciclo e nome repetido são conferidos pelo serviço com ``LocationTree`` antes de
    gravar."""


class PartyRepository(Repository[Party, PartyId], Protocol):
    """Partes. ``list`` em ordem de nome, sem diferenciar maiúsculas."""


class MovementRepository(Protocol):
    """Livro de movimentações: só acrescenta (INV-02, ADR-004)."""

    def append(self, movement: Movement) -> None:
        """Acrescenta uma movimentação. ``id`` já lançado levanta ``ConflictError``."""
        ...

    def get(self, movement_id: MovementId) -> Movement: ...

    def list(
        self,
        *,
        item_id: ItemId | None = None,
        location_id: LocationId | None = None,
        lot_id: LotId | None = None,
        until: datetime | None = None,
    ) -> Sequence[Movement]:
        """Movimentações que batem com **todos** os filtros informados.

        ``until`` inclui o instante dado (saldo "em uma data", RF-006). Ordem: ``occurred_at`` e,
        no empate, ordem de lançamento — a mesma em qualquer adaptador.
        """
        ...

    def transfer_pair(self, transfer_id: TransferId) -> tuple[Movement, Movement]:
        """As duas pontas de uma transferência, (saída, entrada). Sem o par: ``NotFoundError``."""
        ...
