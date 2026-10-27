"""Testes do gerador da matriz de rastreabilidade (tools/traceability.py)."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from tools.traceability import (
    ROOT,
    Requirement,
    Row,
    build_rows,
    load_requirements,
    marker_problems,
    render_json,
    render_markdown,
)

REQ_A = Requirement("RF-001", "Cadastrar itens", "M1", "Planejado")
REQ_B = Requirement("RF-002", "Cadastrar locais", "M1", "Atendido")


def test_load_requirements_reads_all_rows_of_the_real_file() -> None:
    requirements = load_requirements()
    assert len(requirements) == 34
    assert requirements["RF-007"].milestone == "M1"
    assert requirements["RNF-006"].text.startswith("Nenhum segredo")


def test_load_requirements_ignores_gap_table(tmp_path: Path) -> None:
    doc = tmp_path / "req.md"
    doc.write_text(
        "| ID | Requisito | Milestone | Invariantes | Portão | Status |\n"
        "|---|---|---|---|---|---|\n"
        "| RF-001 | Cadastrar itens | M1 | — | TP-M3-02 | Planejado |\n"
        "\n## Lacunas conhecidas\n\n| ID | Primeiro milestone | Sugestão |\n"
        "| RF-001 | M1 | algo |\n",
        encoding="utf-8",
    )
    assert list(load_requirements(doc)) == ["RF-001"]


def test_marker_problems_flags_unknown_and_empty_ids() -> None:
    links = {"t.py::ok": ["RF-001"], "t.py::vazio": [], "t.py::errado": ["RF-999"]}
    problems = marker_problems(links, {"RF-001"})
    assert len(problems) == 2
    assert any("t.py::vazio" in p for p in problems)
    assert any("RF-999" in p for p in problems)


@pytest.mark.parametrize(
    ("outcomes", "expected"),
    [
        ({}, "sem teste"),
        ({"a": "passed"}, "ok"),
        ({"a": "passed", "b": "failed"}, "falhando"),
        ({"a": "skipped"}, "pulado"),
        ({"a": "passed", "b": "skipped"}, "ok"),
    ],
)
def test_row_result(outcomes: dict[str, str], expected: str) -> None:
    assert Row(REQ_A, dict(outcomes)).result == expected


def test_declared_atendido_without_green_test_is_flagged() -> None:
    assert Row(REQ_B).warning
    assert not Row(REQ_B, {"a": "passed"}).warning


def test_build_rows_links_tests_and_keeps_requirement_order() -> None:
    rows = build_rows(
        {"RF-001": REQ_A, "RF-002": REQ_B},
        links={"t.py::x": ["RF-002"], "t.py::y": ["RF-002", "RF-001"]},
        outcomes={"t.py::x": "passed", "t.py::y": "failed"},
    )
    assert [r.requirement.id for r in rows] == ["RF-001", "RF-002"]
    assert rows[0].tests == {"t.py::y": "failed"}
    assert rows[1].tests == {"t.py::x": "passed", "t.py::y": "failed"}


def test_render_markdown_has_summary_and_one_line_per_requirement() -> None:
    rows = build_rows(
        {"RF-001": REQ_A, "RF-002": REQ_B}, {"t.py::x": ["RF-001"]}, {"t.py::x": "passed"}
    )
    text = render_markdown(rows, "2026-10-27 12:00 UTC", "abc1234")
    assert "**1 de 2** requisitos com teste" in text
    assert "| RF-001 | Cadastrar itens | M1 | Planejado | ok | `t.py::x` (passed) |" in text
    assert "| RF-002 | Cadastrar locais | M1 | Atendido | sem teste ⚠" in text


def test_render_json_is_parseable() -> None:
    import json

    rows = build_rows({"RF-001": REQ_A}, {}, {})
    data = json.loads(render_json(rows, "agora", "abc1234"))
    assert data["requirements"][0] == {
        "id": "RF-001",
        "milestone": "M1",
        "declared_status": "Planejado",
        "result": "sem teste",
        "tests": {},
    }


def test_write_stdout_survives_a_cp1252_console() -> None:
    """Regressão do BUG-02: matriz com "≥" redirecionada para arquivo no Windows quebrava."""
    code = "from tools.traceability import write_stdout; write_stdout('cobertura ≥ 90%')"
    env = os.environ | {"PYTHONIOENCODING": "cp1252", "PYTHONUTF8": "0"}
    result = subprocess.run(
        [sys.executable, "-c", code], cwd=ROOT, env=env, capture_output=True, check=False
    )
    assert result.returncode == 0, result.stderr.decode(errors="replace")
    assert result.stdout.decode("utf-8").strip() == "cobertura ≥ 90%"
