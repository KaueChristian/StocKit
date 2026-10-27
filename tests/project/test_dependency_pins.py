"""RNF-006: dependências com versão fixa e sem segredos versionados.

Também impede que as versões repetidas em .pre-commit-config.yaml e no workflow de CI se
afastem das do pyproject.toml (custo registrado na M0.3, PROJECT_CONTEXT.md §19).
"""

import re
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PYPROJECT = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
PRE_COMMIT = (ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8")
WORKFLOWS = sorted((ROOT / ".github" / "workflows").glob("*.yml"))

EXACT_PIN = re.compile(
    r"^(?P<name>[A-Za-z0-9][A-Za-z0-9._-]*)(\[[^\]]+\])?==(?P<version>\d[^\s,;]*)$"
)


def normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def declared_requirements() -> list[str]:
    reqs = list(PYPROJECT["build-system"]["requires"])
    reqs += PYPROJECT["project"].get("dependencies", [])
    for extra in PYPROJECT["project"].get("optional-dependencies", {}).values():
        reqs += extra
    for group in PYPROJECT.get("dependency-groups", {}).values():
        reqs += [r for r in group if isinstance(r, str)]
    return reqs


def dev_pins() -> dict[str, str]:
    pins: dict[str, str] = {}
    for req in PYPROJECT["dependency-groups"]["dev"]:
        match = EXACT_PIN.match(req)
        assert match, req
        pins[normalize(match["name"])] = match["version"]
    return pins


@pytest.mark.req("RNF-006")
@pytest.mark.parametrize("requirement", declared_requirements())
def test_every_declared_dependency_has_exact_version(requirement: str) -> None:
    assert EXACT_PIN.match(requirement), f"versão não fixada com '==': {requirement}"


@pytest.mark.req("RNF-006")
def test_pre_commit_versions_match_dev_group() -> None:
    pins = dev_pins()
    found = re.findall(r"additional_dependencies: \[([^\]]*)\]", PRE_COMMIT)
    assert found, "nenhum additional_dependencies encontrado"
    for dep in (d.strip() for line in found for d in line.split(",")):
        match = EXACT_PIN.match(dep)
        assert match, f"dependência de gancho sem versão fixa: {dep}"
        assert pins.get(normalize(match["name"])) == match["version"], (
            f"{dep} diverge do [dependency-groups] dev ({pins.get(normalize(match['name']))})"
        )

    ruff_rev = re.search(r"ruff-pre-commit\n\s+rev: v(\S+)", PRE_COMMIT)
    assert ruff_rev, "gancho do ruff não encontrado"
    assert ruff_rev[1] == pins["ruff"], "rev do ruff-pre-commit diverge do ruff do grupo dev"


@pytest.mark.req("RNF-006")
@pytest.mark.parametrize("workflow", WORKFLOWS, ids=lambda p: p.name)
def test_workflow_pins_actions_by_sha_and_tools_by_version(workflow: Path) -> None:
    text = workflow.read_text(encoding="utf-8")
    for action in re.findall(r"uses:\s*(\S+)", text):
        assert re.fullmatch(r"[\w.-]+/[\w./-]+@[0-9a-f]{40}", action), f"action sem hash: {action}"
    pins = dev_pins()
    for name, version in re.findall(r"pip install (?:--upgrade )?([A-Za-z0-9_.-]+)==(\S+)", text):
        if normalize(name) in pins:
            assert pins[normalize(name)] == version, f"{name}=={version} diverge do grupo dev"


@pytest.mark.req("RNF-006")
@pytest.mark.parametrize("pattern", [".env", "*.db", "*.sqlite3"])
def test_secrets_and_local_databases_are_git_ignored(pattern: str) -> None:
    ignored = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert pattern in ignored
