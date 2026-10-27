# ADR-005: Campos personalizados guardados em JSON e validados por definição

## Status

Aceito — 2026-10-27

## Contexto

O StocKit é universal (§3): uma cozinha quer "temperatura de armazenamento", uma oficina quer "aplicação/modelo", TI
quer "patrimônio". Esses campos não podem virar colunas fixas nem código de nicho no núcleo (§4.3). Eles vêm de
**perfis** (RF-011) e de definições feitas pelo usuário (RF-004), e precisam ser validados igual nas duas
plataformas.

## Decisão

- Cada tipo de item tem **definições de campo** (`CampoPersonalizado`): nome, tipo (texto, número, data, booleano,
  lista de opções), obrigatório e regras de validação.
- Os valores ficam num **único campo JSON** do item (`custom_fields`): objeto `{nome_do_campo: valor}`.
- A **validação acontece no núcleo** (`core`), antes de gravar, contra as definições; erros são erros de domínio
  tipados que identificam o campo (TP-M1-07).
- Persistência: coluna `TEXT` com JSON no SQLite (consultas pelas funções JSON do SQLite quando necessário);
  `JSONField` no Django.
- Números e dinheiro dentro do JSON são gravados como texto decimal e convertidos para `Decimal` no domínio
  (princípio 4).

## Consequências

- **Positivas:** novos campos sem migração de schema; perfis só configuram; validação única no núcleo, igual nas
  duas plataformas; leitura do item vem numa linha só.
- **Negativas / custos:** filtrar e ordenar por campo personalizado é menos eficiente que por coluna (sem índice
  comum); renomear ou remover uma definição exige migrar os valores existentes; o banco não garante o tipo — só o
  núcleo.
- **Como verificar:** testes de validação no núcleo (TP-M1-07); suíte de contrato garante que o JSON volta igual nos
  dois adaptadores; carga dos 4 perfis (TP-M1-08).

## Alternativas consideradas

| Alternativa | Por que não |
|---|---|
| EAV puro (tabela item × atributo × valor) | Consultas e validação complexas e lentas; JSON validado basta para o escopo (P-03) |
| Uma coluna por campo, criada dinamicamente | Migração de schema a cada campo novo; inviável no desktop sem servidor e diferente entre SQLite e Django |
| Campos fixos genéricos (`extra1`, `extra2`...) | Sem tipo, sem nome, sem validação; limita a quantidade de campos |

## Referências

- `PROJECT_CONTEXT.md` §3, §4.3, §7.1, §16 (P-03)
- Requisitos: RF-004, RF-011
