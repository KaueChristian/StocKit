# Planos de teste

Os casos de cada portão são definidos no `PROJECT_CONTEXT.md` §10 (blocos "Portão") e as execuções são registradas
no §11. Esta pasta guarda o que não cabe numa linha de tabela:

- roteiros de teste manual e exploratório (portões M3, M6 e M7);
- planilhas de cálculo feito à mão usadas como valor esperado (TP-M1-09, TP-M4-01);
- evidências (prints, logs) de execuções de portão, em `evidencias/<milestone>/`.

## Portões

| Milestone | Plano e execuções | Situação |
|---|---|---|
| M0 | [`M0-portao.md`](M0-portao.md) | 4 de 6 casos passaram (2026-10-27); TP-M0-03 e TP-M0-04 pendentes |

## Template de caso de teste manual

Um arquivo por roteiro: `M<n>-<assunto>.md`.

```markdown
### TP-M<n>-<nn> · <Título>

- **Pré-condição:**
- **Passos:**
  1.
- **Resultado esperado:**
- **Evidência:** (print/log, caminho em evidencias/)
- **Status:** Não executado | Passou | Falhou (bug §15: B-xx)
- **Observações:**
```
