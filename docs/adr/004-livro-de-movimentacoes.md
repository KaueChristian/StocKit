# ADR-004: Estoque como livro de movimentações imutáveis; saldo sempre derivado

## Status

Aceito — 2026-10-27

## Contexto

Saldo errado é o pior bug possível num sistema de estoque (§4.1). Um saldo guardado como coluna editável perde o
histórico, permite inconsistência silenciosa e não responde "quanto havia em tal data". As funções de inteligência
(M4: giro, curva ABC, previsão de ruptura) precisam justamente do histórico de entradas e saídas.

## Decisão

- Toda mudança de estoque é uma **movimentação**: entrada, saída, transferência, ajuste, perda ou devolução.
- Movimentações são **imutáveis**: nunca alteradas nem apagadas (INV-02). Erro se corrige com movimento de ajuste.
- O **saldo** de (item, local, lote) é a soma assinada das movimentações (INV-01); nunca é a fonte da verdade.
- Transferência é um par saída + entrada gravado atomicamente (INV-03).
- Cada movimentação registra item, local, lote, quantidade (`Decimal`), custo unitário, motivo, autor e `ocorreu_em`
  (UTC, relógio injetável).
- Desempenho: se a soma ficar lenta (RNF-002), usar índices, visões ou **snapshots derivados e reconstruíveis** do
  livro — nunca um saldo editável. Só depois de medir (§0: meça antes de otimizar).

## Consequências

- **Positivas:** auditoria completa; saldo em qualquer data; extrato por item (RF-012); a inteligência do M4 sai do
  mesmo dado; inconsistência vira impossível por construção.
- **Negativas / custos:** cálculo de saldo custa mais que ler uma coluna; corrigir um lançamento errado exige dois
  registros (o original e o ajuste), o que precisa ficar claro na interface.
- **Como verificar:** testes de propriedade (hypothesis) para INV-01, INV-03 e INV-08 (TP-M1-01, TP-M1-02); triggers
  no SQLite que rejeitam `UPDATE`/`DELETE` (TP-M2-04); repositórios sem métodos de alteração; medição de RNF-002
  (TP-M2-07).

## Alternativas consideradas

| Alternativa | Por que não |
|---|---|
| Saldo como coluna editável do item | Perde auditoria e permite inconsistência (P-02) |
| Saldo em coluna + log de auditoria à parte | Duas fontes da verdade que podem discordar; o log vira enfeite |
| Event sourcing completo (todas as entidades como eventos) | Complexidade além do necessário; só o estoque precisa de histórico imutável |

## Referências

- `PROJECT_CONTEXT.md` §0 (regras inegociáveis), §4.1, §7.1, §7.2, §16 (P-02)
- Requisitos: RF-005, RF-006, RF-012, RNF-002
