"""Sentinela dos contratos do import-linter (M0.10, caso de portão TP-M0-02).

Prova que os contratos reais do pyproject.toml **quebram** quando aparece um import proibido.
Sem este teste, um contrato mal escrito (nome de módulo errado, camada trocada) passaria em
silêncio para sempre.

Cada caso copia o ``core`` e o ``pyproject.toml`` para uma pasta temporária, planta um arquivo
com o import proibido e roda o import-linter num subprocesso apontado para a cópia.
O repositório nunca é alterado.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

LINT_IMPORTS = (
    "from importlinter.cli import lint_imports_command; lint_imports_command(['--no-cache'])"
)


@pytest.fixture
def sandbox(tmp_path: Path) -> Path:
    shutil.copytree(ROOT / "core", tmp_path / "core", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copy2(ROOT / "pyproject.toml", tmp_path / "pyproject.toml")
    return tmp_path


def run_linter(sandbox: Path) -> subprocess.CompletedProcess[str]:
    # PYTHONPATH na frente: a cópia temporária do core vence a instalação editável do repositório.
    env = os.environ | {"PYTHONPATH": str(sandbox), "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    return subprocess.run(
        [sys.executable, "-c", LINT_IMPORTS],
        cwd=sandbox,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=120,
    )


def test_clean_copy_keeps_every_contract(sandbox: Path) -> None:
    """Controle: sem violação, todos os contratos passam (garante que o sandbox funciona)."""
    result = run_linter(sandbox)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "0 broken" in result.stdout


@pytest.mark.parametrize(
    ("module", "source", "expected"),
    [
        ("core/domain/_sentinela.py", "import tkinter\n", "core is not allowed to import tkinter"),
        (
            "core/services/_sentinela.py",
            "from django.db import models\n",
            "core is not allowed to import django",
        ),
        ("core/ports/_sentinela.py", "import sqlite3\n", "core is not allowed to import sqlite3"),
        (
            "core/_sentinela.py",
            "from adapters.sqlite import repo\n",
            "core is not allowed to import adapters",
        ),
        (
            "core/domain/_sentinela.py",
            "import core.services\n",
            "core.domain is not allowed to import core.services",
        ),
        (
            "core/ports/_sentinela.py",
            "from core.services import algo\n",
            "core.ports is not allowed to import core.services",
        ),
    ],
    ids=["tkinter", "django", "sqlite3", "adapters", "domain->services", "ports->services"],
)
def test_forbidden_import_breaks_contract(
    sandbox: Path, module: str, source: str, expected: str
) -> None:
    (sandbox / module).write_text(source, encoding="utf-8")
    result = run_linter(sandbox)
    assert result.returncode == 1, result.stdout + result.stderr
    assert expected in result.stdout
    assert "1 broken" in result.stdout
