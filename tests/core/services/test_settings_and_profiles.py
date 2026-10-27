"""Configuração do sistema e aplicação de perfis nos serviços (M1.12; RF-007, RF-011)."""

from dataclasses import replace
from decimal import Decimal

import pytest

from adapters.clock import FixedClock
from adapters.memory.repositories import MemoryState
from adapters.memory.unit_of_work import MemoryUnitOfWork
from adapters.profiles import load_bundled_profiles
from core.domain.catalog import Category, Item, ItemKind
from core.domain.custom_fields import CustomFieldDefinition, CustomFieldType
from core.domain.errors import InsufficientStockError, ValidationError
from core.domain.location import Location
from core.domain.movement import MovementKind
from core.domain.policy import NegativeStockPolicy
from core.domain.quantity import STANDARD_UNITS, Quantity
from core.services.catalog import define_custom_field, register_item
from core.services.movements import RecordMovement, record_movement
from core.services.settings import apply_profile, current_settings, set_negative_stock_policy

PROFILES = load_bundled_profiles()
UN = STANDARD_UNITS["un"]


def uow_on(state: MemoryState) -> MemoryUnitOfWork:
    return MemoryUnitOfWork(state)


# --- política vinda da configuração ------------------------------------------------------


@pytest.mark.req("RF-007")
def test_movements_follow_the_policy_in_the_settings() -> None:
    from datetime import UTC, datetime

    state = MemoryState()
    item = Item(sku="PAR", name="Parafuso", kind=ItemKind.RESALE, base_unit=UN)
    shop = Location(name="Loja")
    with uow_on(state) as uow:
        uow.items.add(item)
        uow.locations.add(shop)
        uow.commit()
    clock = FixedClock(datetime(2026, 10, 27, tzinfo=UTC))
    issue = RecordMovement(
        kind=MovementKind.ISSUE,
        item_id=item.id,
        location_id=shop.id,
        quantity=Quantity(Decimal(2), UN),
        author="Ana",
    )
    with pytest.raises(InsufficientStockError):
        record_movement(uow_on(state), clock, issue)
    set_negative_stock_policy(uow_on(state), NegativeStockPolicy.ALLOW)
    assert current_settings(uow_on(state)).negative_stock_policy is NegativeStockPolicy.ALLOW
    record_movement(uow_on(state), clock, issue)
    with pytest.raises(InsufficientStockError):
        record_movement(uow_on(state), clock, issue, policy=NegativeStockPolicy.FORBID)
    assert len(state.movements) == 1


# --- aplicar perfil (TP-M1-08) -----------------------------------------------------------


@pytest.mark.req("RF-011")
@pytest.mark.parametrize("key", sorted(PROFILES))
def test_each_bundled_profile_applies_on_an_empty_stock(key: str) -> None:
    state = MemoryState()
    profile = PROFILES[key]
    report = apply_profile(uow_on(state), profile)
    settings = current_settings(uow_on(state))
    assert settings.profile_key == key
    assert settings.labels == profile.labels
    assert settings.units == profile.units
    assert report.created_categories == profile.categories
    assert report.created_fields == tuple(f.key for f in profile.custom_fields)
    assert (report.kept_categories, report.kept_fields) == ((), ())
    assert sorted(c.name for c in state.categories.values()) == sorted(profile.categories)


@pytest.mark.req("RF-011")
def test_applying_again_keeps_what_exists() -> None:
    state = MemoryState()
    apply_profile(uow_on(state), PROFILES["cozinha"])
    report = apply_profile(uow_on(state), PROFILES["cozinha"])
    assert report.created_categories == report.created_fields == ()
    assert len(state.categories) == len(PROFILES["cozinha"].categories)


@pytest.mark.req("RF-011")
def test_existing_user_choices_are_not_overwritten() -> None:
    state = MemoryState()
    with uow_on(state) as uow:
        uow.categories.add(Category(name="laticínios"))
        uow.commit()
    mine = CustomFieldDefinition(
        key="temperatura",
        label="Minha temperatura",
        field_type=CustomFieldType.TEXT,
        kinds=frozenset({ItemKind.CONSUMABLE}),
    )
    define_custom_field(uow_on(state), mine)
    report = apply_profile(uow_on(state), PROFILES["cozinha"])
    assert "Laticínios" in report.kept_categories
    assert "temperatura" in report.kept_fields
    assert next(iter(d for d in state.custom_fields.values() if d.key == "temperatura")) is mine


@pytest.mark.req("RF-011")
def test_second_profile_replaces_vocabulary_and_units_but_keeps_registries() -> None:
    state = MemoryState()
    apply_profile(uow_on(state), PROFILES["cozinha"])
    apply_profile(uow_on(state), PROFILES["ti"])
    settings = current_settings(uow_on(state))
    assert (settings.profile_key, settings.label("item", "Item")) == ("ti", "Equipamento")
    assert settings.units == ()
    keys = {d.key for d in state.custom_fields.values()}
    assert {"temperatura", "patrimonio"} <= keys


@pytest.mark.req("RF-011")
def test_profile_without_policy_keeps_the_current_one() -> None:
    state = MemoryState()
    set_negative_stock_policy(uow_on(state), NegativeStockPolicy.ALLOW)
    apply_profile(uow_on(state), replace(PROFILES["ti"], negative_stock_policy=None))
    assert current_settings(uow_on(state)).negative_stock_policy is NegativeStockPolicy.ALLOW
    apply_profile(uow_on(state), PROFILES["ti"])
    assert current_settings(uow_on(state)).negative_stock_policy is NegativeStockPolicy.FORBID


@pytest.mark.req("RF-004")
def test_profile_fields_are_enforced_on_items() -> None:
    state = MemoryState()
    apply_profile(uow_on(state), PROFILES["cozinha"])
    milk = Item(sku="LEITE", name="Leite", kind=ItemKind.CONSUMABLE, base_unit=UN)
    with pytest.raises(ValidationError, match="Temperatura de armazenamento") as error:
        register_item(uow_on(state), milk)
    assert error.value.field == "custom_fields.temperatura"
    register_item(uow_on(state), replace(milk, custom_fields={"temperatura": Decimal(4)}))
