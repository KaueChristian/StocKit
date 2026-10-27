# ADR-001: Núcleo hexagonal em Python puro compartilhado pelas duas plataformas

## Status

Aceito — 2026-10-27

## Contexto

O StocKit roda em duas plataformas, desktop (Tkinter + SQLite) e web (Django + DRF + React), e precisa ter **o mesmo
comportamento** nas duas (RNF-004). Se a regra de negócio morar em telas, views ou models, ela será escrita duas
vezes e vai divergir. O projeto também é vitrine de portfólio: a separação de responsabilidades precisa ser visível
e verificável, não só declarada.

## Decisão

Toda regra de negócio vive num pacote `core` em **Python puro**, organizado em portas e adaptadores (arquitetura
hexagonal):

- `core.domain`: entidades, value objects e erros de domínio;
- `core.ports`: `Protocol`s que o núcleo precisa (repositórios, `UnitOfWork`, `Clock`);
- `core.services`: casos de uso, que recebem as portas por injeção.

Fora do núcleo: `adapters/` (memória, SQLite, Django ORM) implementam as portas; `apps/` (desktop, web) só orquestram
e exibem. Dependências permitidas: `apps` → `core.services` + um adaptador; `adapters` → `core.ports`/`core.domain`;
`core` → nada externo. Dentro do `core`: `services` → `ports` → `domain`.

## Consequências

- **Positivas:** regra testável sem banco nem janela (rápido, determinístico); a mesma suíte de testes do núcleo vale
  para as duas plataformas; trocar banco não toca em regra.
- **Negativas / custos:** mais indireção (interfaces e injeção); cada porta tem duas implementações persistentes
  (SQLite e Django ORM) que podem divergir — mitigado pela suíte de contrato (ADR-002, ADR-003); mapear objetos de
  domínio para o ORM dá trabalho.
- **Como verificar:** contratos `core-puro` e `core-camadas` do import-linter (`pyproject.toml`), rodados no check, no
  pre-commit e no CI; teste "sentinela" (M0.10); suíte de contrato (M2.6, M5.3); teste de paridade (M5.10).

## Alternativas consideradas

| Alternativa | Por que não |
|---|---|
| Django em tudo, inclusive no desktop (ORM sem servidor) | Executável pesado e foge da stack Tkinter + SQLite; mantido como plano B (P-08) |
| Regra dentro dos models/views de cada plataforma | Duplicação garantida e divergência entre plataformas |
| Microsserviço com API usada também pelo desktop | Exige servidor e rede; complexidade sem ganho no escopo (P-07, P-04) |
| Biblioteca compartilhada sem portas (núcleo acessa o banco direto) | Núcleo preso a um banco; não daria para usar Django ORM na web |

## Referências

- `PROJECT_CONTEXT.md` §0 (regras inegociáveis), §4.2, §6.1, §6.2, §16 (P-07, P-08)
- Requisitos: RNF-001, RNF-004
