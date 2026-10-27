"""Verificação única do projeto (equivalente a ``make check``; funciona no Windows sem GNU make).

Uso:  python tools/check.py          (com o venv ativo, ou .venv\\Scripts\\python tools\\check.py)

Roda todas as etapas mesmo que uma falhe, mostra um resumo e sai com código 1 se alguma falhou.
Definição de pronto (PROJECT_CONTEXT.md §9.3.6): este comando precisa estar verde.
"""

import os
import subprocess
import sys
import sysconfig
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Pasta de executáveis do Python em uso. Num venv é a pasta do próprio python.exe, mas numa
# instalação comum do Windows (como no CI) fica na subpasta Scripts: por isso o sysconfig.
SCRIPTS = Path(sysconfig.get_path("scripts"))


def module(*args: str) -> list[str]:
    """Roda uma ferramenta como ``python -m`` com o Python do venv."""
    return [sys.executable, "-m", *args]


def script(name: str, *args: str) -> list[str]:
    """Roda um executável instalado no Python em uso (para ferramentas sem ``__main__``)."""
    return [str(SCRIPTS / name), *args]


STEPS: list[tuple[str, list[str]]] = [
    ("ruff (lint)", module("ruff", "check", ".")),
    ("ruff (formato)", module("ruff", "format", "--check", ".")),
    ("mypy", module("mypy")),
    ("import-linter", script("lint-imports")),
    ("pytest + cobertura", module("pytest", "--cov", "--cov-report=term-missing")),
]


def run_step(name: str, command: list[str]) -> tuple[bool, float]:
    print(f"\n=== {name} ===", flush=True)
    start = time.perf_counter()
    # UTF-8 forçado: sem isso, acentos saem embaralhados quando a saída é redirecionada no Windows.
    env = os.environ | {"PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    try:
        result = subprocess.run(command, cwd=ROOT, env=env, check=False)
    except FileNotFoundError:
        print(f"ferramenta não encontrada: {command[0]}", flush=True)
        return False, time.perf_counter() - start
    return result.returncode == 0, time.perf_counter() - start


def main() -> int:
    results = [(name, *run_step(name, args)) for name, args in STEPS]

    print("\n=== resumo ===")
    for name, ok, seconds in results:
        print(f"{'OK   ' if ok else 'FALHA'}  {name:<22} {seconds:6.1f} s")
    total = sum(seconds for _, _, seconds in results)
    failed = [name for name, ok, _ in results if not ok]
    print(f"total: {total:.1f} s")
    if failed:
        print(f"check FALHOU: {', '.join(failed)}")
        return 1
    print("check OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
