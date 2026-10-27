# StocKit

Gerenciador de estoque **universal**, com o mesmo núcleo em duas plataformas:

- **Desktop:** Tkinter + SQLite, offline, sem servidor.
- **Web:** Django + Django REST Framework + React (TypeScript).

O saldo vem de um **livro de movimentações imutáveis** (nunca de uma coluna editável), o sistema ajuda a decidir
(reposição, curva ABC, previsão de ruptura, validade) e se adapta a qualquer negócio por **perfis** configuráveis.

> **Status:** em fundação (milestone M0). Ainda não há código executável.

## Documentação

- [`PROJECT_CONTEXT.md`](PROJECT_CONTEXT.md) — documento-chefe: visão, arquitetura, requisitos, roadmap, diário e decisões.
- `docs/` — ADRs, diagramas C4, requisitos e planos de teste (a partir da etapa M0.6).

## Branches

- `main` — estável; recebe um milestone só depois do portão de integridade aprovado.
- `dev` — trabalho em andamento.

## Licença

[MIT](LICENSE).
