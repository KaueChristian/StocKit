"""Partes (M1.2, RF-003, caso de portão TP-M1-13)."""

import pytest

from core.domain.errors import ValidationError
from core.domain.party import Party, PartyRole

pytestmark = pytest.mark.req("RF-003")


@pytest.mark.parametrize("role", list(PartyRole))
def test_party_with_each_role(role: PartyRole) -> None:
    party = Party(name="Distribuidora Exemplo", roles=frozenset({role}))
    assert party.has_role(role)
    assert party.roles == {role}


def test_party_with_several_roles() -> None:
    party = Party(name="Loja Parceira", roles=frozenset({PartyRole.SUPPLIER, PartyRole.CUSTOMER}))
    assert party.has_role(PartyRole.SUPPLIER)
    assert party.has_role(PartyRole.CUSTOMER)
    assert not party.has_role(PartyRole.DEPARTMENT)


def test_roles_given_as_another_collection_become_a_frozenset() -> None:
    party = Party(name="Setor de Manutenção", roles=[PartyRole.DEPARTMENT, PartyRole.DEPARTMENT])  # type: ignore[arg-type]
    assert party.roles == frozenset({PartyRole.DEPARTMENT})


@pytest.mark.parametrize(
    ("roles", "message"),
    [
        (frozenset(), "pelo menos um papel"),
        (frozenset({"supplier"}), "papel inválido"),
        (frozenset({PartyRole.CUSTOMER, "vendedor"}), "papel inválido"),
        ("supplier", "coleção"),
        (None, "coleção"),
    ],
    ids=["vazio", "texto-no-lugar-do-papel", "um-invalido", "string", "nada"],
)
def test_invalid_roles_are_refused(roles: object, message: str) -> None:
    with pytest.raises(ValidationError, match=message) as error:
        Party(name="Fornecedor X", roles=roles)  # type: ignore[arg-type]
    assert error.value.field == "roles"


@pytest.mark.parametrize("name", ["", "   ", "x" * 121])
def test_invalid_name_is_refused(name: str) -> None:
    with pytest.raises(ValidationError) as error:
        Party(name=name, roles=frozenset({PartyRole.SUPPLIER}))
    assert error.value.field == "name"


def test_wrong_types_are_refused() -> None:
    with pytest.raises(ValidationError):
        Party(name="X", roles=frozenset({PartyRole.SUPPLIER}), active=None)  # type: ignore[arg-type]
    with pytest.raises(ValidationError):
        Party(name="X", roles=frozenset({PartyRole.SUPPLIER}), id="1")  # type: ignore[arg-type]


def test_deactivated_party_keeps_identity() -> None:
    party = Party(name="Cliente Exemplo", roles=frozenset({PartyRole.CUSTOMER}))
    inactive = party.deactivated()
    assert inactive == party
    assert not inactive.active
