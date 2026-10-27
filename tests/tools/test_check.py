"""Testes do comando único de verificação (tools/check.py).

Regressão do CI no Windows (portão M0): o check procurava ``lint-imports`` ao lado do
python.exe, o que só vale dentro de um venv.
"""

import sys
from pathlib import Path

import pytest

from tools import check


def test_every_script_step_points_to_an_installed_executable() -> None:
    commands = [command for _, command in check.STEPS if command[0] != sys.executable]
    assert commands, "nenhuma etapa usa executável próprio"
    for command in commands:
        path = Path(command[0])
        # No Windows o executável tem .exe; o CreateProcess completa a extensão sozinho.
        assert path.exists() or path.with_suffix(".exe").exists(), f"não encontrado: {path}"


def test_missing_tool_is_reported_as_failure_not_crash(
    capsys: pytest.CaptureFixture[str],
) -> None:
    ok, _ = check.run_step("fantasma", [str(Path("nao-existe") / "ferramenta-fantasma")])
    assert not ok
    assert "ferramenta não encontrada" in capsys.readouterr().out
