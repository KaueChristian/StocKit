"""O pacote ``core`` está instalado, tem as subcamadas da arquitetura e se declara tipado."""

import importlib
from importlib.resources import files

import pytest


@pytest.mark.parametrize("module", ["core", "core.domain", "core.services", "core.ports"])
def test_core_layers_are_importable(module: str) -> None:
    assert importlib.import_module(module).__doc__


def test_core_ships_py_typed_marker() -> None:
    assert files("core").joinpath("py.typed").is_file()
