# Glossário

Fonte única do vocabulário do StocKit (criada na M0.6 a partir do antigo §20 do `PROJECT_CONTEXT.md`).
Interface e documentação em PT-BR; identificadores de código em inglês (coluna **No código**, quando já definida).

## Domínio

| Termo | Significado | No código |
|---|---|---|
| **Item** | Qualquer coisa controlada em estoque (produto, insumo, ativo, peça) | `Item` |
| **SKU** | Código único que identifica um item | `sku` |
| **Unidade de medida** | Símbolo e grandeza de uma quantidade, com conversões (caixa → 12 un; L → mL) | — |
| **Local** | Lugar onde há saldo; hierárquico (depósito › corredor › prateleira) | — |
| **Parte** | Fornecedor, cliente ou setor; o papel é configurável | — |
| **Lote** | Grupo de unidades de um item com código e validade; base do FEFO | — |
| **Item serializado** | Item controlado por unidade, cada uma com número de série único | — |
| **Movimentação** | Registro imutável de entrada, saída, transferência, ajuste, perda ou devolução | — |
| **Livro (ledger)** | Sequência de movimentações da qual o saldo é derivado | — |
| **Saldo** | Soma assinada das movimentações de (item, local, lote); nunca é armazenado como verdade | — |
| **Saldo em uma data** | Saldo considerando só as movimentações ocorridas até aquele instante | — |
| **Ajuste** | Movimentação que corrige o saldo (nunca se edita uma movimentação antiga) | — |
| **Transferência** | Par atômico saída + entrada entre dois locais; conserva a quantidade total | — |
| **Política de saldo negativo** | Configuração que proíbe (padrão) ou permite saída acima do saldo | — |
| **FEFO** | *First Expired, First Out*: sai primeiro o lote que vence primeiro | — |
| **Campo personalizado** | Campo extra definido por tipo de item (nome, tipo, obrigatório, validação), guardado em JSON | — |
| **Perfil** | JSON que pré-configura rótulos, campos e unidades de um tipo de negócio | — |
| **Contagem / inventário cíclico** | Conferência física: contado × sistema → divergência → movimentos de ajuste | — |
| **Custo médio móvel** | Valoração em que cada entrada recalcula o custo médio do item (D-07) | — |
| **Ponto de reposição** | Saldo a partir do qual se deve repor | — |
| **Estoque de segurança** | Margem para absorver variação de consumo/prazo | — |
| **Curva ABC** | Classificação dos itens por valor de consumo (A mais relevante) | — |
| **Giro** | Quantas vezes o estoque se renova num período | — |
| **Cobertura** | Dias que o estoque atual dura no ritmo de consumo | — |
| **Ruptura** | Falta do item quando há demanda | — |

## Arquitetura

| Termo | Significado |
|---|---|
| **Núcleo (`core`)** | Python puro com domínio, serviços e portas; não conhece banco, UI nem framework (ADR-001) |
| **Porta** | Interface (`Protocol`) que o núcleo define e precisa: repositórios, `UnitOfWork`, `Clock` |
| **Adaptador** | Implementação concreta de uma porta (memória, SQLite, Django ORM) |
| **Value object** | Objeto definido só pelo valor, imutável (ex.: `Quantity`) |
| **Invariante** | Regra que vale sempre (`INV-xx`, `PROJECT_CONTEXT.md` §7.2); cada uma tem teste de propriedade |
| **Unit of Work** | Porta que agrupa gravações numa transação: tudo é gravado ou nada é |
| **Clock** | Porta que fornece a hora atual; injetável para testes determinísticos |
| **Presenter** | Lógica de uma tela do desktop, testável sem abrir janela (padrão MVP, view passiva) |
| **Composition root** | Ponto único onde os adaptadores são escolhidos e ligados aos serviços |

## Processo

| Termo | Significado |
|---|---|
| **Etapa** | Melhoria com ID (`M3.4`) dentro de um milestone |
| **Milestone** | Conjunto de etapas que, somadas, justificam um teste de integridade |
| **Portão** | Execução do plano de teste que fecha um milestone (casos `TP-M<n>-<nn>`; ★ = crítico) |
| **Contrato (teste)** | Suíte que todo adaptador de uma porta precisa passar |
| **Paridade** | Mesmo cenário produz os mesmos resultados no desktop e na web |
| **Dataset de referência** | Dados demo gerados com semente fixa; base dos números dourados |
| **JSON dourado** | Resultado esperado gravado (ex.: saldos do dataset) contra o qual os testes comparam |
| **Check** | `python tools/check.py`: ruff, mypy, import-linter e pytest com cobertura |
| **ADR** | *Architecture Decision Record*: decisão de arquitetura com contexto e consequências |
| **Rastreabilidade** | Ligação requisito ↔ teste ↔ status, gerada por script (M0.9) |
