"""Perfis de negócio: arquivos JSON que acompanham o StocKit e leitura deles (M1.12).

Este adaptador só lê arquivos; quem valida e monta o ``Profile`` é ``core.domain.profile``. Número
JSON com casas decimais vira ``float`` na leitura e é recusado pelo núcleo com o caminho do campo
(o perfil usa texto decimal, ADR-005).
"""

import json
from importlib.resources import files
from pathlib import Path

from core.domain.errors import ProfileError
from core.domain.profile import Profile, parse_profile

BUNDLED = ("varejo", "cozinha", "oficina", "ti")


def parse_profile_text(text: str) -> Profile:
    """Perfil a partir do texto JSON. JSON malformado vira ``ProfileError`` com linha e coluna."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as error:
        raise ProfileError(
            "$", f"JSON inválido na linha {error.lineno}, coluna {error.colno}"
        ) from None
    return parse_profile(data)


def load_profile_file(path: Path) -> Profile:
    return parse_profile_text(path.read_text(encoding="utf-8"))


def load_bundled_profiles() -> dict[str, Profile]:
    """Os perfis que vêm com o StocKit, pela chave."""
    folder = files("adapters.profiles").joinpath("data")
    profiles = [
        parse_profile_text(folder.joinpath(f"{k}.json").read_text("utf-8")) for k in BUNDLED
    ]
    return {profile.key: profile for profile in profiles}


def schema_text() -> str:
    """O JSON Schema publicado do formato de perfil."""
    return files("adapters.profiles").joinpath("profile.schema.json").read_text("utf-8")
