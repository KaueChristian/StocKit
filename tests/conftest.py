"""Configuração comum dos testes.

Perfis do hypothesis (escolhidos pela variável de ambiente HYPOTHESIS_PROFILE):
- ``dev`` (padrão): rápido, para rodar a cada mudança.
- ``ci``: determinístico (``derandomize``) e com mais exemplos, para o CI e os portões.
"""

import os

import pytest
from hypothesis import HealthCheck, settings

from tools.traceability import has_req_marker, load_requirements, marker_problems, req_ids

settings.register_profile("dev", max_examples=50)
settings.register_profile(
    "ci",
    max_examples=300,
    derandomize=True,
    print_blob=True,
    suppress_health_check=[HealthCheck.too_slow],
)
settings.load_profile(os.environ.get("HYPOTHESIS_PROFILE", "dev"))


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Todo ``@pytest.mark.req`` precisa citar requisitos que existem em docs/requirements.md."""
    links = {item.nodeid: req_ids(item) for item in items if has_req_marker(item)}
    problems = marker_problems(links, set(load_requirements()))
    if problems:
        raise pytest.UsageError("marker req inválido:\n  " + "\n  ".join(problems))
