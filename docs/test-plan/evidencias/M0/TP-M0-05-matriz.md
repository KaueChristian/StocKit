# Matriz de rastreabilidade

> Gerada por `tools/traceability.py` em 2026-10-27 14:39 UTC (commit `3e55ded`). Não editar à mão.

**1 de 34** requisitos com teste · **18** testes ligados · **0** requisitos com teste falhando.

| Requisito | Descrição | Milestone | Status declarado | Resultado | Testes |
|---|---|---|---|---|---|
| RF-001 | Cadastrar, editar, inativar e buscar itens | M1/M3/M6 | Planejado | sem teste | — |
| RF-002 | Cadastrar hierarquia de locais | M1/M3/M6 | Planejado | sem teste | — |
| RF-003 | Cadastrar partes (fornecedor/cliente/setor) | M1/M3/M6 | Planejado | sem teste | — |
| RF-004 | Definir campos personalizados por tipo de item e validá-los | M1/M3/M6 | Planejado | sem teste | — |
| RF-005 | Registrar entrada, saída, transferência, ajuste e perda | M1/M3/M6 | Planejado | sem teste | — |
| RF-006 | Calcular saldo por item, local e lote, inclusive "em uma data" | M1 | Planejado | sem teste | — |
| RF-007 | Impedir saldo negativo conforme política configurável | M1 | Planejado | sem teste | — |
| RF-008 | Controlar lote e validade com saída FEFO | M1 | Planejado | sem teste | — |
| RF-009 | Itens serializados (unidade única, estado) | M1 | Planejado | sem teste | — |
| RF-010 | Conversão entre unidades de medida | M1 | Planejado | sem teste | — |
| RF-011 | Carregar perfis (varejo, cozinha, oficina, TI) | M1/M3 | Planejado | sem teste | — |
| RF-012 | Histórico/extrato imutável por item com filtros | M3/M6 | Planejado | sem teste | — |
| RF-013 | Migrações de schema versionadas e reversíveis a partir de banco antigo | M2 | Planejado | sem teste | — |
| RF-014 | Backup/restauração do banco com verificação de integridade | M2/M3 | Planejado | sem teste | — |
| RF-015 | Importar/exportar itens e movimentações em CSV com relatório de erros por linha | M3/M5/M6 | Planejado | sem teste | — |
| RF-016 | Dashboard com KPIs e alertas | M3/M6 | Planejado | sem teste | — |
| RF-017 | Registrar movimentação via leitor de código de barras (modo scanner) | M3/M6 | Planejado | sem teste | — |
| RF-018 | Ponto de reposição e estoque de segurança por item | M4 | Planejado | sem teste | — |
| RF-019 | Alertas: abaixo do mínimo, a vencer, sem giro | M4 | Planejado | sem teste | — |
| RF-020 | Curva ABC por período | M4 | Planejado | sem teste | — |
| RF-021 | Giro e cobertura em dias | M4 | Planejado | sem teste | — |
| RF-022 | Previsão de ruptura com indicação de confiança | M4 | Planejado | sem teste | — |
| RF-023 | Sugestão de compra por fornecedor | M4 | Planejado | sem teste | — |
| RF-024 | Inventário cíclico com geração de ajustes | M4 | Planejado | sem teste | — |
| RF-025 | Relatórios em PDF e etiquetas com QR/código de barras | M4 | Planejado | sem teste | — |
| RF-026 | API REST documentada (OpenAPI) com autenticação e papéis | M5 | Planejado | sem teste | — |
| RF-027 | Interface web com os mesmos fluxos do desktop | M6 | Planejado | sem teste | — |
| RF-028 | Modo demonstração com dados determinísticos | M2/M7 | Planejado | sem teste | — |
| RNF-001 | Cobertura de testes do `core` ≥ 90% (linhas) | M1 em diante | Em andamento (gate ativo desde a M0.3) | sem teste | — |
| RNF-002 | Saldo de item calculado em < 100 ms com 100 mil movimentações (meta inicial; recalibrar com medição) | M2/M4 | Planejado | sem teste | — |
| RNF-003 | Abertura do desktop em < 3 s com o dataset demo (meta inicial) | M3 | Planejado | sem teste | — |
| RNF-004 | Paridade: mesmo dataset ⇒ mesmos saldos nas duas plataformas | M5 | Planejado | sem teste | — |
| RNF-005 | Acessibilidade: operação completa por teclado; contraste AA | M3/M6 | Planejado | sem teste | — |
| RNF-006 | Nenhum segredo no repositório; dependências com versão fixa | M0 em diante | Em andamento (diretas fixadas; transitivas sem lock) | ok | `tests/project/test_dependency_pins.py::test_every_declared_dependency_has_exact_version[setuptools==84.2.1]` (passed)<br>`tests/project/test_dependency_pins.py::test_every_declared_dependency_has_exact_version[customtkinter==6.0.0]` (passed)<br>`tests/project/test_dependency_pins.py::test_every_declared_dependency_has_exact_version[Django==5.2.18]` (passed)<br>`tests/project/test_dependency_pins.py::test_every_declared_dependency_has_exact_version[djangorestframework==3.18.3]` (passed)<br>`tests/project/test_dependency_pins.py::test_every_declared_dependency_has_exact_version[pyinstaller==6.22.3]` (passed)<br>`tests/project/test_dependency_pins.py::test_every_declared_dependency_has_exact_version[ruff==0.17.3]` (passed)<br>`tests/project/test_dependency_pins.py::test_every_declared_dependency_has_exact_version[mypy==2.4.0]` (passed)<br>`tests/project/test_dependency_pins.py::test_every_declared_dependency_has_exact_version[pytest==9.1.1]` (passed)<br>`tests/project/test_dependency_pins.py::test_every_declared_dependency_has_exact_version[pytest-cov==7.1.0]` (passed)<br>`tests/project/test_dependency_pins.py::test_every_declared_dependency_has_exact_version[coverage==7.17.0]` (passed)<br>`tests/project/test_dependency_pins.py::test_every_declared_dependency_has_exact_version[hypothesis==6.170.12]` (passed)<br>`tests/project/test_dependency_pins.py::test_every_declared_dependency_has_exact_version[pre-commit==4.7.0]` (passed)<br>`tests/project/test_dependency_pins.py::test_every_declared_dependency_has_exact_version[import-linter==2.15]` (passed)<br>`tests/project/test_dependency_pins.py::test_pre_commit_versions_match_dev_group` (passed)<br>`tests/project/test_dependency_pins.py::test_workflow_pins_actions_by_sha_and_tools_by_version[ci.yml]` (passed)<br>`tests/project/test_dependency_pins.py::test_secrets_and_local_databases_are_git_ignored[.env]` (passed)<br>`tests/project/test_dependency_pins.py::test_secrets_and_local_databases_are_git_ignored[*.db]` (passed)<br>`tests/project/test_dependency_pins.py::test_secrets_and_local_databases_are_git_ignored[*.sqlite3]` (passed) |
