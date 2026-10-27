"""Coerência entre PROJECT_CONTEXT.md e docs/ (§0: discrepância é bug de processo).

Garante que todo ID citado (requisito, caso de portão, invariante, ADR) existe na sua fonte,
e que os ADRs seguem o template (TP-M0-06).
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CONTEXT = ROOT / "PROJECT_CONTEXT.md"
DOCS = ROOT / "docs"
REQUIREMENTS = DOCS / "requirements.md"
ADR_DIR = DOCS / "adr"
C4_DIR = DOCS / "c4"

REQ_ID = re.compile(r"\b(?:RF|RNF)-\d{3}\b")
GATE_ID = re.compile(r"\bTP-M\d+-\d{2}\b")
INV_ID = re.compile(r"\bINV-\d{2}\b")
ADR_ID = re.compile(r"\bADR-\d{3}\b")

ADR_SECTIONS = [
    "## Status",
    "## Contexto",
    "## Decisão",
    "## Consequências",
    "## Alternativas consideradas",
    "## Referências",
]
ADR_STATUSES = ("Proposto", "Aceito", "Substituído por ADR-", "Descartado")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def markdown_sources() -> list[Path]:
    extras = [
        ROOT / "README.md",
        ROOT / "CONTRIBUTING.md",
        ROOT / ".github" / "pull_request_template.md",
    ]
    return [CONTEXT, *extras, *sorted(DOCS.rglob("*.md"))]


def ids_defined_in_table(text: str, pattern: re.Pattern[str]) -> list[str]:
    """IDs que abrem uma linha de tabela (``| ID | ...``), onde cada ID é definido.

    Aceita sufixo na célula, como o ``★`` dos casos críticos.
    """
    found: list[str] = []
    for line in text.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        first_cell = line.strip().strip("|").split("|")[0].strip()
        match = pattern.match(first_cell)
        if match:
            found.append(match.group(0))
    return found


def requirement_rows() -> dict[str, list[str]]:
    """Linhas das tabelas de requisitos: ID → células."""
    rows: dict[str, list[str]] = {}
    for line in read(REQUIREMENTS).splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("|") and REQ_ID.fullmatch(cells[0]) and len(cells) == 6:
            rows[cells[0]] = cells
    return rows


def adr_files() -> list[Path]:
    return sorted(p for p in ADR_DIR.glob("[0-9][0-9][0-9]-*.md"))


def test_requirement_ids_are_unique() -> None:
    tables = read(REQUIREMENTS).split("## Lacunas conhecidas", 1)[0]
    ids = ids_defined_in_table(tables, REQ_ID)
    duplicated = sorted({i for i in ids if ids.count(i) > 1})
    assert not duplicated, f"IDs de requisito repetidos em requirements.md: {duplicated}"
    assert len(ids) == 34, "esperados 28 RF + 6 RNF; mudou? atualize este teste e o diário"


@pytest.mark.parametrize("source", markdown_sources(), ids=lambda p: p.relative_to(ROOT).as_posix())
def test_cited_requirements_exist(source: Path) -> None:
    defined = set(requirement_rows())
    cited = set(REQ_ID.findall(read(source)))
    assert cited <= defined, (
        f"requisitos citados que não existem em requirements.md: {sorted(cited - defined)}"
    )


@pytest.mark.parametrize("source", markdown_sources(), ids=lambda p: p.relative_to(ROOT).as_posix())
def test_cited_gate_cases_exist(source: Path) -> None:
    defined = set(ids_defined_in_table(read(CONTEXT), GATE_ID))
    cited = set(GATE_ID.findall(read(source)))
    assert cited <= defined, (
        f"casos de portão inexistentes no PROJECT_CONTEXT §10: {sorted(cited - defined)}"
    )


@pytest.mark.parametrize("source", markdown_sources(), ids=lambda p: p.relative_to(ROOT).as_posix())
def test_cited_invariants_exist(source: Path) -> None:
    defined = set(re.findall(r"^- (INV-\d{2}) ", read(CONTEXT), flags=re.MULTILINE))
    cited = set(INV_ID.findall(read(source)))
    assert cited <= defined, (
        f"invariantes inexistentes no PROJECT_CONTEXT §7.2: {sorted(cited - defined)}"
    )


def test_requirements_without_gate_case_are_listed_as_gaps() -> None:
    text = read(REQUIREMENTS)
    gaps_section = text.split("## Lacunas conhecidas", 1)[1]
    without_gate = {
        rid for rid, cells in requirement_rows().items() if not GATE_ID.search(cells[4])
    }
    listed = set(ids_defined_in_table(gaps_section, REQ_ID))
    assert without_gate == listed, (
        f"sem caso de portão e fora das lacunas: {sorted(without_gate - listed)}; "
        f"listados como lacuna mas já têm caso: {sorted(listed - without_gate)}"
    )


def test_there_are_adrs() -> None:
    assert len(adr_files()) >= 5


@pytest.mark.parametrize("adr", adr_files(), ids=lambda p: p.name)
def test_adr_follows_template(adr: Path) -> None:
    text = read(adr)
    number = adr.name[:3]
    assert text.startswith(f"# ADR-{number}: "), (
        "título deve ser '# ADR-NNN: ...' com o número do arquivo"
    )

    positions = [text.find(f"\n{section}\n") for section in ADR_SECTIONS]
    missing = [s for s, pos in zip(ADR_SECTIONS, positions, strict=True) if pos < 0]
    assert not missing, f"seções obrigatórias ausentes: {missing}"
    assert positions == sorted(positions), "seções fora da ordem do template"

    status = text.split("## Status\n", 1)[1].strip().splitlines()[0]
    assert status.startswith(ADR_STATUSES), f"status inválido: {status!r}"


def test_adr_index_lists_every_adr() -> None:
    index = read(ADR_DIR / "README.md")
    linked = set(re.findall(r"\]\((\d{3}-[^)]+\.md)\)", index))
    on_disk = {p.name for p in adr_files()}
    assert linked == on_disk, f"só no índice {linked - on_disk}, só no disco {on_disk - linked}"


@pytest.mark.parametrize("source", markdown_sources(), ids=lambda p: p.relative_to(ROOT).as_posix())
def test_cited_adrs_exist(source: Path) -> None:
    defined = {f"ADR-{p.name[:3]}" for p in adr_files()}
    cited = set(ADR_ID.findall(read(source)))
    assert cited <= defined, f"ADRs citados que não existem: {sorted(cited - defined)}"


def c4_files() -> list[Path]:
    return sorted(C4_DIR.glob("[0-9][0-9]-*.md"))


def test_c4_has_levels_1_and_2() -> None:
    assert [p.name[:2] for p in c4_files()] == ["01", "02"]


@pytest.mark.parametrize("diagram", c4_files(), ids=lambda p: p.name)
def test_c4_level_has_one_flowchart(diagram: Path) -> None:
    blocks = re.findall(r"```mermaid\n(.*?)```", read(diagram), flags=re.DOTALL)
    assert len(blocks) == 1, "cada nível do C4 tem exatamente um bloco mermaid"
    assert blocks[0].startswith("flowchart "), "notação adotada: flowchart (docs/c4/README.md)"


def test_c4_index_links_every_level() -> None:
    index = read(C4_DIR / "README.md")
    linked = set(re.findall(r"\]\((\d{2}-[^)]+\.md)\)", index))
    assert linked == {p.name for p in c4_files()}


def test_pr_template_carries_definition_of_done() -> None:
    template = read(ROOT / ".github" / "pull_request_template.md")
    for item in ["tools/check.py", "@pytest.mark.req", "§1", "§10", "§14", "Conventional Commits"]:
        assert item in template, f"checklist do PR sem: {item}"
