# C4 nível 1 — Contexto do sistema

O StocKit visto de fora: quem o usa e com o que ele troca informação. Não há integração direta com outros sistemas
(ERP, fiscal e PDV estão fora do escopo, §3); a troca acontece por arquivos CSV.

```mermaid
flowchart TB
    operador["<b>Operador de estoque</b><br/>[Pessoa]<br/>Registra entradas, saídas,<br/>transferências e contagens"]
    gestor["<b>Gestor do negócio</b><br/>[Pessoa]<br/>Configura itens e perfis;<br/>decide compras pelos<br/>alertas e relatórios"]
    avaliador["<b>Avaliador do portfólio</b><br/>[Pessoa]<br/>Abre a demo com<br/>dados de exemplo"]

    stockit["<b>StocKit</b><br/>[Sistema de software]<br/>Controle de estoque universal:<br/>livro de movimentações, saldos,<br/>reposição, curva ABC e previsão.<br/>Roda no desktop e na web"]

    scanner["<b>Leitor de código de barras</b><br/>[Dispositivo externo]<br/>Funciona como teclado"]
    planilhas["<b>Planilhas e outros sistemas</b><br/>[Externo]<br/>Fonte e destino de itens<br/>e movimentações"]
    impressora["<b>Impressora / leitor de PDF</b><br/>[Externo]<br/>Relatórios e etiquetas"]

    operador -->|"Usa no desktop ou no navegador"| stockit
    gestor -->|"Configura e consulta"| stockit
    avaliador -->|"Explora a demo"| stockit
    scanner -->|"Envia os códigos lidos"| stockit
    stockit <-->|"Importa e exporta CSV"| planilhas
    stockit -->|"Gera PDF e etiquetas<br/>com QR/código de barras"| impressora

    classDef person fill:#08427b,stroke:#052e56,color:#ffffff
    classDef system fill:#1168bd,stroke:#0b4884,color:#ffffff
    classDef external fill:#6b6b6b,stroke:#4d4d4d,color:#ffffff
    class operador,gestor,avaliador person
    class stockit system
    class scanner,planilhas,impressora external
```

## Elementos

| Elemento | Tipo | Papel | Requisitos |
|---|---|---|---|
| Operador de estoque | Pessoa | Opera o dia a dia: movimentações, contagens, consulta de saldo e extrato | RF-005, RF-012, RF-017, RF-024 |
| Gestor do negócio | Pessoa | Cadastra itens, locais, partes e perfis; acompanha dashboard, alertas e sugestão de compra | RF-001..RF-004, RF-011, RF-016, RF-018..RF-023 |
| Avaliador do portfólio | Pessoa | Abre o `.exe` ou a demo web com dados determinísticos | RF-028 |
| Leitor de código de barras | Dispositivo | Lê o código e "digita" no campo focado (modo scanner) | RF-017 |
| Planilhas e outros sistemas | Externo | Origem e destino de dados em CSV, com relatório de erros por linha | RF-015 |
| Impressora / leitor de PDF | Externo | Recebe relatórios e etiquetas | RF-025 |

## Fora deste diagrama (de propósito)

- **Sincronização desktop ↔ web:** não existe no escopo atual (P-05, backlog B-01). Cada plataforma tem seus dados.
- **Servidor dedicado:** não há; ver os modos de execução em `PROJECT_CONTEXT.md` §5.3 e o nível 2.
