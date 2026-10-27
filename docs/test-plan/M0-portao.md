# Portão M0 — Fundação

Plano de teste em `PROJECT_CONTEXT.md` §10 (bloco "Portão M0"). Execuções registradas no §11.
Casos críticos (★) precisam passar 100% para fechar o milestone.

**Execução 1 — 2026-10-27, commit `3e55ded` (branch `dev`), Windows 11, Python 3.14.3.**
Resultado: 4 de 6 casos executados, todos passaram. TP-M0-03 ★ e TP-M0-04 pendentes (exigem repositório no
GitHub). **Portão não fechado.**

---

### TP-M0-01 ★ · Clone limpo → venv → instalar → check

- **Pré-condição:** Python 3.14 e Git instalados; repositório na branch `dev`.
- **Passos:**
  1. `git clone -b dev <repo> clone` numa pasta temporária vazia.
  2. Seguir **só** os comandos do README, seção "Ambiente de desenvolvimento", no PowerShell: criar venv, atualizar
     pip, `pip install -e . --group dev`, `pre_commit install`, `python tools\check.py`.
- **Resultado esperado:** check verde, sem passo manual fora do README.
- **Resultado obtido:** check verde (ruff, formato, mypy, import-linter, pytest: 128 testes, cobertura do `core`
  100%); nenhum passo extra; 36 s do clone ao fim do check (cache do pip já aquecido nesta máquina).
- **Evidência:** [`evidencias/M0/TP-M0-01.log`](evidencias/M0/TP-M0-01.log)
- **Status:** Passou
- **Observações:** máquina limpa de verdade (sem cache do pip) não foi testada; o CI no GitHub fará isso (TP-M0-03).

### TP-M0-02 ★ · `import tkinter` no `core` → import-linter falha; CI falha

- **Pré-condição:** clone do TP-M0-01 com check verde.
- **Passos:**
  1. Criar `core/domain/_portao.py` com um import de `tkinter`.
  2. Rodar `lint-imports`, depois `python tools\check.py` (mesmo comando do job `check` do CI).
  3. Tentar `git commit` (ganchos do pre-commit).
- **Resultado esperado:** import-linter falha com o contrato `core-puro`; check falha; commit bloqueado.
- **Resultado obtido:** `lint-imports` saiu com 1 ("core is not allowed to import tkinter"); check saiu com 1;
  commit bloqueado (HEAD não mudou).
- **Evidência:** [`evidencias/M0/TP-M0-02.log`](evidencias/M0/TP-M0-02.log)
- **Status:** Passou (parte local). A falha **no GitHub Actions** depende do TP-M0-03.
- **Observações:** na 1ª tentativa o arquivo tinha só `import tkinter` (sem uso). No commit, o gancho
  `ruff check --fix` **apagou** o import não usado antes do import-linter rodar, e o gancho do import-linter apareceu
  como "Passed" — o commit foi barrado pelo ruff, não pela regra de arquitetura. Repetido com o import **usado**
  (`JANELA = tkinter.Tk`): o gancho do import-linter falhou como esperado. Não é defeito (um import proibido real é
  usado), mas casos de violação devem usar import usado. A sentinela (`tests/architecture`) também falhou porque
  copia o `core` real, que estava com a violação — sinal extra, coerente.

### TP-M0-03 ★ · PR de teste na `dev` → CI executa e reporta

- **Pré-condição:** repositório no GitHub com `main` e `dev` publicadas.
- **Status:** **Pendente** — não há repositório remoto; push só com pedido explícito do usuário (§0).

### TP-M0-04 · Mermaid dos C4 renderiza no GitHub

- **Pré-condição:** repositório no GitHub.
- **Status:** **Pendente** — mesmo motivo do TP-M0-03.
- **Observações:** renderização local já conferida na M0.7 (Mermaid 11.4.1, temas claro e escuro); o GitHub usa a
  própria versão do Mermaid.

### TP-M0-05 ★ · `tools/traceability.py` gera a matriz com teste ligado a requisito

- **Pré-condição:** commit `3e55ded`, árvore limpa.
- **Passos:** `python tools\traceability.py --output docs\test-plan\evidencias\M0\TP-M0-05-matriz.md`.
- **Resultado esperado:** matriz gerada com um teste ligado a um requisito (o plano original dizia "teste dummy ligado
  a um RF"; trocado por testes reais da RNF-006, decisão no §19).
- **Resultado obtido:** saída 0; 34 requisitos na matriz; **RNF-006 com 18 testes ligados, resultado "ok"**; demais
  33 "sem teste" (esperado no M0).
- **Evidência:** [`evidencias/M0/TP-M0-05-matriz.md`](evidencias/M0/TP-M0-05-matriz.md)
- **Status:** Passou

### TP-M0-06 · ADRs 001–005 existem e seguem o template

- **Pré-condição:** `docs/adr/` com os 5 ADRs.
- **Passos:**
  1. Teste automático de estrutura (`tests/docs/test_docs_consistency.py`, casos de ADR).
  2. Revisão manual: status e data; afirmações conferidas no repositório (contratos `core-puro`/`core-camadas` e
     camadas no `pyproject.toml`, sentinela existente, Django 5.2.18 no extra `web`, `core` sem dependências);
     referências a P-02/03/04/07/08, D-02 e etapas M0.10, M2.x, M3.12, M5.x existem no `PROJECT_CONTEXT.md`.
- **Resultado esperado:** todos existem, seguem o template e não contradizem o código.
- **Resultado obtido:** estrutura ok; 5 ADRs "Aceito — 2026-10-27"; nenhuma afirmação contradiz o repositório.
- **Status:** Passou
- **Observações:** a revisão foi feita pelo próprio autor dos ADRs; uma leitura independente é recomendada.
