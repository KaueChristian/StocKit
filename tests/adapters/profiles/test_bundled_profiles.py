"""Perfis que acompanham o StocKit e o JSON Schema publicado (M1.12, RF-011; caso TP-M1-08).

A validação que vale é a do núcleo (``parse_profile``). O schema existe para quem escreve perfis
(editor com autocompletar); estes testes garantem que os dois aceitam e recusam as mesmas coisas.
"""

import json
from pathlib import Path
from typing import Any

import jsonschema
import pytest

from adapters.profiles import (
    BUNDLED,
    load_bundled_profiles,
    load_profile_file,
    parse_profile_text,
    schema_text,
)
from core.domain.errors import ProfileError
from tests.core.domain.test_profile_and_settings import INVALID, SEMANTIC_ONLY, VALID

pytestmark = pytest.mark.req("RF-011")

DATA = Path(__file__).resolve().parents[3] / "adapters" / "profiles" / "data"
SCHEMA = json.loads(schema_text())
VALIDATOR = jsonschema.Draft202012Validator(SCHEMA)


def test_the_four_bundled_profiles_load() -> None:
    profiles = load_bundled_profiles()
    assert set(profiles) == set(BUNDLED) == {"varejo", "cozinha", "oficina", "ti"}
    for profile in profiles.values():
        assert profile.name
        assert profile.custom_fields, f"{profile.key} sem campos"
        assert profile.categories, f"{profile.key} sem categorias"


def test_bundled_profiles_are_what_the_folder_has() -> None:
    assert sorted(p.stem for p in DATA.glob("*.json")) == sorted(BUNDLED)


def test_schema_is_a_valid_json_schema() -> None:
    jsonschema.Draft202012Validator.check_schema(SCHEMA)


@pytest.mark.parametrize("key", BUNDLED)
def test_bundled_profile_matches_the_published_schema(key: str) -> None:
    VALIDATOR.validate(json.loads((DATA / f"{key}.json").read_text(encoding="utf-8")))


def test_valid_sample_matches_the_schema() -> None:
    VALIDATOR.validate(VALID)


@pytest.mark.parametrize(("case", "data", "path"), INVALID, ids=[c for c, _, _ in INVALID])
def test_schema_refuses_what_the_core_refuses(case: str, data: Any, path: str) -> None:
    assert not VALIDATOR.is_valid(data), f"o schema aceitou o caso {case!r}, que o núcleo recusa"


def test_malformed_json_names_line_and_column() -> None:
    with pytest.raises(ProfileError, match="linha 1, coluna") as error:
        parse_profile_text('{"schema_version": 1,')
    assert error.value.path == "$"


def test_profile_file_is_read_as_utf8(tmp_path: Path) -> None:
    file = tmp_path / "padaria.json"
    file.write_text(json.dumps(VALID, ensure_ascii=False), encoding="utf-8")
    assert load_profile_file(file).categories == ("Pães", "Doces")


@pytest.mark.parametrize(
    ("case", "data", "path"), SEMANTIC_ONLY, ids=[c for c, _, _ in SEMANTIC_ONLY]
)
def test_rules_of_meaning_are_only_in_the_core(case: str, data: Any, path: str) -> None:
    """Documenta o limite do schema: se um dia ele passar a recusar, mova o caso para INVALID."""
    assert VALIDATOR.is_valid(data)
