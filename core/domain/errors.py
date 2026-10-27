"""Erros de domínio.

Toda regra de negócio violada vira uma subclasse de ``DomainError``, para que a interface (desktop e
web) mostre a mensagem sem conhecer a regra. A hierarquia completa, com códigos para a API, chega na
M1.13.
"""


class DomainError(Exception):
    """Base dos erros de regra de negócio. A mensagem é legível pelo usuário final (PT-BR)."""


class InvalidUnitError(DomainError):
    """Definição de unidade de medida inválida (símbolo, nome, grandeza ou fator)."""


class InvalidQuantityError(DomainError):
    """Quantidade inválida: não é ``Decimal``, não é finita, passa de 6 casas ou do limite."""


class IncompatibleUnitsError(DomainError):
    """Operação entre unidades diferentes, ou conversão entre grandezas diferentes."""
