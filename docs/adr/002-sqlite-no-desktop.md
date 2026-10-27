# ADR-002: Desktop persiste em SQLite com repositórios próprios (`sqlite3` da biblioteca padrão)

## Status

Aceito — 2026-10-27 (decisão D-02, escolhida pelo usuário)

## Contexto

O desktop precisa funcionar **offline, sem servidor e sem conta**, com um arquivo de dados que o usuário possa copiar
(princípio 6). O executável (PyInstaller, M3.12) deve ser leve e abrir rápido (RNF-003). Havia duas opções para
implementar as portas do núcleo (ADR-001): repositórios escritos sobre `sqlite3`, ou reaproveitar o Django ORM sem
servidor (`django.setup()` sem `runserver`).

## Decisão

O desktop usa **repositórios próprios sobre `sqlite3`** em `adapters/sqlite`, implementando as portas do núcleo:

- conexão com `foreign_keys=ON`, `journal_mode=WAL`, `busy_timeout` e `row_factory` (M2.2);
- schema em SQL numerado com migrações controladas por `PRAGMA user_version` (M2.1);
- movimentações **append-only**: triggers bloqueiam `UPDATE`/`DELETE` (ADR-004, M2.4);
- `UnitOfWork` transacional com commit/rollback (M2.5);
- quantidades e custos gravados como texto decimal e lidos como `Decimal` (princípio 4: nunca `float`);
- datas em UTC (ISO 8601).

## Consequências

- **Positivas:** zero dependência de runtime além da biblioteca padrão; executável menor; controle total do SQL
  (índices, visões de saldo, triggers); demonstra o padrão de portas e adaptadores na prática.
- **Negativas / custos:** dois adaptadores persistentes (SQLite e Django ORM) e dois schemas para manter
  equivalentes; migrações escritas à mão.
- **Como verificar:** **suíte de contrato** parametrizada rodando os mesmos testes contra memória e SQLite (M2.6) e,
  depois, Django ORM (M5.3); teste de migração v1 → vN (TP-M2-02); triggers testados (TP-M2-04); teste de paridade
  com JSON dourado (M5.10).

## Alternativas consideradas

| Alternativa | Por que não |
|---|---|
| Django ORM sem servidor no desktop | Um só schema, mas executável pesado, inicialização mais lenta e foge da stack Tkinter + SQLite puro. Fica como **plano B** (P-08), reavaliado só se o escopo da M2/M5 estourar |
| SQLAlchemy nos dois lados | Terceira stack para aprender e manter; na web o Django ORM já vem integrado ao admin, migrações e DRF |
| Arquivo JSON/CSV como banco | Sem transação, sem integridade referencial, lento com 100 mil movimentações (RNF-002) |

## Referências

- `PROJECT_CONTEXT.md` §4.6, §5.2, §6.3, §16 (P-08), §18 (D-02)
- Requisitos: RF-013, RF-014, RNF-002, RNF-003, RNF-004
