"""Itens e categorias (M1.2, RF-001)."""

from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
from uuid import uuid4

import pytest

from core.domain.catalog import SKU_MAX_LENGTH, Category, Item, ItemKind
from core.domain.errors import DomainError, ValidationError
from core.domain.ids import CategoryId, ItemId
from core.domain.quantity import STANDARD_UNITS, Dimension, UnitOfMeasure

UN = STANDARD_UNITS["un"]
KG = STANDARD_UNITS["kg"]
DZ = STANDARD_UNITS["dz"]


def make_item(**changes: object) -> Item:
    data: dict[str, object] = {
        "sku": "PAR-001",
        "name": "Parafuso sextavado M6",
        "kind": ItemKind.RESALE,
        "base_unit": UN,
    }
    data |= changes
    return Item(**data)  # type: ignore[arg-type]


pytestmark = pytest.mark.req("RF-001")


def test_item_with_defaults() -> None:
    item = make_item()
    assert item.active
    assert not item.tracks_lots
    assert not item.tracks_expiry
    assert item.category_id is None
    assert isinstance(item.id, type(uuid4()))


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("par-001", "PAR-001"), ("  7891234567890 ", "7891234567890"), ("a.b_c/d-e", "A.B_C/D-E")],
)
def test_sku_is_trimmed_and_uppercased(raw: str, expected: str) -> None:
    assert make_item(sku=raw).sku == expected


@pytest.mark.parametrize(
    "sku",
    ["", "   ", "PAR 001", "-PAR", "PAR#1", "ÇÃO", "X" * (SKU_MAX_LENGTH + 1), 123],
    ids=[
        "vazio",
        "espacos",
        "espaco-interno",
        "comeca-com-hifen",
        "cerquilha",
        "acento",
        "longo",
        "numero",
    ],
)
def test_invalid_sku_is_refused(sku: object) -> None:
    with pytest.raises(ValidationError) as error:
        make_item(sku=sku)
    assert error.value.field == "sku"
    assert "SKU" in str(error.value)


def test_sku_at_the_maximum_length_is_accepted() -> None:
    assert len(make_item(sku="X" * SKU_MAX_LENGTH).sku) == SKU_MAX_LENGTH


def test_name_is_trimmed_and_inner_spaces_collapsed() -> None:
    assert make_item(name="  Parafuso   sextavado ").name == "Parafuso sextavado"


@pytest.mark.parametrize("name", ["", "   ", "x" * 201, None])
def test_invalid_name_is_refused(name: object) -> None:
    with pytest.raises(ValidationError) as error:
        make_item(name=name)
    assert error.value.field == "name"


@pytest.mark.parametrize(
    ("changes", "field"),
    [
        ({"kind": "resale"}, "kind"),
        ({"base_unit": "un"}, "base_unit"),
        ({"category_id": "eletrica"}, "category_id"),
        ({"tracks_lots": 1}, "tracks_lots"),
        ({"active": "sim"}, "active"),
        ({"id": "abc"}, "id"),
    ],
)
def test_wrong_types_are_refused(changes: dict[str, object], field: str) -> None:
    with pytest.raises(ValidationError) as error:
        make_item(**changes)
    assert error.value.field == field


def test_expiry_requires_lot_control() -> None:
    with pytest.raises(ValidationError, match="lote") as error:
        make_item(tracks_expiry=True)
    assert error.value.field == "tracks_expiry"
    assert make_item(tracks_lots=True, tracks_expiry=True).tracks_expiry


@pytest.mark.parametrize(
    "unit",
    [KG, DZ, UnitOfMeasure("cx12", "caixa com 12", Dimension.COUNT, Decimal(12))],
    ids=["kg", "duzia", "caixa"],
)
def test_serialized_item_needs_a_single_count_unit(unit: UnitOfMeasure) -> None:
    with pytest.raises(ValidationError, match="serializado") as error:
        make_item(kind=ItemKind.SERIALIZED, base_unit=unit)
    assert error.value.field == "base_unit"


def test_serialized_item_with_unit_is_accepted() -> None:
    assert make_item(kind=ItemKind.SERIALIZED, base_unit=UN).kind is ItemKind.SERIALIZED


def test_items_are_immutable() -> None:
    item = make_item()
    with pytest.raises(FrozenInstanceError):
        item.name = "outro"  # type: ignore[misc]


def test_editing_keeps_identity_and_revalidates() -> None:
    item = make_item()
    edited = replace(item, name="Parafuso M6 zincado", sku="par-001z")
    assert edited == item, "mesma entidade (mesmo id), outra versão"
    assert edited.sku == "PAR-001Z"
    with pytest.raises(ValidationError):
        replace(item, sku="com espaço")


def test_deactivate_and_activate() -> None:
    item = make_item()
    inactive = item.deactivated()
    assert not inactive.active
    assert inactive == item
    assert inactive.activated().active


def test_identity_is_by_id_and_type() -> None:
    shared = uuid4()
    item = make_item(id=ItemId(shared))
    category = Category(name="Fixação", id=CategoryId(shared))
    assert make_item(id=ItemId(shared), name="Outro nome") == item
    assert make_item() != item
    assert item != category, "mesmo UUID em tipos diferentes não é a mesma entidade"
    assert item != "PAR-001"
    assert len({item, make_item(id=ItemId(shared)), make_item()}) == 2


def test_item_accepts_a_category() -> None:
    category = Category(name="  Fixação  ")
    assert category.name == "Fixação"
    assert make_item(category_id=category.id).category_id == category.id


@pytest.mark.parametrize("name", ["", "x" * 81])
def test_invalid_category_name_is_refused(name: str) -> None:
    with pytest.raises(ValidationError):
        Category(name=name)


def test_category_rejects_invalid_id() -> None:
    with pytest.raises(ValidationError):
        Category(name="Fixação", id="x")  # type: ignore[arg-type]


def test_validation_errors_are_domain_errors() -> None:
    assert issubclass(ValidationError, DomainError)


def test_serialized_item_cannot_track_lots() -> None:
    with pytest.raises(ValidationError, match="número de série") as error:
        make_item(kind=ItemKind.SERIALIZED, tracks_lots=True)
    assert error.value.field == "tracks_lots"
