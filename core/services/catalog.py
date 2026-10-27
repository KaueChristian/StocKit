"""Cadastro de itens e de campos personalizados (M1.11; RF-001, RF-004).

Regras que dependem de outros cadastros ficam aqui: a categoria precisa existir e os campos
personalizados do item são conferidos contra as definições do tipo dele (ADR-005). O ``Item`` em
si já valida o que só depende dele mesmo.
"""

from dataclasses import replace

from core.domain.catalog import Item
from core.domain.custom_fields import CustomFieldDefinition, validate_custom_fields
from core.ports.unit_of_work import UnitOfWork


def define_custom_field(
    uow: UnitOfWork, definition: CustomFieldDefinition
) -> CustomFieldDefinition:
    """Cadastra uma definição. Chave repetida: ``ConflictError``. Itens existentes não são
    revalidados agora: um campo obrigatório novo é cobrado na próxima edição de cada item."""
    with uow:
        uow.custom_fields.add(definition)
        uow.commit()
    return definition


def register_item(uow: UnitOfWork, item: Item) -> Item:
    """Cadastra um item novo (RF-001). SKU repetido: ``ConflictError``."""
    with uow:
        checked = _checked(uow, item)
        uow.items.add(checked)
        uow.commit()
    return checked


def update_item(uow: UnitOfWork, item: Item) -> Item:
    """Grava uma nova versão de um item existente (editar, inativar), com as mesmas regras."""
    with uow:
        uow.items.get(item.id)
        checked = _checked(uow, item)
        uow.items.update(checked)
        uow.commit()
    return checked


def _checked(uow: UnitOfWork, item: Item) -> Item:
    if item.category_id is not None:
        uow.categories.get(item.category_id)
    values = validate_custom_fields(uow.custom_fields.list(), item.kind, item.custom_fields)
    return replace(item, custom_fields=values)
