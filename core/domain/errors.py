"""Erros de domínio tipados (M1.13, ADR-007).

Toda regra violada no núcleo vira uma subclasse de ``DomainError``. Cada classe tem:

- ``code``: identificador **estável** (``rule.insufficient_stock``) para a API e para traduções; o
  prefixo é a categoria;
- ``kind``: a categoria (``ErrorKind``), que diz à interface como reagir — destacar um campo,
  "não encontrado", conflito de cadastro ou regra de negócio — e à API qual status HTTP usar;
- ``message``: texto em PT-BR para o usuário final;
- ``details``: dados estruturados (SKU, local, campo, quanto falta…), para a tela montar a própria
  mensagem ou a API devolver em JSON (``to_dict``).

Hierarquia::

    DomainError
    ├── ValidationError            invalid            entrada inválida (``field`` diz qual)
    │   ├── InvalidUnitError       invalid.unit
    │   ├── InvalidQuantityError   invalid.quantity
    │   ├── IncompatibleUnitsError invalid.units
    │   ├── CustomFieldError       invalid.custom_field (``custom_fields.<chave>``)
    │   └── ProfileError           invalid.profile    (``path`` diz onde, no JSON do perfil)
    ├── NotFoundError              not_found
    ├── ConflictError              conflict
    └── BusinessRuleError          rule               regra de negócio recusou a operação
        ├── InsufficientStockError rule.insufficient_stock
        ├── SerialNumberError      rule.serial_number
        ├── InactiveRecordError    rule.inactive_record
        └── HierarchyError         rule.location_hierarchy
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum, StrEnum
from typing import ClassVar
from uuid import UUID


class ErrorKind(StrEnum):
    """Categoria do erro. Mapeamento sugerido para HTTP no ADR-007."""

    INVALID = "invalid"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    RULE = "rule"


type JsonScalar = str | int | bool | None


def _json_safe(value: object) -> JsonScalar:
    if isinstance(value, Enum):
        # Enum com ``code`` (MovementKind) usa o código gravado; os outros, o valor.
        return _json_safe(getattr(value, "code", value.value))
    if value is None or isinstance(value, bool | int | str):
        return value
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, Decimal | UUID):
        return str(value)
    return str(value)  # Quantity, Location... têm __str__ legível


class DomainError(Exception):
    """Base dos erros de regra de negócio. Não é levantada diretamente: use uma subclasse."""

    code: ClassVar[str] = "domain"
    kind: ClassVar[ErrorKind] = ErrorKind.RULE

    def __init__(self, message: str, **details: object) -> None:
        super().__init__(message)
        self.message = message
        self.details = details

    def to_dict(self) -> dict[str, object]:
        """Forma estável para JSON (API, log): código, categoria, mensagem e detalhes."""
        return {
            "code": self.code,
            "kind": self.kind.value,
            "message": self.message,
            "details": {key: _json_safe(value) for key, value in self.details.items()},
        }


# --- entrada inválida --------------------------------------------------------------------


class ValidationError(DomainError):
    """Valor de entrada inválido. ``field`` é o nome do atributo no código (``sku``,
    ``custom_fields.temperatura``) — a tela usa para destacar o campo."""

    code = "invalid"
    kind = ErrorKind.INVALID

    def __init__(self, field: str, message: str, **details: object) -> None:
        super().__init__(message, field=field, **details)
        self.field = field


class InvalidUnitError(ValidationError):
    """Definição de unidade de medida inválida (símbolo, nome, grandeza ou fator)."""

    code = "invalid.unit"

    def __init__(self, message: str, **details: object) -> None:
        super().__init__("unit", message, **details)


class InvalidQuantityError(ValidationError):
    """Quantidade inválida: não é ``Decimal``, não é finita, passa de 6 casas ou do limite."""

    code = "invalid.quantity"

    def __init__(self, message: str, **details: object) -> None:
        super().__init__("quantity", message, **details)


class IncompatibleUnitsError(ValidationError):
    """Operação entre unidades diferentes, conversão entre grandezas diferentes ou conversão que
    arredondaria uma quantidade lançada."""

    code = "invalid.units"

    def __init__(self, message: str, **details: object) -> None:
        super().__init__("quantity", message, **details)


class CustomFieldError(ValidationError):
    """Valor de campo personalizado inválido; ``field`` = ``custom_fields.<chave>`` (TP-M1-07)."""

    code = "invalid.custom_field"

    def __init__(self, key: str, message: str) -> None:
        super().__init__(f"custom_fields.{key}", message, key=key)
        self.key = key


class ProfileError(ValidationError):
    """Perfil inválido. ``path`` diz onde, no JSON do perfil (ex.: ``custom_fields[2].type``)."""

    code = "invalid.profile"

    def __init__(self, path: str, message: str) -> None:
        super().__init__(path, f"{path}: {message}", path=path, reason=message)
        self.path = path
        self.reason = message


# --- cadastro ----------------------------------------------------------------------------


class NotFoundError(DomainError):
    """Registro pedido não existe (``get`` ou ``update`` de algo que não foi gravado)."""

    code = "not_found"
    kind = ErrorKind.NOT_FOUND


class ConflictError(DomainError):
    """Gravação que viola unicidade: ``id`` já gravado, SKU repetido, movimentação já lançada."""

    code = "conflict"
    kind = ErrorKind.CONFLICT


# --- regras de negócio -------------------------------------------------------------------


class BusinessRuleError(DomainError):
    """Os dados estão certos, mas uma regra do estoque não permite a operação."""

    code = "rule"
    kind = ErrorKind.RULE


class InsufficientStockError(BusinessRuleError):
    """Saída deixaria o saldo negativo e a política proíbe (INV-05)."""

    code = "rule.insufficient_stock"


class SerialNumberError(BusinessRuleError):
    """Número de série em lugar impossível: entra já estando em estoque, ou sai de onde não está."""

    code = "rule.serial_number"


class InactiveRecordError(BusinessRuleError):
    """Operação nova sobre cadastro inativo (item, local ou parte)."""

    code = "rule.inactive_record"


class HierarchyError(BusinessRuleError):
    """Hierarquia de locais inconsistente: ciclo, pai inexistente ou nome repetido entre irmãos."""

    code = "rule.location_hierarchy"
