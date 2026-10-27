"""Relógios que implementam a porta ``Clock`` (M1.5)."""

from datetime import UTC, datetime, timedelta


class SystemClock:
    """Hora real do sistema, em UTC. É o relógio dos apps."""

    def now(self) -> datetime:
        return datetime.now(UTC)


class FixedClock:
    """Relógio parado, para testes e para o dataset demo: só anda quando ``advance`` é chamado."""

    def __init__(self, at: datetime) -> None:
        if at.tzinfo is None or at.utcoffset() is None:
            raise ValueError("FixedClock precisa de um datetime com fuso")
        self._now = at.astimezone(UTC)

    def now(self) -> datetime:
        return self._now

    def advance(self, delta: timedelta) -> None:
        if delta < timedelta(0):
            raise ValueError("o relógio não volta no tempo")
        self._now += delta
