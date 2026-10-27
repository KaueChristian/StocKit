"""Configuração do sistema e aplicação de perfis (M1.12; RF-007, RF-011)."""

from dataclasses import dataclass, replace

from core.domain.catalog import Category
from core.domain.policy import NegativeStockPolicy
from core.domain.profile import Profile
from core.domain.settings import SystemSettings
from core.ports.unit_of_work import UnitOfWork


def current_settings(uow: UnitOfWork) -> SystemSettings:
    with uow:
        return uow.settings.get()


def set_negative_stock_policy(uow: UnitOfWork, policy: NegativeStockPolicy) -> SystemSettings:
    """Troca a política de saldo negativo (INV-05). Vale para os próximos lançamentos."""
    with uow:
        settings = replace(uow.settings.get(), negative_stock_policy=policy)
        uow.settings.save(settings)
        uow.commit()
    return settings


@dataclass(frozen=True, slots=True)
class ProfileReport:
    """O que ``apply_profile`` fez: o que criou e o que já existia e foi mantido."""

    profile_key: str
    created_categories: tuple[str, ...]
    kept_categories: tuple[str, ...]
    created_fields: tuple[str, ...]
    kept_fields: tuple[str, ...]


def apply_profile(uow: UnitOfWork, profile: Profile) -> ProfileReport:
    """Aplica um perfil: vocabulário, unidades e política vão para a configuração (substituindo os
    do perfil anterior); categorias e campos personalizados são **acrescentados** — o que já existe
    com o mesmo nome/chave é mantido como está, sem sobrescrever o que o usuário ajustou."""
    with uow:
        settings = uow.settings.get()
        uow.settings.save(
            replace(
                settings,
                profile_key=profile.key,
                labels=profile.labels,
                units=profile.units,
                negative_stock_policy=profile.negative_stock_policy
                or settings.negative_stock_policy,
            )
        )
        existing = {c.name.casefold() for c in uow.categories.list()}
        created_categories, kept_categories = [], []
        for name in profile.categories:
            if name.casefold() in existing:
                kept_categories.append(name)
            else:
                uow.categories.add(Category(name=name))
                existing.add(name.casefold())
                created_categories.append(name)
        created_fields, kept_fields = [], []
        for definition in profile.custom_fields:
            if uow.custom_fields.find_by_key(definition.key) is None:
                uow.custom_fields.add(definition)
                created_fields.append(definition.key)
            else:
                kept_fields.append(definition.key)
        uow.commit()
    return ProfileReport(
        profile.key,
        tuple(created_categories),
        tuple(kept_categories),
        tuple(created_fields),
        tuple(kept_fields),
    )
