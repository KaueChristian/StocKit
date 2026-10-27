"""Erros de domínio tipados (M1.13, ADR-007): códigos estáveis, categorias e detalhes em JSON."""

import ast
import inspect
import json
import re
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest

from core.domain import errors
from core.domain.errors import (
    BusinessRuleError,
    ConflictError,
    CustomFieldError,
    DomainError,
    ErrorKind,
    IncompatibleUnitsError,
    InsufficientStockError,
    InvalidQuantityError,
    InvalidUnitError,
    NotFoundError,
    ProfileError,
    ValidationError,
)
from core.domain.movement import Direction, MovementKind
from core.domain.quantity import STANDARD_UNITS, Quantity
from core.domain.serials import SerialProblem

CORE = Path(__file__).resolve().parents[3] / "core"
ERROR_CLASSES = [
    cls
    for _, cls in inspect.getmembers(errors, inspect.isclass)
    if issubclass(cls, DomainError) and cls.__module__ == errors.__name__
]
CODE = re.compile(r"[a-z_]+(\.[a-z_]+)?")


def test_every_error_has_a_unique_well_formed_code() -> None:
    codes = [cls.code for cls in ERROR_CLASSES]
    assert len(codes) == len(set(codes)), "código repetido"
    assert all(CODE.fullmatch(code) for code in codes)
    assert len(ERROR_CLASSES) == 14


@pytest.mark.parametrize("cls", ERROR_CLASSES, ids=lambda c: c.__name__)
def test_code_starts_with_the_kind(cls: type[DomainError]) -> None:
    if cls is DomainError:
        return
    assert cls.code.split(".")[0] == cls.kind.value


@pytest.mark.parametrize(
    ("cls", "parent", "kind"),
    [
        (InvalidUnitError, ValidationError, ErrorKind.INVALID),
        (InvalidQuantityError, ValidationError, ErrorKind.INVALID),
        (IncompatibleUnitsError, ValidationError, ErrorKind.INVALID),
        (ProfileError, ValidationError, ErrorKind.INVALID),
        (CustomFieldError, ValidationError, ErrorKind.INVALID),
        (NotFoundError, DomainError, ErrorKind.NOT_FOUND),
        (ConflictError, DomainError, ErrorKind.CONFLICT),
        (InsufficientStockError, BusinessRuleError, ErrorKind.RULE),
    ],
)
def test_hierarchy(cls: type[DomainError], parent: type[DomainError], kind: ErrorKind) -> None:
    assert issubclass(cls, parent)
    assert cls.kind is kind


def test_to_dict_is_plain_json() -> None:
    when = datetime(2026, 10, 27, 15, tzinfo=UTC)
    some_id = uuid4()
    error = InsufficientStockError(
        "saldo insuficiente",
        sku="PAR-001",
        balance=Quantity(Decimal(-2), STANDARD_UNITS["un"]),
        at=when,
        day=date(2026, 10, 27),
        id=some_id,
        cost=Decimal("1.50"),
        problem=SerialProblem.NOT_HERE,
        kind=MovementKind.ISSUE,
        direction=Direction.OUT,
        count=3,
        exact=True,
        nothing=None,
    )
    data = error.to_dict()
    assert json.loads(json.dumps(data)) == data
    assert data == {
        "code": "rule.insufficient_stock",
        "kind": "rule",
        "message": "saldo insuficiente",
        "details": {
            "sku": "PAR-001",
            "balance": "-2 un",
            "at": "2026-10-27T15:00:00+00:00",
            "day": "2026-10-27",
            "id": str(some_id),
            "cost": "1.50",
            "problem": "not_here",
            "kind": "issue",
            "direction": -1,
            "count": 3,
            "exact": True,
            "nothing": None,
        },
    }
    assert str(error) == error.message
    assert type(data["details"]["problem"]) is str  # type: ignore[index]


def test_validation_errors_carry_the_field() -> None:
    error = ValidationError("custom_fields.temperatura", "obrigatório")
    assert (error.field, error.to_dict()["details"]) == (
        "custom_fields.temperatura",
        {"field": "custom_fields.temperatura"},
    )
    assert InvalidQuantityError("x").field == "quantity"
    assert InvalidUnitError("x").field == "unit"
    assert IncompatibleUnitsError("x").field == "quantity"
    custom = CustomFieldError("temperatura", "obrigatório")
    assert (custom.field, custom.key, custom.code) == (
        "custom_fields.temperatura",
        "temperatura",
        "invalid.custom_field",
    )


def test_profile_error_keeps_path_and_reason() -> None:
    error = ProfileError("units[0].factor", "número inválido")
    assert (error.path, error.reason, error.field) == (
        "units[0].factor",
        "número inválido",
        "units[0].factor",
    )
    assert error.message == "units[0].factor: número inválido"
    assert error.to_dict()["details"] == {
        "field": "units[0].factor",
        "path": "units[0].factor",
        "reason": "número inválido",
    }


# --- arquitetura: o núcleo só levanta erros de domínio ------------------------------------

ALLOWED = {cls.__name__ for cls in ERROR_CLASSES} - {"DomainError"}


def _raised_names(tree: ast.AST) -> list[tuple[int, str]]:
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Raise) and node.exc is not None:
            target = node.exc.func if isinstance(node.exc, ast.Call) else node.exc
            name = target.id if isinstance(target, ast.Name) else ast.unparse(target)
            found.append((node.lineno, name))
    return found


@pytest.mark.parametrize(
    "module", sorted(CORE.rglob("*.py")), ids=lambda p: str(p.relative_to(CORE))
)
def test_core_raises_only_specific_domain_errors(module: Path) -> None:
    """Interface e API contam com código e categoria: ``ValueError`` ou ``DomainError`` cru
    escapando do núcleo viraria erro 500 / tela genérica."""
    tree = ast.parse(module.read_text(encoding="utf-8"))
    wrong = [f"linha {line}: {name}" for line, name in _raised_names(tree) if name not in ALLOWED]
    assert not wrong, f"{module.name} levanta erro fora da hierarquia: {wrong}"


def test_the_architecture_check_sees_raises() -> None:
    """Controle: o detector acha ``raise`` com e sem chamada, e com ``from``."""
    sample = (
        "raise ValueError('x')\nraise KeyError\n"
        "try:\n    pass\nexcept E:\n    raise X() from None\n"
    )
    assert [n for _, n in _raised_names(ast.parse(sample))] == ["ValueError", "KeyError", "X"]
