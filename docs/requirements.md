# Requisitos

Fonte única dos requisitos do StocKit (criada na M0.6 a partir do antigo §8 do `PROJECT_CONTEXT.md`).

**Regras**

- Cada RF/RNF tem ID estável, milestone-alvo e **pelo menos um teste** marcado com `@pytest.mark.req("RF-xxx")`
  (ou equivalente no Vitest/Playwright). A matriz requisito × teste × status é gerada por `tools/traceability.py`
  (M0.9).
- A coluna **Portão** aponta os casos dos planos de teste (`TP-M<n>-<nn>`, `PROJECT_CONTEXT.md` §10) que verificam
  o requisito. Um teste automatizado confere que todo ID citado aqui existe lá.
- Mudou comportamento → muda o requisito aqui, o teste ligado a ele e a documentação, **no mesmo commit**.
- IDs nunca são reaproveitados. Requisito descartado fica na tabela com status `Descartado` e o motivo.

Status: `Planejado` · `Em andamento` · `Atendido` (teste verde ligado) · `Descartado`.

## Requisitos funcionais

| ID | Requisito | Milestone | Invariantes | Portão | Status |
|---|---|---|---|---|---|
| RF-001 | Cadastrar, editar, inativar e buscar itens | M1/M3/M6 | — | TP-M3-02, TP-M6-01 | Em andamento (M1.2: entidade e regras) |
| RF-002 | Cadastrar hierarquia de locais | M1/M3/M6 | INV-08 | TP-M1-12, TP-M1-02 | Em andamento (M1.2: entidade e árvore) |
| RF-003 | Cadastrar partes (fornecedor/cliente/setor) | M1/M3/M6 | — | TP-M1-13 | Em andamento (M1.2: entidade e papéis) |
| RF-004 | Definir campos personalizados por tipo de item e validá-los | M1/M3/M6 | — | TP-M1-07 | Planejado |
| RF-005 | Registrar entrada, saída, transferência, ajuste e perda | M1/M3/M6 | INV-02, INV-03 | TP-M1-01, TP-M1-02, TP-M3-02 | Em andamento (núcleo pronto: M1.3 movimentação, M1.6 registro, M1.8 transferência; telas M3/M6) |
| RF-006 | Calcular saldo por item, local e lote, inclusive "em uma data" | M1 | INV-01, INV-08 | TP-M1-01, TP-M1-02, TP-M3-02 | Atendido (M1.7: total, por local com sublocais, por lote e em uma data) |
| RF-007 | Impedir saldo negativo conforme política configurável | M1 | INV-05 | TP-M1-04, TP-M3-03, TP-M5-04 | Em andamento (M1.6: política aplicada no registro; configuração na M1.12) |
| RF-008 | Controlar lote e validade com saída FEFO | M1 | INV-06 | TP-M1-05 | Planejado |
| RF-009 | Itens serializados (unidade única, estado) | M1 | INV-07 | TP-M1-06 | Planejado |
| RF-010 | Conversão entre unidades de medida | M1 | INV-04 | TP-M1-03 | Atendido (M1.1; regras no ADR-006) |
| RF-011 | Carregar perfis (varejo, cozinha, oficina, TI) | M1/M3 | — | TP-M1-08 | Planejado |
| RF-012 | Histórico/extrato imutável por item com filtros | M3/M6 | INV-02 | TP-M3-02, TP-M6-01 | Planejado |
| RF-013 | Migrações de schema versionadas e reversíveis a partir de banco antigo | M2 | — | TP-M2-02 | Planejado |
| RF-014 | Backup/restauração do banco com verificação de integridade | M2/M3 | — | TP-M2-06 | Planejado |
| RF-015 | Importar/exportar itens e movimentações em CSV com relatório de erros por linha | M3/M5/M6 | — | TP-M3-04, TP-M6-02 | Planejado |
| RF-016 | Dashboard com KPIs e alertas | M3/M6 | — | — (lacuna) | Planejado |
| RF-017 | Registrar movimentação via leitor de código de barras (modo scanner) | M3/M6 | — | TP-M3-05 | Planejado |
| RF-018 | Ponto de reposição e estoque de segurança por item | M4 | — | TP-M4-01 | Planejado |
| RF-019 | Alertas: abaixo do mínimo, a vencer, sem giro | M4 | — | — (lacuna) | Planejado |
| RF-020 | Curva ABC por período | M4 | — | TP-M4-02 | Planejado |
| RF-021 | Giro e cobertura em dias | M4 | — | TP-M4-01, TP-M4-05 | Planejado |
| RF-022 | Previsão de ruptura com indicação de confiança | M4 | — | TP-M4-03 | Planejado |
| RF-023 | Sugestão de compra por fornecedor | M4 | — | TP-M5-02 | Planejado |
| RF-024 | Inventário cíclico com geração de ajustes | M4 | — | TP-M4-04 | Planejado |
| RF-025 | Relatórios em PDF e etiquetas com QR/código de barras | M4 | — | TP-M4-06 | Planejado |
| RF-026 | API REST documentada (OpenAPI) com autenticação e papéis | M5 | — | TP-M5-03, TP-M5-05 | Planejado |
| RF-027 | Interface web com os mesmos fluxos do desktop | M6 | — | TP-M6-01, TP-M6-03 | Planejado |
| RF-028 | Modo demonstração com dados determinísticos | M2/M7 | — | TP-M2-05, TP-M7-03 | Planejado |

## Requisitos não funcionais

| ID | Requisito | Milestone | Invariantes | Portão | Status |
|---|---|---|---|---|---|
| RNF-001 | Cobertura de testes do `core` ≥ 90% (linhas) | M1 em diante | — | TP-M1-10 | Em andamento (gate ativo desde a M0.3) |
| RNF-002 | Saldo de item calculado em < 100 ms com 100 mil movimentações (meta inicial; recalibrar com medição) | M2/M4 | — | TP-M2-07 | Planejado |
| RNF-003 | Abertura do desktop em < 3 s com o dataset demo (meta inicial) | M3 | — | TP-M3-07 | Planejado |
| RNF-004 | Paridade: mesmo dataset ⇒ mesmos saldos nas duas plataformas | M5 | — | TP-M5-02 | Planejado |
| RNF-005 | Acessibilidade: operação completa por teclado; contraste AA | M3/M6 | — | TP-M3-05, TP-M6-04 | Planejado |
| RNF-006 | Nenhum segredo no repositório; dependências com versão fixa | M0 em diante | — | TP-M7-05 | Em andamento (diretas fixadas; transitivas sem lock) |

## Lacunas conhecidas

Requisitos sem caso de portão que os verifique diretamente. Cada um precisa ganhar um caso antes do portão do
primeiro milestone em que aparece:

| ID | Primeiro milestone | Sugestão de caso |
|---|---|---|
| RF-016 | M3 | KPIs do dashboard == valores calculados pelos serviços sobre o dataset demo |
| RF-019 | M4 | Dataset com item abaixo do mínimo, lote a vencer e item parado: cada alerta aparece uma vez |
