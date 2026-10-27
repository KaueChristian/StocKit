# C4 nível 2 — Containers

O StocKit por dentro: duas plataformas independentes que compartilham o mesmo **núcleo** (ADR-001). O núcleo não é um
processo à parte: é uma biblioteca Python que roda **dentro** do app desktop e **dentro** da API.

```mermaid
flowchart TB
    usuario["<b>Usuário</b><br/>[Pessoa]<br/>Operador ou gestor"]
    scanner["<b>Leitor de código de barras</b><br/>[Dispositivo externo]"]

    subgraph desktop["Desktop (offline)"]
        app_desktop["<b>App desktop</b><br/>[Container: Python 3.14, CustomTkinter]<br/>Views passivas + presenters.<br/>Empacotado com PyInstaller (M3)"]
        db_desktop[("<b>Arquivo .db</b><br/>[Container: SQLite, WAL]<br/>Livro append-only (triggers).<br/>Copiável pelo usuário (M2)")]
    end

    core["<b>Núcleo · core</b><br/>[Biblioteca: Python puro]<br/>Domínio, serviços e portas.<br/>Toda regra de negócio (M1)"]

    subgraph web["Web"]
        spa["<b>SPA</b><br/>[Container: React + TypeScript, Vite]<br/>Mesmos fluxos do desktop;<br/>cliente gerado do OpenAPI (M6)"]
        api["<b>API</b><br/>[Container: Django 5.2 LTS + DRF]<br/>Views finas, auth por papéis,<br/>OpenAPI, serve o build da SPA (M5)"]
        db_web[("<b>Banco da web</b><br/>[Container: SQLite; Postgres opcional]<br/>Migrações do Django (M5)")]
    end

    usuario -->|"Usa (teclado e mouse)"| app_desktop
    usuario -->|"Usa (navegador)"| spa
    scanner -->|"Códigos como teclado"| app_desktop
    scanner -->|"Códigos como teclado"| spa

    app_desktop -->|"Chama serviços<br/>(no mesmo processo)"| core
    api -->|"Chama serviços<br/>(no mesmo processo)"| core
    spa -->|"JSON via HTTP<br/>sessão + CSRF"| api

    app_desktop -->|"Lê e grava via<br/>adapters/sqlite (sqlite3)"| db_desktop
    api -->|"Lê e grava via<br/>adapters/django_orm"| db_web

    %% Ligação invisível: só posiciona o núcleo entre as duas plataformas.
    db_desktop ~~~ core ~~~ db_web

    classDef person fill:#08427b,stroke:#052e56,color:#ffffff
    classDef external fill:#6b6b6b,stroke:#4d4d4d,color:#ffffff
    classDef container fill:#438dd5,stroke:#2e6295,color:#ffffff
    classDef library fill:#438dd5,stroke:#0b4884,color:#ffffff,stroke-width:3px,stroke-dasharray:6 4
    class usuario person
    class scanner external
    class app_desktop,db_desktop,spa,api,db_web container
    class core library
```

## Elementos

| Container | Tecnologia | Responsabilidade | Não faz | Milestone |
|---|---|---|---|---|
| App desktop | Python 3.14, CustomTkinter | Telas, navegação, modo scanner; **composition root** que liga serviços ao adaptador SQLite | Regra de negócio (fica no núcleo) | M3 |
| Arquivo `.db` | SQLite (`sqlite3`), WAL, `foreign_keys=ON` | Persistir itens, locais, partes, lotes e o livro de movimentações; migrações por `PRAGMA user_version` | Guardar saldo como verdade (ADR-004) | M2 |
| Núcleo (`core`) | Python puro, sem dependências | Domínio, invariantes, casos de uso e portas (`Protocol`) | Importar banco, UI, framework ou rede (import-linter) | M1 |
| SPA | React + TypeScript, Vite, TanStack Query | Interface web com os mesmos fluxos do desktop | Regra de negócio; acesso direto ao banco | M6 |
| API | Django 5.2 LTS + DRF, drf-spectacular, WhiteNoise | Autenticação e papéis, endpoints finos sobre o núcleo, erros padronizados, OpenAPI; serve o build da SPA | Regra em models, signals ou serializers (ADR-003) | M5 |
| Banco da web | SQLite (local/demo); Postgres se houver uso real | Mesmo modelo de dados, via Django ORM | — | M5 |

## Adaptadores (dentro dos containers)

| Adaptador | Implementa as portas para | Roda em | Garantia de equivalência |
|---|---|---|---|
| `adapters/memory` | Testes do núcleo | pytest | Referência da suíte de contrato (M1.5) |
| `adapters/sqlite` | Desktop (ADR-002) | App desktop | Suíte de contrato (M2.6) |
| `adapters/django_orm` | Web (ADR-003) | API | Suíte de contrato (M5.3) e paridade com JSON dourado (M5.10) |

## Variações de execução

- **Vitrine estática (M7.4):** o build da SPA publicado no GitHub Pages fala com uma **API simulada** (MSW) no próprio
  navegador, sem API nem banco reais.
- **Demo online (M7.3):** API + SPA num plano gratuito, banco recriado com o dataset de referência a cada boot.
- **Sem sincronização:** não há ligação entre `Arquivo .db` e `Banco da web` (P-05, B-01). A igualdade de
  comportamento é provada por testes (RNF-004), não por troca de dados.
