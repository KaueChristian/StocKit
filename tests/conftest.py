"""Configuração comum dos testes.

Perfis do hypothesis (escolhidos pela variável de ambiente HYPOTHESIS_PROFILE):
- ``dev`` (padrão): rápido, para rodar a cada mudança.
- ``ci``: determinístico (``derandomize``) e com mais exemplos, para o CI e os portões.
"""

import os

from hypothesis import HealthCheck, settings

settings.register_profile("dev", max_examples=50)
settings.register_profile(
    "ci",
    max_examples=300,
    derandomize=True,
    print_blob=True,
    suppress_health_check=[HealthCheck.too_slow],
)
settings.load_profile(os.environ.get("HYPOTHESIS_PROFILE", "dev"))
