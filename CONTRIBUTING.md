# Como contribuir

O processo completo está no [`PROJECT_CONTEXT.md`](PROJECT_CONTEXT.md) §0. Este é o resumo.

## Ambiente

Python 3.14 e Git. Passo a passo no [README](README.md#ambiente-de-desenvolvimento):

```powershell
py -3.14 -m venv .venv
.venv\Scripts\python -m pip install -e . --group dev
.venv\Scripts\python -m pre_commit install
.venv\Scripts\python tools\check.py
```

## Fluxo de trabalho

1. Escolha **uma** etapa do milestone aberto (`PROJECT_CONTEXT.md` §10): a de menor ID com os pré-requisitos
   cumpridos. Não pule milestone sem o portão do anterior aprovado.
2. Trabalhe na branch `dev` (ou numa branch a partir dela). A `main` só recebe um milestone depois do portão.
3. Mudou comportamento → no **mesmo commit**: requisito em `docs/requirements.md`, teste marcado com
   `@pytest.mark.req("RF-xxx")` e documentação.
4. Rode `python tools/check.py` até ficar verde. O pre-commit roda o mesmo conjunto a cada commit.
5. Atualize o `PROJECT_CONTEXT.md`: painel (§1), status da etapa (§10) e uma linha no diário (§14), inclusive do que
   não deu certo. Bug → §15; ideia rejeitada → §16 com o motivo; decisão → §19 (e ADR em `docs/adr/` se for de
   arquitetura).

## Regras que o código precisa seguir

- O `core` é Python puro: não importa banco, UI, framework, rede nem ferramentas de teste (import-linter).
- Saldo é derivado do livro de movimentações; nunca uma coluna editável (ADR-004).
- Regra de negócio só em `core/services`; telas e views só orquestram e exibem.
- `Decimal` em quantidades e dinheiro; datas em UTC com relógio injetável.

## Commits

[Conventional Commits](https://www.conventionalcommits.org/), um assunto por commit, citando a etapa:

```
feat(core): registra movimentação com política de saldo negativo (M1.6)
fix(desktop): corrige foco do modo scanner após erro (M3.5)
docs: atualiza ADR-002 com o índice de saldo (M2.8)
```

Tipos usados: `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `build`, `ci`, `chore`.

## Issues e pull requests

- Bugs e etapas têm formulários próprios (`.github/ISSUE_TEMPLATE/`).
- O template de PR traz o checklist da definição de pronto (§9.3.6).
- **Publicar é um ato deliberado:** push, tag, release e deploy só com pedido explícito do responsável pelo projeto.
