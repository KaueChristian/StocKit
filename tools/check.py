"""Verificação única do projeto (equivalente a ``make check``; funciona no Windows sem GNU make).

Uso:  python tools/check.py          (com o venv ativo, ou .venv\\Scripts\\python tools\\check.py)

Roda todas as etapas mesmo que uma falhe, mostra um resumo e sai com código 1 se alguma falhou.
Definição de pronto (PROJECT_CONTEXT.md §9.3.6): este comando precisa estar verde.
"""

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

STEPS: list[tuple[str, list[str]]] = [
    ("ruff (lint)", ["ruff", "check", "."]),
    ("ruff (formato)", ["ruff", "format", "--check", "."]),
    ("mypy", ["mypy"]),
    ("pytest + cobertura", ["pytest", "--cov", "--cov-report=term-missing"]),
]


def run_step(name: str, args: list[str]) -> tuple[bool, float]:
    print(f"\n=== {name} ===", flush=True)
    start = time.perf_counter()
    result = subprocess.run([sys.executable, "-m", *args], cwd=ROOT, check=False)
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
