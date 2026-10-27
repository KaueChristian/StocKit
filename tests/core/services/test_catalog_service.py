"""Cadastro de itens com campos personalizados (M1.11, RF-001, RF-004; caso TP-M1-07)."""

from dataclasses import replace
from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from adapters.memory.repositories import MemoryState
from adapters.memory.unit_of_work import MemoryUnitOfWork
from core.domain.catalog import Category, Item, ItemKind
from core.domain.custom_fields import CustomFieldDefinition, CustomFieldType
from core.domain.errors import ConflictError, NotFoundError, ValidationError
from core.domain.ids import CategoryId
from core.domain.quantity import STANDARD_UNITS
from core.services.catalog import define_custom_field, register_item, update_item

pytestmark = pytest.mark.req("RF-004")

UN, KG = STANDARD_UNITS["un"], STANDARD_UNITS["kg"]


class Kitchen:
    def __init__(self) -> None:
        self.state = MemoryState()
        self.temperature = define_custom_field(
            self.uow(),
            CustomFieldDefinition(
                key="temperatura",
                label="Temperatura de armazenamento",
                field_type=CustomFieldType.NUMBER,
                kinds=frozenset({ItemKind.CONSUMABLE}),
                required=True,
            ),
        )
        self.patrimonio = define_custom_field(
            self.uow(),
            CustomFieldDefinition(
                key="patrimonio",
                label="Patrimônio",
                field_type=CustomFieldType.TEXT,
                kinds=frozenset({ItemKind.ASSET}),
            ),
        )

    def uow(self) -> MemoryUnitOfWork:
        return MemoryUnitOfWork(self.state)

    def milk(self, **changes: object) -> Item:
        data: dict[str, object] = {
            "sku": "LEITE",
            "name": "Leite",
            "kind": ItemKind.CONSUMABLE,
            "base_unit": UN,
            "custom_fields": {"temperatura": Decimal(4)},
        }
        data |= changes
        return Item(**data)  # type: ignore[arg-type]


@pytest.fixture
def kitchen() -> Kitchen:
    return Kitchen()


def test_register_item_with_valid_fields(kitchen: Kitchen) -> None:
    item = register_item(kitchen.uow(), kitchen.milk())
    assert kitchen.state.items == {item.id: item}
    assert dict(item.custom_fields) == {"temperatura": Decimal(4)}


@pytest.mark.req("RF-001")
def test_register_item_checks_the_category_and_the_sku(kitchen: Kitchen) -> None:
    with pytest.raises(NotFoundError):
        register_item(kitchen.uow(), kitchen.milk(category_id=CategoryId(uuid4())))
    dairy = Category(name="Laticínios")
    with kitchen.uow() as uow:
        uow.categories.add(dairy)
        uow.commit()
    register_item(kitchen.uow(), kitchen.milk(category_id=dairy.id))
    with pytest.raises(ConflictError):
        register_item(kitchen.uow(), kitchen.milk(name="Outro leite"))


def test_missing_required_field_is_refused_with_the_field_named(kitchen: Kitchen) -> None:
    with pytest.raises(ValidationError, match="Temperatura de armazenamento") as error:
        register_item(kitchen.uow(), kitchen.milk(custom_fields={}))
    assert error.value.field == "custom_fields.temperatura"
    assert kitchen.state.items == {}


def test_wrong_type_is_refused_with_the_field_named(kitchen: Kitchen) -> None:
    with pytest.raises(ValidationError, match="precisa ser número") as error:
        register_item(kitchen.uow(), kitchen.milk(custom_fields={"temperatura": "frio"}))
    assert error.value.field == "custom_fields.temperatura"


def test_fields_follow_the_item_kind(kitchen: Kitchen) -> None:
    notebook = Item(
        sku="NOTE",
        name="Notebook",
        kind=ItemKind.ASSET,
        base_unit=UN,
        custom_fields={"patrimonio": " PAT-0042 "},
    )
    assert register_item(kitchen.uow(), notebook).custom_fields == {"patrimonio": "PAT-0042"}
    with pytest.raises(ValidationError, match="não se aplica"):
        register_item(
            kitchen.uow(), kitchen.milk(custom_fields={"temperatura": 4, "patrimonio": "X"})
        )


@pytest.mark.req("RF-001")
def test_update_revalidates_and_deactivation_keeps_fields(kitchen: Kitchen) -> None:
    item = register_item(kitchen.uow(), kitchen.milk())
    with pytest.raises(ValidationError):
        update_item(kitchen.uow(), replace(item, custom_fields={"temperatura": "frio"}))
    inactive = update_item(kitchen.uow(), item.deactivated())
    assert not kitchen.state.items[item.id].active
    assert inactive.custom_fields == {"temperatura": Decimal(4)}
    with pytest.raises(NotFoundError):
        update_item(kitchen.uow(), kitchen.milk(sku="NOVO"))


def test_new_required_field_is_charged_on_the_next_edit(kitchen: Kitchen) -> None:
    item = register_item(kitchen.uow(), kitchen.milk())
    define_custom_field(
        kitchen.uow(),
        CustomFieldDefinition(
            key="validade_aberto",
            label="Validade depois de aberto",
            field_type=CustomFieldType.DATE,
            kinds=frozenset({ItemKind.CONSUMABLE}),
            required=True,
        ),
    )
    assert kitchen.state.items[item.id] == item, "itens antigos não são mexidos"
    with pytest.raises(ValidationError, match="Validade depois de aberto"):
        update_item(kitchen.uow(), replace(item, name="Leite integral"))
    fields = {"temperatura": Decimal(4), "validade_aberto": date(2026, 11, 3)}
    update_item(kitchen.uow(), replace(item, custom_fields=fields))


def test_duplicate_field_key_is_refused(kitchen: Kitchen) -> None:
    with pytest.raises(ConflictError, match="temperatura"):
        define_custom_field(
            kitchen.uow(),
            CustomFieldDefinition(
                key="temperatura",
                label="Outra",
                field_type=CustomFieldType.TEXT,
                kinds=frozenset({ItemKind.ASSET}),
            ),
        )
