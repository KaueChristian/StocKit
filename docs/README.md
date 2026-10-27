# Documentação do StocKit

Documentação como código: muda junto com o comportamento, no mesmo commit (PROJECT_CONTEXT.md §0.7).
O documento-chefe, com roadmap, diário, bugs e decisões, é o [`PROJECT_CONTEXT.md`](../PROJECT_CONTEXT.md) na raiz.

| Caminho | Conteúdo | Desde |
|---|---|---|
| [`requirements.md`](requirements.md) | Requisitos funcionais e não funcionais com ID, milestone e casos de portão (**fonte única**) | M0.6 |
| [`glossary.md`](glossary.md) | Vocabulário do domínio e do processo (**fonte única**) | M0.6 |
| [`adr/`](adr/README.md) | Registros de decisão de arquitetura (ADRs) e o template | M0.6 |
| [`test-plan/`](test-plan/README.md) | Planos de teste dos portões, roteiros manuais e planilhas de cálculo | M0.6 |
| [`c4/`](c4/README.md) | Diagramas C4 em Mermaid: [contexto](c4/01-contexto.md) e [containers](c4/02-containers.md) | M0.7 |
| `api/` | OpenAPI gerado pelo drf-spectacular | M5.7 |

A consistência entre estes arquivos e o `PROJECT_CONTEXT.md` é verificada por teste
(`tests/docs/test_docs_consistency.py`): IDs de requisito e de caso de portão citados precisam existir, e todo ADR
precisa seguir o template, e cada nível do C4 tem um diagrama `flowchart`.
