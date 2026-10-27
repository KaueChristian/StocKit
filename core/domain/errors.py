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


class ValidationError(DomainError):
    """Campo de entidade com valor inválido. ``field`` é o nome do atributo no código."""

    def __init__(self, field: str, message: str) -> None:
        super().__init__(message)
        self.field = field


class HierarchyError(DomainError):
    """Hierarquia de locais inconsistente: ciclo, pai inexistente ou nome repetido entre irmãos."""


class NotFoundError(DomainError):
    """Registro pedido não existe (``get`` ou ``update`` de algo que não foi gravado)."""


class ConflictError(DomainError):
    """Gravação que viola unicidade: ``id`` já gravado, SKU repetido, movimentação já lançada."""


class InactiveRecordError(DomainError):
    """Operação nova sobre cadastro inativo (item, local ou parte)."""


class InsufficientStockError(DomainError):
    """Saída deixaria o saldo negativo e a política proíbe (INV-05)."""


class SerialNumberError(DomainError):
    """Número de série em lugar impossível: entra já estando em estoque, ou sai de onde não está."""


class ProfileError(DomainError):
    """Perfil inválido. ``path`` diz onde, no JSON do perfil (ex.: ``custom_fields[2].type``)."""

    def __init__(self, path: str, message: str) -> None:
        super().__init__(f"{path}: {message}")
        self.path = path
        self.reason = message
