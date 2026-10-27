"""Cálculos sobre o livro de movimentações (funções puras).

O saldo nunca é guardado: é a soma de ``signed_quantity`` das movimentações (INV-01). A ordem do
livro é ``occurred_at`` e, no empate, a ordem em que as movimentações chegam — a mesma dos
repositórios.
"""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime

from core.domain.movement import Movement
from core.domain.quantity import Quantity, UnitOfMeasure


def balance(movements: Iterable[Movement], unit: UnitOfMeasure) -> Quantity:
    """Soma assinada. Todas as movimentações precisam estar em ``unit`` (a unidade base do item)."""
    total = Quantity.zero(unit)
    for movement in movements:
        total += movement.signed_quantity
    return total


def in_ledger_order(movements: Iterable[Movement]) -> list[Movement]:
    """Ordena por ``occurred_at``; ``sorted`` é estável, então o empate mantém a ordem recebida."""
    return sorted(movements, key=lambda m: m.occurred_at)


@dataclass(frozen=True, slots=True)
class NegativePoint:
    """Primeiro instante, a partir de uma movimentação, em que o saldo fica negativo."""

    at: datetime
    balance: Quantity


def first_negative_from(
    history: Sequence[Movement], new: Movement, unit: UnitOfMeasure
) -> NegativePoint | None:
    """Simula o livro com ``new`` incluída e procura saldo negativo **a partir dela**.

    ``history`` são as movimentações já lançadas do mesmo item, local e lote. ``new`` entra depois
    das que têm o mesmo ``occurred_at``, como acontecerá no repositório. Uma saída retroativa pode
    estar coberta na data dela e mesmo assim deixar negativo um ponto posterior: isso também conta.
    """
    timeline = in_ledger_order([*history, new])
    running = Quantity.zero(unit)
    reached_new = False
    for movement in timeline:
        running += movement.signed_quantity
        reached_new = reached_new or movement is new
        if reached_new and running.value < 0:
            return NegativePoint(movement.occurred_at, running)
    return None


def available_at(history: Sequence[Movement], at: datetime, unit: UnitOfMeasure) -> Quantity:
    """Quanto dá para tirar em ``at`` sem deixar nenhum ponto do livro, dali em diante, negativo.

    É o menor saldo entre o saldo em ``at`` e os saldos depois de cada movimentação posterior
    (nunca menos que zero). Usado pelo FEFO para repartir uma saída entre lotes.
    """
    running = Quantity.zero(unit)
    lowest: Quantity | None = None  # None até chegar em "at"
    for movement in in_ledger_order(history):
        if movement.occurred_at > at:
            if lowest is None:
                lowest = running  # saldo em "at"
            running += movement.signed_quantity
            lowest = running if running < lowest else lowest
        else:
            running += movement.signed_quantity
    if lowest is None:
        lowest = running
    zero = Quantity.zero(unit)
    return lowest if lowest > zero else zero
