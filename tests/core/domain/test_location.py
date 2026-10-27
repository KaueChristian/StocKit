"""Locais e hierarquia (M1.2, RF-002, caso de portão TP-M1-12)."""

import itertools
from uuid import uuid4

import pytest
from hypothesis import given
from hypothesis import strategies as st

from core.domain.errors import HierarchyError, ValidationError
from core.domain.ids import LocationId
from core.domain.location import Location, LocationTree

pytestmark = pytest.mark.req("RF-002")


def warehouse() -> tuple[LocationTree, Location, Location, Location]:
    deposito = Location(name="Depósito")
    corredor = Location(name="Corredor A", parent_id=deposito.id)
    prateleira = Location(name="Prateleira 3", parent_id=corredor.id)
    return LocationTree([prateleira, deposito, corredor]), deposito, corredor, prateleira


# --- local -------------------------------------------------------------------------------


def test_location_name_is_cleaned() -> None:
    assert Location(name="  Corredor   A ").name == "Corredor A"


@pytest.mark.parametrize("name", ["", "  ", "x" * 81])
def test_invalid_location_name_is_refused(name: str) -> None:
    with pytest.raises(ValidationError):
        Location(name=name)


def test_location_cannot_be_its_own_parent() -> None:
    own = LocationId(uuid4())
    with pytest.raises(ValidationError, match="si mesmo") as error:
        Location(name="Caixa", id=own, parent_id=own)
    assert error.value.field == "parent_id"


@pytest.mark.parametrize(
    ("changes", "field"),
    [({"parent_id": "raiz"}, "parent_id"), ({"active": 0}, "active"), ({"id": 1}, "id")],
)
def test_location_wrong_types_are_refused(changes: dict[str, object], field: str) -> None:
    with pytest.raises(ValidationError) as error:
        Location(name="Caixa", **changes)  # type: ignore[arg-type]
    assert error.value.field == field


def test_location_deactivated_keeps_identity() -> None:
    location = Location(name="Caixa")
    assert location.deactivated() == location
    assert not location.deactivated().active


# --- árvore (TP-M1-12) -------------------------------------------------------------------


def test_three_levels_give_the_full_path() -> None:
    tree, deposito, corredor, prateleira = warehouse()
    assert tree.path(prateleira.id) == (deposito, corredor, prateleira)
    assert tree.full_name(prateleira.id) == "Depósito › Corredor A › Prateleira 3"
    assert tree.full_name(deposito.id) == "Depósito"
    assert tree.roots() == (deposito,)
    assert tree.children(deposito.id) == (corredor,)
    assert tree.descendants(deposito.id) == (corredor, prateleira)
    assert tree.descendants(prateleira.id) == ()
    assert len(tree) == 3
    assert set(tree) == {deposito, corredor, prateleira}
    assert corredor.id in tree


def test_moving_a_location_inside_its_descendant_is_refused() -> None:
    tree, deposito, _, prateleira = warehouse()
    with pytest.raises(HierarchyError, match="ciclo"):
        tree.with_location(deposito.moved_to(prateleira.id))


def test_two_locations_pointing_at_each_other_is_a_cycle() -> None:
    a_id, b_id = LocationId(uuid4()), LocationId(uuid4())
    with pytest.raises(HierarchyError, match=r"ciclo.*'A'.*'B'"):
        LocationTree(
            [
                Location(name="A", id=a_id, parent_id=b_id),
                Location(name="B", id=b_id, parent_id=a_id),
            ]
        )


def test_moving_to_another_branch_is_accepted() -> None:
    tree, deposito, corredor, prateleira = warehouse()
    corredor_b = Location(name="Corredor B", parent_id=deposito.id)
    tree = tree.with_location(corredor_b).with_location(prateleira.moved_to(corredor_b.id))
    assert tree.full_name(prateleira.id) == "Depósito › Corredor B › Prateleira 3"
    assert tree.children(corredor.id) == ()


@pytest.mark.parametrize("name", ["Corredor A", "corredor a", "  CORREDOR   A "])
def test_sibling_names_must_be_unique_ignoring_case(name: str) -> None:
    tree, deposito, _, _ = warehouse()
    with pytest.raises(HierarchyError, match=r"já existe.*Depósito"):
        tree.with_location(Location(name=name, parent_id=deposito.id))


def test_same_name_under_different_parents_is_fine() -> None:
    tree, deposito, _, _ = warehouse()
    other = Location(name="Corredor B", parent_id=deposito.id)
    tree = tree.with_location(other).with_location(
        Location(name="Prateleira 3", parent_id=other.id)
    )
    assert len(tree) == 5


def test_duplicate_root_names_are_refused() -> None:
    with pytest.raises(HierarchyError, match="na raiz"):
        LocationTree([Location(name="Loja"), Location(name="loja")])


def test_missing_parent_is_refused() -> None:
    with pytest.raises(HierarchyError, match="pai que não existe"):
        LocationTree([Location(name="Órfão", parent_id=LocationId(uuid4()))])


def test_repeated_location_is_refused() -> None:
    location = Location(name="Loja")
    with pytest.raises(HierarchyError, match="repetido"):
        LocationTree([location, location])


def test_unknown_location_is_reported() -> None:
    tree, *_ = warehouse()
    with pytest.raises(HierarchyError, match="não encontrado"):
        tree.full_name(LocationId(uuid4()))


def test_replacing_a_location_keeps_its_children() -> None:
    tree, _, corredor, prateleira = warehouse()
    renamed = tree.with_location(
        Location(name="Corredor 1", id=corredor.id, parent_id=corredor.parent_id)
    )
    assert renamed.full_name(prateleira.id) == "Depósito › Corredor 1 › Prateleira 3"
    assert tree.full_name(prateleira.id) == "Depósito › Corredor A › Prateleira 3", (
        "árvore original intacta"
    )


# --- propriedades ------------------------------------------------------------------------


@st.composite
def forests(draw: st.DrawFn) -> list[Location]:
    """Floresta aleatória: cada local tem como pai algum local criado antes dele (ou nenhum)."""
    size = draw(st.integers(min_value=1, max_value=25))
    locations: list[Location] = []
    for index in range(size):
        parent = draw(st.none() | st.sampled_from(locations)) if locations else None
        locations.append(Location(name=f"L{index}", parent_id=parent.id if parent else None))
    return draw(st.permutations(locations))


@given(forests())
def test_every_path_starts_at_a_root_and_follows_parents(locations: list[Location]) -> None:
    tree = LocationTree(locations)
    for location in locations:
        path = tree.path(location.id)
        assert path[0].parent_id is None
        assert path[-1] == location
        assert all(child.parent_id == parent.id for parent, child in itertools.pairwise(path))


@given(forests())
def test_descendants_are_exactly_the_locations_with_this_one_in_their_path(
    locations: list[Location],
) -> None:
    tree = LocationTree(locations)
    for location in locations:
        expected = {
            other for other in locations if other != location and location in tree.path(other.id)
        }
        assert set(tree.descendants(location.id)) == expected


@given(forests(), st.data())
def test_moving_under_itself_or_a_descendant_is_always_refused(
    locations: list[Location], data: st.DataObject
) -> None:
    tree = LocationTree(locations)
    location = data.draw(st.sampled_from(locations))
    candidates = [*tree.descendants(location.id)]
    if not candidates:
        return
    target = data.draw(st.sampled_from(candidates))
    with pytest.raises(HierarchyError, match="ciclo"):
        tree.with_location(location.moved_to(target.id))
