"""Porta da Unit of Work: agrupa gravações numa transação (tudo ou nada).

Uso nos serviços::

    with uow:
        uow.movements.append(saida)
        uow.movements.append(entrada)
        uow.commit()

Sair do bloco sem ``commit`` — por exceção ou não — desfaz tudo o que foi feito nele. Depois do
``commit`` ou do ``rollback`` o bloco pode continuar e gravar de novo.
"""

from types import TracebackType
from typing import Protocol, Self

from core.ports.repositories import (
    CategoryRepository,
    CustomFieldRepository,
    ItemRepository,
    LocationRepository,
    LotRepository,
    MovementRepository,
    PartyRepository,
    SettingsRepository,
)


class UnitOfWork(Protocol):
    @property
    def items(self) -> ItemRepository: ...

    @property
    def categories(self) -> CategoryRepository: ...

    @property
    def locations(self) -> LocationRepository: ...

    @property
    def parties(self) -> PartyRepository: ...

    @property
    def lots(self) -> LotRepository: ...

    @property
    def custom_fields(self) -> CustomFieldRepository: ...

    @property
    def settings(self) -> SettingsRepository: ...

    @property
    def movements(self) -> MovementRepository: ...

    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Desfaz o que não teve ``commit``. Não engole exceções."""
        ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...
