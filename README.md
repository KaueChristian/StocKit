# StocKit

Gerenciador de estoque **universal**, com o mesmo núcleo em duas plataformas:

- **Desktop:** Tkinter + SQLite, offline, sem servidor.
- **Web:** Django + Django REST Framework + React (TypeScript).

O saldo vem de um **livro de movimentações imutáveis** (nunca de uma coluna editável), o sistema ajuda a decidir
(reposição, curva ABC, previsão de ruptura, validade) e se adapta a qualquer negócio por **perfis** configuráveis.

> **Status:** em fundação (milestone M0). Ainda não há código executável.

## Documentação

- [`PROJECT_CONTEXT.md`](PROJECT_CONTEXT.md) — documento-chefe: visão, arquitetura, requisitos, roadmap, diário e decisões.
- [`docs/`](docs/README.md) — [requisitos](docs/requirements.md), [glossário](docs/glossary.md),
  [decisões de arquitetura (ADRs)](docs/adr/README.md) e [planos de teste](docs/test-plan/README.md).

## Ambiente de desenvolvimento

Requisitos: **Python 3.14** e **Git**. (Node 24 LTS só será necessário a partir do frontend web, M6.)

```powershell
py -3.14 -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip==26.2.2
.venv\Scripts\python -m pip install -e . --group dev
.venv\Scripts\python -m pre_commit install
.venv\Scripts\python tools\check.py
```

O pacote `core` fica instalado em modo editável: alterações no código valem sem reinstalar.

### Verificação (`check`)

`python tools/check.py` é o comando único de qualidade (no Linux/CI, `make check` chama o mesmo script). Ele roda:
ruff (lint e formato), mypy (estrito), import-linter (regras de arquitetura) e pytest com cobertura do `core`
(mínimo 90%). Uma etapa só está pronta com o check verde. O pre-commit roda ruff, mypy, import-linter e pytest a cada
commit.

### Regras de arquitetura (import-linter)

Os contratos ficam no `pyproject.toml`, seção `[tool.importlinter]`:

- **`core-puro`**: o `core` não importa adaptadores, apps, Tkinter, Django, `sqlite3`, bibliotecas de relatório,
  rede, subprocessos nem ferramentas de teste.
- **`core-camadas`**: dentro do `core`, `services` → `ports` → `domain` (nunca o contrário).

Imports dinâmicos (`importlib.import_module("tkinter")`) **não** são detectados; a revisão de código cobre esse caso.

### Integração contínua

[`.github/workflows/ci.yml`](.github/workflows/ci.yml) roda em push e PR nas branches `dev` e `main`:

- **check** (Ubuntu e Windows): instala o projeto do zero e roda `python tools/check.py` com o hypothesis no perfil `ci`.
- **higiene** (Ubuntu): ganchos do pre-commit que o check não cobre (espaços, fim de arquivo, YAML/TOML, schema dos
  workflows).

As actions são fixadas por hash de commit.

Os testes com hypothesis usam o perfil `dev` (rápido) por padrão; `HYPOTHESIS_PROFILE=ci` deixa a execução
determinística e com mais exemplos.
Extras com versões fixas, instalados quando o milestone pedir: `.[desktop]` (CustomTkinter), `.[web]` (Django LTS + DRF)
e `.[package]` (PyInstaller).

## Branches

- `main` — estável; recebe um milestone só depois do portão de integridade aprovado.
- `dev` — trabalho em andamento.

## Licença

[MIT](LICENSE).
