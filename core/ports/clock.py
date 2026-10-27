"""Porta do relógio (§4, princípio 5: datas em UTC, relógio injetável)."""

from datetime import datetime
from typing import Protocol


class Clock(Protocol):
    """Fonte da hora atual. Testes usam um relógio fixo; o app usa o do sistema."""

    def now(self) -> datetime:
        """Hora atual **com fuso, em UTC**. Nunca devolve ``datetime`` sem fuso."""
        ...
