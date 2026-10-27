"""Matriz de rastreabilidade requisito × teste × status (M0.9).

Uso:
    python tools/traceability.py                    # imprime a matriz em Markdown
    python tools/traceability.py --output m.md      # grava em arquivo
    python tools/traceability.py --json             # saída em JSON

Roda a suíte do pytest, coleta os testes marcados com ``@pytest.mark.req("RF-xxx", ...)``
e cruza com ``docs/requirements.md``. Sai com código 1 se algum teste ligado a requisito
falhar ou se a suíte não rodar.
As funções de leitura e validação também são usadas por ``tests/conftest.py``.
"""

import argparse
import contextlib
import io
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
REQUIREMENTS = ROOT / "docs" / "requirements.md"
REQ_ID = re.compile(r"(?:RF|RNF)-\d{3}")

# Ordem de gravidade: o pior resultado de um teste prevalece.
OUTCOME_RANK = {"passed": 0, "skipped": 1, "failed": 2}


@dataclass(frozen=True)
class Requirement:
    id: str
    text: str
    milestone: str
    declared_status: str


@dataclass
class Row:
    requirement: Requirement
    tests: dict[str, str] = field(default_factory=dict)  # nodeid → resultado

    @property
    def result(self) -> str:
        outcomes = set(self.tests.values())
        if not outcomes:
            return "sem teste"
        if "failed" in outcomes:
            return "falhando"
        if outcomes == {"skipped"}:
            return "pulado"
        return "ok"

    @property
    def warning(self) -> str:
        if self.requirement.declared_status.startswith("Atendido") and self.result != "ok":
            return "declarado Atendido sem teste verde"
        return ""


def load_requirements(path: Path = REQUIREMENTS) -> dict[str, Requirement]:
    """Lê as tabelas de requisitos (linhas com 6 colunas cujo primeiro campo é um ID)."""
    found: dict[str, Requirement] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 6 and REQ_ID.fullmatch(cells[0]):
            req_id, text, milestone, _invariants, _gate, status = cells
            found[req_id] = Requirement(req_id, text, milestone, status)
    return found


def marker_problems(links: dict[str, list[str]], known: set[str]) -> list[str]:
    """Problemas nos markers ``req``: sem ID ou com ID que não existe em requirements.md."""
    problems: list[str] = []
    for nodeid, ids in links.items():
        if not ids:
            problems.append(f"{nodeid}: @pytest.mark.req sem ID de requisito")
        problems.extend(
            f"{nodeid}: requisito {rid!r} não existe em docs/requirements.md"
            for rid in ids
            if rid not in known
        )
    return problems


def req_ids(item: pytest.Item) -> list[str]:
    return [str(arg) for mark in item.iter_markers("req") for arg in mark.args]


def has_req_marker(item: pytest.Item) -> bool:
    return any(True for _ in item.iter_markers("req"))


def build_rows(
    requirements: dict[str, Requirement],
    links: dict[str, list[str]],
    outcomes: dict[str, str],
) -> list[Row]:
    rows = {rid: Row(req) for rid, req in requirements.items()}
    for nodeid, ids in links.items():
        for rid in ids:
            if rid in rows:
                rows[rid].tests[nodeid] = outcomes.get(nodeid, "não executado")
    return list(rows.values())


def render_markdown(rows: list[Row], generated_at: str, commit: str) -> str:
    covered = sum(1 for r in rows if r.tests)
    failing = sum(1 for r in rows if r.result == "falhando")
    linked = len({t for r in rows for t in r.tests})
    lines = [
        "# Matriz de rastreabilidade",
        "",
        f"> Gerada por `tools/traceability.py` em {generated_at} (commit `{commit}`). "
        "Não editar à mão.",
        "",
        f"**{covered} de {len(rows)}** requisitos com teste · **{linked}** testes ligados · "
        f"**{failing}** requisitos com teste falhando.",
        "",
        "| Requisito | Descrição | Milestone | Status declarado | Resultado | Testes |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows:
        req = r.requirement
        tests = "<br>".join(f"`{nodeid}` ({outcome})" for nodeid, outcome in r.tests.items())
        result = r.result + (f" ⚠ {r.warning}" if r.warning else "")
        lines.append(
            f"| {req.id} | {req.text} | {req.milestone} | {req.declared_status} | {result} | "
            f"{tests or '—'} |"
        )
    return "\n".join(lines) + "\n"


def render_json(rows: list[Row], generated_at: str, commit: str) -> str:
    data = {
        "generated_at": generated_at,
        "commit": commit,
        "requirements": [
            {
                "id": r.requirement.id,
                "milestone": r.requirement.milestone,
                "declared_status": r.requirement.declared_status,
                "result": r.result,
                "tests": r.tests,
            }
            for r in rows
        ],
    }
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


class Collector:
    """Plugin do pytest que guarda os testes ligados a requisitos e o resultado de cada um."""

    def __init__(self) -> None:
        self.links: dict[str, list[str]] = {}
        self.outcomes: dict[str, str] = {}

    def pytest_collection_modifyitems(self, items: list[pytest.Item]) -> None:
        for item in items:
            if has_req_marker(item):
                self.links[item.nodeid] = req_ids(item)

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        if report.nodeid not in self.links:
            return
        if report.when != "call" and report.passed:
            return  # setup/teardown sem problema não muda o resultado
        outcome = report.outcome
        current = self.outcomes.get(report.nodeid)
        if current is None or OUTCOME_RANK[outcome] > OUTCOME_RANK[current]:
            self.outcomes[report.nodeid] = outcome


def current_commit() -> str:
    git = shutil.which("git")
    if git is None:
        return "desconhecido"
    result = subprocess.run(
        [git, "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=False
    )
    return result.stdout.strip() or "desconhecido"


def write_stdout(text: str) -> None:
    """Imprime em UTF-8 mesmo quando o stdout do Windows está em cp1252 (saída redirecionada)."""
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.stdout.write(text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument(
        "--output", type=Path, help="grava a matriz neste arquivo em vez de imprimir"
    )
    parser.add_argument("--json", action="store_true", help="gera JSON em vez de Markdown")
    args = parser.parse_args(argv)

    collector = Collector()
    # A saída do pytest vai para stderr: stdout fica só com a matriz (senão o --json quebra).
    with contextlib.redirect_stdout(sys.stderr):
        exit_code = pytest.main(
            ["-q", "-p", "no:cacheprovider", "--rootdir", str(ROOT), str(ROOT / "tests")],
            plugins=[collector],
        )
    if exit_code not in (pytest.ExitCode.OK, pytest.ExitCode.TESTS_FAILED):
        print(f"a suíte não rodou (código {int(exit_code)}); matriz não gerada", file=sys.stderr)
        return 1

    rows = build_rows(load_requirements(), collector.links, collector.outcomes)
    generated_at = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    render = render_json if args.json else render_markdown
    text = render(rows, generated_at, current_commit())

    if args.output:
        args.output.write_text(text, encoding="utf-8", newline="\n")
        print(f"matriz gravada em {args.output}", file=sys.stderr)
    else:
        write_stdout(text)

    return 1 if any(r.result == "falhando" for r in rows) else 0


if __name__ == "__main__":
    raise SystemExit(main())
