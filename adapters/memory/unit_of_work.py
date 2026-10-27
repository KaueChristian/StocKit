"""Unit of Work em memória (M1.5).

Várias ``MemoryUnitOfWork`` podem compartilhar o mesmo ``MemoryState`` confirmado — como várias
conexões ao mesmo banco. Dentro do ``with``, os repositórios trabalham numa **cópia**; ``commit``
a torna o novo estado confirmado, ``rollback`` (ou sair do bloco sem ``commit``) a descarta.
"""

from types import TracebackType
from typing import Self

from adapters.memory.repositories import (
    MemoryCategoryRepository,
    MemoryItemRepository,
    MemoryLocationRepository,
    MemoryLotRepository,
    MemoryMovementRepository,
    MemoryPartyRepository,
    MemoryState,
)


class MemoryUnitOfWork:
    def __init__(self, state: MemoryState | None = None) -> None:
        self.committed_state = state if state is not None else MemoryState()
        self._working: MemoryState | None = None

    def __enter__(self) -> Self:
        if self._working is not None:
            raise RuntimeError(
                "esta Unit of Work já está aberta; blocos aninhados não são suportados"
            )
        self._begin()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._working = None  # o que não teve commit se perde aqui

    def commit(self) -> None:
        state = self._require_open()
        # O estado confirmado passa a usar os contêineres do rascunho; o _begin seguinte dá ao
        # rascunho cópias novas, então o que vier depois do commit não vaza para o confirmado.
        vars(self.committed_state).update(vars(state))
        self._begin()

    def rollback(self) -> None:
        self._require_open()
        self._begin()

    def _begin(self) -> None:
        self._working = self.committed_state.copy()

    def _require_open(self) -> MemoryState:
        if self._working is None:
            raise RuntimeError("use a Unit of Work dentro de um bloco 'with'")
        return self._working

    @property
    def items(self) -> MemoryItemRepository:
        return MemoryItemRepository(self._require_open().items)

    @property
    def categories(self) -> MemoryCategoryRepository:
        return MemoryCategoryRepository(self._require_open().categories)

    @property
    def locations(self) -> MemoryLocationRepository:
        return MemoryLocationRepository(self._require_open().locations)

    @property
    def parties(self) -> MemoryPartyRepository:
        return MemoryPartyRepository(self._require_open().parties)

    @property
    def lots(self) -> MemoryLotRepository:
        return MemoryLotRepository(self._require_open().lots)

    @property
    def movements(self) -> MemoryMovementRepository:
        return MemoryMovementRepository(self._require_open().movements)
