"""Números de série no livro (M1.10, RF-009, INV-07).

Cada número de série é uma unidade física: ou está em estoque num local, ou está fora. Na linha do
tempo de uma série, entradas e saídas se alternam — entra (de fora para um local), sai (daquele
local para fora). Transferência é uma saída e uma entrada no mesmo instante. Assim nenhuma série
fica em dois lugares, e o saldo de item serializado é sempre inteiro.
"""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from core.domain.ids import LocationId
from core.domain.ledger import in_ledger_order
from core.domain.movement import Direction, Movement


class SerialProblem(StrEnum):
    ALREADY_IN_STOCK = "already_in_stock"
    """Entrada de série que já está em estoque (num local qualquer)."""
    NOT_HERE = "not_here"
    """Saída de série que não está naquele local naquele momento."""


@dataclass(frozen=True, slots=True)
class SerialConflict:
    serial: str
    at: datetime
    problem: SerialProblem
    location_id: LocationId
    """Onde a movimentação em conflito acontece."""
    current: LocationId | None
    """Onde a série estava naquele momento (``None`` = fora do estoque)."""


def serial_positions(movements: Iterable[Movement]) -> dict[str, LocationId | None]:
    """Onde cada série está depois das movimentações dadas (``None`` = saiu do estoque)."""
    positions: dict[str, LocationId | None] = {}
    for movement in in_ledger_order(movements):
        for serial in movement.serials:
            positions[serial] = movement.location_id if movement.direction is Direction.IN else None
    return positions


def first_serial_conflict(
    history: Sequence[Movement], new: Sequence[Movement]
) -> SerialConflict | None:
    """Simula o livro com ``new`` incluídas (depois das de mesmo instante, na ordem dada) e
    devolve a primeira quebra da alternância entrada/saída das séries de ``new``."""
    watched = {serial for movement in new for serial in movement.serials}
    position: dict[str, LocationId | None] = {}
    for movement in in_ledger_order([*history, *new]):
        for serial in movement.serials & watched:
            current = position.get(serial)
            if movement.direction is Direction.IN:
                if current is not None:
                    return SerialConflict(
                        serial,
                        movement.occurred_at,
                        SerialProblem.ALREADY_IN_STOCK,
                        movement.location_id,
                        current,
                    )
                position[serial] = movement.location_id
            else:
                if current != movement.location_id:
                    return SerialConflict(
                        serial,
                        movement.occurred_at,
                        SerialProblem.NOT_HERE,
                        movement.location_id,
                        current,
                    )
                position[serial] = None
    return None
