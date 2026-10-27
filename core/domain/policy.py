"""Políticas configuráveis do estoque. A configuração completa do sistema chega na M1.12."""

from enum import StrEnum


class NegativeStockPolicy(StrEnum):
    """O que fazer com uma saída maior que o saldo (INV-05, RF-007)."""

    FORBID = "forbid"
    """Padrão: recusa a movimentação com ``InsufficientStockError``."""
    ALLOW = "allow"
    """Aceita; o saldo fica negativo até alguém lançar a entrada que faltou."""
