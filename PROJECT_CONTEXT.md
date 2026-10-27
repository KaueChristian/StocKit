# PROJECT_CONTEXT — Gerenciador de estoque universal (desktop + web)

> **Arquivo-chefe do projeto.** É a fonte única de verdade sobre o *quê*, o *porquê*, o *como* e o *em que ponto estamos*.
> Dita o ritmo (roadmap em milestones com portão de integridade), a ideia, as ferramentas, os logs de alteração, os bugs
> encontrados e os planos descartados (com o motivo). Se código, documentação e este arquivo discordarem, **a discrepância
> é um bug de processo**: resolva e registre em §14 (diário).
> Nome: **StocKit** (definido na M0.1 — §19, D-01). Criado em 2026-10-27, em `Downloads`; desde a M0.1 vive na **raiz do
> repositório** `C:\Users\Desenvolvedor\Documents\port\StocKit`.
> Modelos usados como base: `project_context.md` do Anatomia 3D (fases, IDs, definição de pronto, registro de decisões) e
> `DOCUMENTO_CHEFE_140388.md` (protocolo de iteração, diário de erros, ideias descartadas).

---

## 0. Como usar este documento (leia primeiro, toda iteração)

**Ao começar uma iteração**
1. Leia as seções 0, 1 (estado atual), 10 (roadmap — só o milestone aberto), 15 (bugs abertos) e 16 (descartados).
   **Não proponha de novo nada que esteja em §16.**
2. Se algo no repositório contradiz este arquivo, o provável é que o código ou o ambiente mudou: re-verifique antes de
   "corrigir" o documento às cegas.
3. Escolha **uma** etapa do milestone aberto (a de menor ID cujos pré-requisitos estejam cumpridos). Nunca pule para um
   milestone seguinte sem o portão do anterior aprovado (ou sem decisão registrada em §19 explicando o desvio).

**Ao terminar uma iteração (obrigatório, mesmo se nada deu certo)**
1. Atualize o painel de §1 (milestone aberto, última etapa concluída, próxima etapa, bloqueios).
2. Marque o status da etapa em §10 (`⬜` → `🔄` → `✅` / `⛔` bloqueada / `🗑️` descartada).
3. Acrescente uma linha em §14 (diário): **data · o que foi feito/tentado · resultado · causa · lição**. Registre também o
   que falhou, com o mesmo cuidado dos acertos.
4. Bug achado → §15. Ideia rejeitada → §16 **com o motivo**. Dúvida que depende do usuário → §18. Decisão tomada → §19
   (e ADR em `docs/adr/` se for arquitetural).
5. Se mediu algo, registre em §13 (número sem condição de medição não entra).
6. Marque o que é **fato verificado** e o que é **hipótese**. Nunca escreva hipótese como fato.
7. Se a etapa mudou comportamento: atualizar requisito (§8), teste vinculado e a documentação em `docs/` **no mesmo commit**.

**Regras inegociáveis**
- **O `core` é Python puro.** Não importa Tkinter, Django, `sqlite3` nem nada de I/O. Vigiado pelo `import-linter` no CI.
- **Estoque é derivado de movimentações imutáveis.** Saldo nunca é coluna editável. Correção = movimento de ajuste.
- **Regra de negócio vive em `core/services`.** Telas do Tkinter, views do DRF e componentes React só orquestram e exibem.
- **Duas plataformas, um comportamento.** Qualquer divergência de resultado entre desktop e web é bug (teste de paridade, M5).
- **Sem milestone fechado sem portão.** O conjunto de melhorias do milestone só conta como entregue depois do plano de
  teste do portão executado e registrado (§9, §11).
- **Meça antes de otimizar; uma hipótese por vez.** Sem causa raiz, sem correção. Três correções seguidas falhando para o
  mesmo bug → pare e reavalie a hipótese (disciplina da skill *systematic-debugging*).
- **Publicar é um ato deliberado.** Sem `push`, release, tag, deploy nem PR sem o usuário pedir naquela ação.
- **Commits** no padrão Conventional Commits (`feat(core): ...`, `fix(desktop): ...`, `docs: ...`), um assunto por commit.
- **Sem dados reais de terceiros** no repositório; dados de demonstração são gerados com semente fixa.

---

## 1. Painel de estado (atualizar a cada iteração)

| Campo | Valor |
|---|---|
| Milestone aberto | **M0 — Fundação** |
| Última etapa concluída | **M0.2** — `pyproject.toml`, `core` instalável em modo editável, venv, versões fixadas (2026-10-27) |
| Próxima etapa | **M0.3** — ruff, mypy (estrito no `core`), pytest, pytest-cov, hypothesis, pre-commit, `make check` |
| Bloqueios | Nenhum |
| Último portão aprovado | — |
| Versão | 0.0.0 (nada publicado) |
| Bugs abertos | 0 |

---

## 2. Identificação

| Item | Valor |
|---|---|
| Projeto | Gerenciador de estoque **universal**, em duas plataformas com o mesmo núcleo |
| Responsável | Dono do portfólio `kauechristian.github.io` (GitHub: `KaueChristian`) |
| Origem | Card "Inventory Manager" do portfólio, que ainda **não tem código** (confirmado em 2026-10-27) |
| Objetivo | Projeto de portfólio que demonstra arquitetura, regra de negócio, testes e documentação alinhados |
| Plataformas | **Desktop**: Tkinter + SQLite · **Web**: Django + DRF + React (TypeScript) |
| Servidor dedicado | **Não**. Desktop roda local; web roda local (docker/script) ou em plano gratuito só para demo (§5.3) |
| Licença | MIT (proposta, D-05) |
| Idioma | Interface e docs em PT-BR; identificadores de código em inglês |

---

## 3. Visão, público e escopo

**Visão.** Um sistema de estoque que não é "mais um CRUD de produtos": o saldo vem de um livro de movimentações, o sistema
ajuda a **decidir** (reposição, curva ABC, previsão de ruptura, validade) e funciona para **qualquer negócio** (varejo,
cozinha, oficina, TI, ateliê), configurando vocabulário, campos e unidades por **perfil**, sem mexer em código.

**Público.** (1) Recrutadores e tech leads que abrirão o repositório/portfólio; (2) pequenos negócios que precisam de controle
simples e confiável, sem servidor.

**O que já nos diferencia e deve ser preservado:** domínio universal (perfis), livro imutável + auditoria, inteligência de
reposição, mesmo comportamento garantido em duas plataformas por testes de contrato e de paridade, e documentação viva
(ADRs, rastreabilidade requisito ↔ teste, OpenAPI gerado).

**Não é (fora de escopo):** ERP/financeiro/fiscal (NF-e, impostos), PDV, multiempresa SaaS, app móvel nativo, ferramenta
de contabilidade. **Sincronização desktop ↔ web** não está no escopo inicial (§12 e §16).

---

## 4. Princípios e restrições (valem para todos os milestones)

1. **Correção antes de recurso.** Saldo errado é o pior bug possível; invariantes têm teste de propriedade (hypothesis).
2. **Núcleo sem framework.** Portas (`Protocol`) no `core`; adaptadores fora. Trocar SQLite por outro banco não toca em regra.
3. **Universal por configuração, não por código.** Nenhuma palavra de nicho no `core` (nada de "serviço", "paciente",
   "prato"). Vocabulário e campos extras vêm de perfis (JSON) e de definições de campos personalizados.
4. **Aritmética decimal.** `Decimal` em quantidades e custos; nunca `float` em dinheiro ou saldo.
5. **Datas e fusos.** Tudo em UTC no armazenamento; relógio injetável (`Clock`) para testes determinísticos.
6. **Offline primeiro no desktop.** Sem rede, sem conta, um arquivo `.db` que o usuário pode copiar.
7. **Dados de demonstração determinísticos.** Gerador com semente fixa; os números dourados dos testes dependem dele.
8. **Acessibilidade e usabilidade desde o início:** teclado em todas as telas, contraste AA, foco visível.
9. **Documento e código andam juntos.** Mudou comportamento → muda requisito, teste e doc no mesmo commit (§0.7).
10. **Segurança básica por padrão** na web: authz por papel, CSRF, throttling, sem segredos no repositório.

---

## 5. Ambiente e ferramentas

### 5.1 Máquina de desenvolvimento
- Windows 11, PowerShell/Git Bash. Pasta do projeto: `C:\Users\Desenvolvedor\Documents\port\StocKit` (D-06, M0.1).
- **Instalado na máquina (fato, verificado em 2026-10-27):** Git 2.56.0.windows.2, Python 3.14.3 (também há 3.12.10),
  Node v24.14.1, Tk 8.6.
- **Versões fixadas na M0.2 (D-04, 2026-10-27):**

| Componente | Versão | Onde está fixada | Verificação |
|---|---|---|---|
| Python | 3.14 (`>=3.14,<3.15`) | `pyproject.toml`, `.python-version` | Instalado; venv criado com 3.14.3 |
| Node | 24 (LTS) | `.nvmrc` | Instalado (v24.14.1); usado a partir da M6 |
| pip (venv) | 26.2.2 | README (passo de setup) | Instalado no venv |
| setuptools (build) | 84.2.1 | `pyproject.toml` `[build-system]` | Instalação editável ok |
| Django | 5.2.18 (LTS) | extra `web` | PyPI declara Python 3.14 (fato). Não instalado ainda (M5). 6.1.2 existe, mas não é LTS |
| Django REST Framework | 3.18.3 | extra `web` | PyPI declara Python 3.14 (fato). Não instalado (M5) |
| CustomTkinter | 6.0.0 | extra `desktop` | Testado em venv descartável no 3.14.3: janela abre e fecha sem erro (fato) |
| PyInstaller | 6.22.3 | extra `package` | PyPI declara Python 3.14 (fato). Não testado (M3.12) |
| React / Vite / TypeScript | — | — | Fixar na M6.1 |

- Ferramentas de qualidade (ruff, mypy, pytest...) entram com versão fixa na M0.3.
- *Pendente:* dependências **transitivas** ainda não têm lock (ex.: `darkdetect`, `asgiref`). Avaliar lockfile
  (pip-tools/uv) antes de instalar os extras (M3/M5) para cumprir RNF-006 por completo.

### 5.2 Stack e ferramentas

| Camada | Escolha | Papel |
|---|---|---|
| Linguagem | Python (versão a fixar) | `core`, desktop, backend |
| Desktop | Tkinter (CustomTkinter — D-03) | UI, padrão MVP com views passivas |
| Banco desktop | SQLite (`sqlite3` da stdlib) | WAL, `foreign_keys=ON`, migrações por `PRAGMA user_version` |
| Backend | Django + Django REST Framework | Adaptador ORM + API fina |
| OpenAPI | drf-spectacular | Documentação da API gerada do código |
| Frontend | React + TypeScript + Vite, TanStack Query | SPA; cliente tipado gerado do OpenAPI |
| Qualidade | ruff, mypy, pytest, hypothesis, pytest-cov, pre-commit | Lint, tipos, testes |
| Arquitetura | import-linter | Falha o CI se o `core` importar camada externa |
| Testes web | pytest-django, Vitest, Testing Library, Playwright | API, componentes, E2E |
| Relatórios | reportlab (PDF), `qrcode`/`python-barcode` | Relatórios e etiquetas |
| Dados demo | Faker (semente fixa) | Dataset de referência |
| Empacotamento | PyInstaller (desktop), Docker Compose + WhiteNoise (web) | Entrega sem servidor dedicado |
| CI | GitHub Actions | Lint, tipos, testes, build do frontend |
| Docs | Markdown + Mermaid (C4, ER) em `docs/` | Documentação como código |

### 5.3 Modos de execução (sem servidor dedicado)

| Plataforma | Como roda | Servidor? |
|---|---|---|
| Desktop | Arquivo `.db` local, `.exe` via PyInstaller | Nenhum |
| Web, uso local | `docker compose up` ou script que sobe o Django servindo o build do React (WhiteNoise) | Sua máquina |
| Web, demo online | Plano gratuito de PaaS (Render, Fly.io, PythonAnywhere), com modo demo recriado a cada boot | Compartilhado. **Confira as condições atuais; não usar para dados reais** |
| Vitrine estática | React no GitHub Pages falando com API simulada (MSW) | Nenhum |

### 5.4 Repositório e fluxo
- Branches: `main` (estável, publicável) e `dev` (trabalho). Cada milestone sai de `dev` para `main` **só após o portão**.
- Convenção de tags: `v0.<milestone>.0` ao fechar cada milestone (ex.: `v0.3.0` = desktop MVP).

---

## 6. Arquitetura

### 6.1 Visão (hexagonal: um núcleo, duas interfaces)

```
StocKit/
├─ PROJECT_CONTEXT.md          este arquivo (raiz)
├─ docs/                       adr/, c4/, requirements.md, glossary.md, test-plan/, api/
├─ core/                       Python puro (instalável em modo editável)
│   ├─ domain/                 entidades, value objects, erros de domínio
│   ├─ services/               casos de uso (registrar_movimento, curva_abc, ...)
│   └─ ports/                  Protocols: repositórios, UnitOfWork, Clock
├─ adapters/
│   ├─ memory/                 repositórios em memória (testes do core)
│   ├─ sqlite/                 repositórios para o desktop
│   └─ django_orm/             repositórios para a web
├─ apps/
│   ├─ desktop/                Tkinter: views passivas + presenters testáveis
│   └─ web/{backend,frontend}/ Django+DRF / React+Vite+TS
├─ profiles/                   perfis JSON (varejo, cozinha, oficina, TI)
├─ tools/                      geração de dados demo, rastreabilidade, scripts
└─ tests/                      core/, contract/, parity/, desktop/, api/
```

### 6.2 Regras de dependência (fiscalizadas por `import-linter`)
- `core` **não** importa `adapters`, `apps`, `tkinter`, `django`, `sqlite3`, `reportlab`.
- `adapters` importam `core.ports`/`core.domain`; nunca `apps`.
- `apps` importam `core.services` e um adaptador; nunca outro `app`.
- Views DRF e presenters Tkinter **não contêm regra**: chamam serviço, traduzem erro de domínio, formatam saída.

### 6.3 Persistência dupla e como mantê-la honesta
Há dois adaptadores (SQLite puro e Django ORM) para as mesmas portas. A defesa é a **suíte de contrato**: os mesmos testes
rodam parametrizados contra memória, SQLite e Django ORM. A **suíte de paridade** (M5) roda o mesmo cenário do dataset de
referência nas duas plataformas e compara os saldos com um JSON dourado.
*Plano B (não descartado, D-02):* o desktop usar o Django ORM sem servidor (`django.setup()` sem `runserver`), com schema
único e migrações compartilhadas. Custo: executável mais pesado e fuga da stack "Tkinter + SQLite puro".

### 6.4 Padrão de UI no desktop
MVP: **views passivas** (só widgets), **presenters** com a lógica de tela, testáveis sem abrir janela. O smoke test
dirige a interface real com `event_generate`/`invoke`.

---

## 7. Domínio universal

### 7.1 Entidades

| Entidade | Resumo |
|---|---|
| **Item** | `sku`, nome, tipo (revenda, consumível, ativo, serializado), categoria, unidade base, flags (`controla_lote`, `controla_validade`), ponto de reposição, campos personalizados (JSON) |
| **UnidadeDeMedida** | Símbolo, grandeza e **conversões** (caixa → 12 un; L → mL) |
| **Local** | Hierárquico (depósito › corredor › prateleira); um item tem saldo por local |
| **Parte** | Fornecedor, cliente ou setor (papel configurável) |
| **Lote** | Código, validade, item; usado por FEFO |
| **Movimentação** | Livro **imutável**: entrada, saída, transferência, ajuste, perda, devolução; carrega item, local, lote, quantidade, custo unitário, motivo, autor, `ocorreu_em` |
| **CampoPersonalizado** | Definição (nome, tipo, obrigatório, validação) por tipo de item |
| **Perfil** | JSON que pré-configura rótulos, campos e unidades de um tipo de negócio |
| **Contagem** | Inventário cíclico: contado × sistema → divergência → movimentos de ajuste |

### 7.2 Invariantes (cada uma tem teste de propriedade)
- INV-01 Saldo de (item, local, lote) = soma assinada das movimentações; nunca armazenado como verdade.
- INV-02 Movimentação nunca é alterada ou apagada (trigger no SQLite, ausência de update/delete no repositório).
- INV-03 Transferência é um par atômico (saída + entrada) e conserva a quantidade total.
- INV-04 Conversão de unidade ida e volta preserva o valor (com `Decimal` e arredondamento definido).
- INV-05 Saldo negativo só ocorre se a política do sistema permitir (padrão: proibido).
- INV-06 Saída de item com lote segue FEFO quando o lote não é informado.
- INV-07 Item serializado nunca tem saldo fracionário nem número de série repetido.
- INV-08 Soma dos saldos por local = saldo total do item.

### 7.3 Valoração do estoque
Padrão proposto: **custo médio móvel** (D-07). FIFO fica como política opcional posterior. Decisão pendente em §18.

---

## 8. Requisitos (rastreáveis)

> Cada RF/RNF tem ID, milestone-alvo e **pelo menos um teste** marcado com `@pytest.mark.req("RF-xxx")` (ou equivalente no
> Vitest/Playwright). O script de rastreabilidade (M0.9) gera a matriz requisito × teste × status.

| ID | Requisito | Milestone |
|---|---|---|
| RF-001 | Cadastrar, editar, inativar e buscar itens | M1/M3/M6 |
| RF-002 | Cadastrar hierarquia de locais | M1/M3/M6 |
| RF-003 | Cadastrar partes (fornecedor/cliente/setor) | M1/M3/M6 |
| RF-004 | Definir campos personalizados por tipo de item e validá-los | M1/M3/M6 |
| RF-005 | Registrar entrada, saída, transferência, ajuste e perda | M1/M3/M6 |
| RF-006 | Calcular saldo por item, local e lote, inclusive "em uma data" | M1 |
| RF-007 | Impedir saldo negativo conforme política configurável | M1 |
| RF-008 | Controlar lote e validade com saída FEFO | M1 |
| RF-009 | Itens serializados (unidade única, estado) | M1 |
| RF-010 | Conversão entre unidades de medida | M1 |
| RF-011 | Carregar perfis (varejo, cozinha, oficina, TI) | M1/M3 |
| RF-012 | Histórico/extrato imutável por item com filtros | M3/M6 |
| RF-013 | Migrações de schema versionadas e reversíveis a partir de banco antigo | M2 |
| RF-014 | Backup/restauração do banco com verificação de integridade | M2/M3 |
| RF-015 | Importar/exportar itens e movimentações em CSV com relatório de erros por linha | M3/M5/M6 |
| RF-016 | Dashboard com KPIs e alertas | M3/M6 |
| RF-017 | Registrar movimentação via leitor de código de barras (modo scanner) | M3/M6 |
| RF-018 | Ponto de reposição e estoque de segurança por item | M4 |
| RF-019 | Alertas: abaixo do mínimo, a vencer, sem giro | M4 |
| RF-020 | Curva ABC por período | M4 |
| RF-021 | Giro e cobertura em dias | M4 |
| RF-022 | Previsão de ruptura com indicação de confiança | M4 |
| RF-023 | Sugestão de compra por fornecedor | M4 |
| RF-024 | Inventário cíclico com geração de ajustes | M4 |
| RF-025 | Relatórios em PDF e etiquetas com QR/código de barras | M4 |
| RF-026 | API REST documentada (OpenAPI) com autenticação e papéis | M5 |
| RF-027 | Interface web com os mesmos fluxos do desktop | M6 |
| RF-028 | Modo demonstração com dados determinísticos | M2/M7 |
| RNF-001 | Cobertura de testes do `core` ≥ 90% (linhas) | M1 em diante |
| RNF-002 | Saldo de item calculado em < 100 ms com 100 mil movimentações (meta inicial; recalibrar com medição) | M2/M4 |
| RNF-003 | Abertura do desktop em < 3 s com o dataset demo (meta inicial) | M3 |
| RNF-004 | Paridade: mesmo dataset ⇒ mesmos saldos nas duas plataformas | M5 |
| RNF-005 | Acessibilidade: operação completa por teclado; contraste AA | M3/M6 |
| RNF-006 | Nenhum segredo no repositório; dependências com versão fixa | M0 em diante |

---

## 9. Estratégia de testes e portões de integridade

### 9.1 O conceito de milestone neste projeto
**Milestone = um conjunto de etapas (melhorias) que, somadas, justificam um teste de integridade; ele só fecha depois do
portão.** O portão é a execução do *plano de teste do milestone* (§10, bloco "Portão") mais a regressão dos portões
anteriores. Se um milestone crescer a ponto de passar de ~12 etapas ou de mudar de natureza no meio, **divida-o** (ex.:
M3a/M3b), cada metade com seu portão, e registre em §19.

### 9.2 Camadas de teste

| Camada | Ferramenta | O que prova | Roda em |
|---|---|---|---|
| Unitário do core | pytest + hypothesis | Regras e invariantes, sem I/O | Toda mudança (pré-commit/CI) |
| Contrato de repositório | pytest parametrizado | Memória, SQLite e Django ORM se comportam igual | CI |
| Migração | pytest | Banco vazio → vN e v1 → vN preservam dados | CI |
| Presenter (desktop) | pytest | Lógica de tela sem janela | CI |
| Smoke de UI (desktop) | pytest + `event_generate` | Abrir, navegar, registrar movimento, fechar sem erro | CI (headless quando possível) / portão |
| API | pytest-django + APIClient | Contrato HTTP, authz, erros padronizados | CI |
| Componente (web) | Vitest + Testing Library | Telas isoladas | CI |
| E2E (web) | Playwright | Fluxos críticos reais | Portão M6 em diante |
| Paridade | pytest | Mesmo cenário ⇒ mesmo JSON dourado nas duas plataformas | Portão M5 em diante |
| Desempenho | script em `tools/` | Metas RNF-002/003, registradas em §13 | Portões M2, M3, M4 |
| Exploratório manual | roteiro em `docs/test-plan/` | Usabilidade e o que a automação não vê | Portões M3, M6, M7 |

### 9.3 Regras do portão
1. **Portão = caso a caso.** Cada caso tem ID `TP-M<n>-<nn>`, pré-condição, passos, resultado esperado, evidência e status.
2. **Críticos** (marcados ★) precisam passar 100% para fechar o milestone. Falha não crítica vira bug em §15 com prazo,
   e o milestone fecha *com ressalva* registrada.
3. **Regressão acumulada:** o portão de M*n* inclui os casos críticos de M0..M*n-1* (automatizados: sempre; manuais: os ★).
4. **Execução registrada** em §11 (data, commit, casos, falhas, decisão go/no-go). Sem registro, o portão não aconteceu.
5. **Dataset de referência** (M2.7) é a base de todos os números dourados; mudar o gerador exige regenerar e justificar.
6. **Definição de pronto de uma etapa:** código com teste, requisito referenciado, doc atualizada, `make check` (ruff +
   mypy + pytest + import-linter) verde, entrada no diário (§14).

---

## 10. Roadmap por milestones

Legenda: ⬜ não iniciado · 🔄 em andamento · ✅ concluído · ⛔ bloqueado · 🗑️ descartado.
Tamanhos: **P** ≤ 1 dia · **M** 2–4 dias · **G** 1–2 semanas (estimativas iniciais; recalibrar com §13).
Ordem de execução = ordem de leitura. IDs de etapa (`M3.4`) são para commits, issues e conversas.

---

### M0 — Fundação · tamanho M · `v0.0.x`
**Objetivo:** poder evoluir rápido sem perder o alinhamento entre código, doc e processo.

| ID | Etapa | Tam. | Status |
|---|---|---|---|
| M0.1 | Criar repositório (pasta definida em D-06), `git init`, branches `main`/`dev`, `.gitignore`, LICENSE (D-05), README mínimo; **mover este arquivo para a raiz** | P | ✅ |
| M0.2 | `pyproject.toml` com `core` instalável em modo editável; venv; **fixar versões** de Python/Node/Django e registrar em §5.1 | P | ✅ |
| M0.3 | Ferramentas: ruff, mypy (estrito no `core`), pytest, pytest-cov, hypothesis, pre-commit; alvo único `make check` (ou script equivalente no Windows) | P | ⬜ |
| M0.4 | Contratos do `import-linter` (`core` não importa adaptadores/apps/frameworks) | P | ⬜ |
| M0.5 | CI no GitHub Actions: lint, tipos, testes, import-linter em push na `dev` e PRs | P | ⬜ |
| M0.6 | `docs/`: estrutura, glossário (§20), `requirements.md` (a partir de §8), template de ADR e **ADRs 001–005** (núcleo hexagonal; SQLite no desktop; Django ORM na web; livro de movimentações; campos personalizados em JSON) | M | ⬜ |
| M0.7 | Diagramas C4 níveis 1–2 em Mermaid (`docs/c4/`) | P | ⬜ |
| M0.8 | Template de PR (checklist de §9.3.6), templates de issue, `CONTRIBUTING.md` curto | P | ⬜ |
| M0.9 | Marker `req` no pytest + script `tools/traceability.py` que gera a matriz requisito × teste × status | M | ⬜ |
| M0.10 | Teste "sentinela" do import-linter (prova que um import proibido quebra o CI) e teste dummy anotado com `req` | P | ⬜ |

**Portão M0 — plano de teste**

| Caso | Descrição | Esperado |
|---|---|---|
| TP-M0-01 ★ | Clone limpo → criar venv → instalar → `make check` | Verde, sem passo manual não documentado |
| TP-M0-02 ★ | Introduzir `import tkinter` em `core/` | `import-linter` falha; CI falha |
| TP-M0-03 ★ | Abrir PR de teste na `dev` | CI executa e reporta |
| TP-M0-04 | Mermaid dos C4 renderiza no GitHub | Diagramas visíveis |
| TP-M0-05 ★ | `tools/traceability.py` | Gera matriz com o teste dummy ligado a um RF |
| TP-M0-06 | Todos os ADRs 001–005 existem e seguem o template | Revisão manual |

**Saída:** portão aprovado, `v0.0.1` marcado, §1 e §14 atualizados.

---

### M1 — Núcleo de domínio · tamanho G · `v0.1.0`
**Objetivo:** todas as regras do estoque funcionando em memória, sem banco e sem tela.

| ID | Etapa | Tam. | Status |
|---|---|---|---|
| M1.1 | Value objects: `Quantity` (`Decimal` + unidade), `UnidadeDeMedida` e conversões (INV-04) | M | ⬜ |
| M1.2 | Entidades `Item`, `Categoria`, `Local` (hierarquia), `Parte` com validações | M | ⬜ |
| M1.3 | `Movimentacao` imutável e tipos (entrada, saída, transferência, ajuste, perda, devolução) | M | ⬜ |
| M1.4 | Portas: repositórios, `UnitOfWork`, `Clock` (`Protocol`) | P | ⬜ |
| M1.5 | Repositórios **em memória** (`adapters/memory`) usados pelos testes | M | ⬜ |
| M1.6 | Serviço `registrar_movimento` com política de saldo negativo (INV-05) e atomicidade via UoW | M | ⬜ |
| M1.7 | Serviço de saldo por item/local/lote e **saldo em uma data** (INV-01, INV-08) | M | ⬜ |
| M1.8 | Transferência atômica (INV-03) | P | ⬜ |
| M1.9 | Lotes e validade; **FEFO** na saída sem lote informado (INV-06) | M | ⬜ |
| M1.10 | Itens serializados (INV-07) | P | ⬜ |
| M1.11 | Campos personalizados: definição, tipos, validação no `Item` | M | ⬜ |
| M1.12 | Configuração do sistema (políticas) e **loader de perfis** com validação por JSON Schema; perfis iniciais (varejo, cozinha, oficina, TI) | M | ⬜ |
| M1.13 | Hierarquia de erros de domínio tipados (base para mapear em UI e API) | P | ⬜ |
| M1.14 | Valoração por custo médio móvel (D-07) | M | ⬜ |

**Portão M1 — plano de teste**

| Caso | Descrição | Esperado |
|---|---|---|
| TP-M1-01 ★ | Propriedade: sequência aleatória de movimentos válidos | Saldo == soma assinada (INV-01) |
| TP-M1-02 ★ | Propriedade: transferências aleatórias | Quantidade total conservada (INV-03, INV-08) |
| TP-M1-03 ★ | Conversão ida e volta em unidades variadas | Sem perda além do arredondamento definido (INV-04) |
| TP-M1-04 ★ | Saída acima do saldo com política "proibir" e com "permitir" | Erro de domínio / saldo negativo conforme política |
| TP-M1-05 ★ | FEFO com 3 lotes de validades distintas | Consome na ordem de validade; lote vencido sinalizado |
| TP-M1-06 | Item serializado: número de série repetido; quantidade fracionária | Erro de domínio |
| TP-M1-07 ★ | Campo personalizado obrigatório ausente / tipo inválido | Erro de domínio com mensagem identificável |
| TP-M1-08 | Carregar os 4 perfis; perfil inválido | Válidos carregam; inválido rejeitado com motivo |
| TP-M1-09 ★ | Custo médio móvel: entradas a custos diferentes e saída | Valor igual ao calculado à mão (planilha anexa em `docs/test-plan/`) |
| TP-M1-10 ★ | Cobertura do `core` | ≥ 90% (RNF-001) |
| TP-M1-11 | Regressão do portão M0 | Verde |

**Saída:** portão aprovado, `v0.1.0`, ADRs novos registrados, requisitos RF-004..RF-011 com teste vinculado.

---

### M2 — Persistência SQLite · tamanho G · `v0.2.0`
**Objetivo:** o núcleo persiste num arquivo `.db` com garantias e é provado equivalente à versão em memória.

| ID | Etapa | Tam. | Status |
|---|---|---|---|
| M2.1 | Runner de migrações (`PRAGMA user_version`) e schema inicial em SQL numerado | M | ⬜ |
| M2.2 | Fábrica de conexão: `foreign_keys=ON`, `journal_mode=WAL`, `busy_timeout`, `row_factory` | P | ⬜ |
| M2.3 | Repositórios SQLite: item, local, parte, lote, movimentação | G | ⬜ |
| M2.4 | Movimentação **append-only** no banco (triggers que bloqueiam UPDATE/DELETE) — INV-02 | P | ⬜ |
| M2.5 | `UnitOfWork` transacional (commit/rollback) | M | ⬜ |
| M2.6 | **Suíte de contrato** parametrizada (memória × SQLite) cobrindo as portas inteiras | M | ⬜ |
| M2.7 | Dataset de referência: gerador determinístico (Faker, semente fixa), 6 meses de histórico; JSON dourado de saldos | M | ⬜ |
| M2.8 | Índices e visões de saldo; medição de desempenho (RNF-002) registrada em §13 | M | ⬜ |
| M2.9 | Backup/restauração (API de backup do SQLite) e `PRAGMA integrity_check` | P | ⬜ |
| M2.10 | Diagrama ER (Mermaid) e documentação do schema | P | ⬜ |

**Portão M2 — plano de teste**

| Caso | Descrição | Esperado |
|---|---|---|
| TP-M2-01 ★ | Suíte de contrato nos dois adaptadores | 100% verde, mesmos resultados |
| TP-M2-02 ★ | Banco vazio → última versão; banco v1 → última | Estrutura correta; dados da v1 preservados |
| TP-M2-03 ★ | Falha injetada no meio de uma transferência | Rollback completo; nenhuma meia-movimentação |
| TP-M2-04 ★ | UPDATE/DELETE direto em movimentação | Banco rejeita (INV-02) |
| TP-M2-05 ★ | Dataset demo gerado duas vezes com a mesma semente | Bytes/JSON dourado idênticos |
| TP-M2-06 | Backup → restaurar → comparar saldos; `integrity_check` | Idênticos; `ok` |
| TP-M2-07 | Desempenho: saldo de item com 100 mil movimentos | Dentro da meta (RNF-002) ou meta recalibrada e justificada |
| TP-M2-08 | Regressão M0–M1 | Verde |

**Saída:** portão aprovado, `v0.2.0`, números de desempenho em §13.

---

### M3 — Desktop MVP · tamanho G · `v0.3.0`
**Objetivo:** primeira entrega usável e bonita; o recrutador abre o `.exe`, vê dados demo e opera.

| ID | Etapa | Tam. | Status |
|---|---|---|---|
| M3.1 | Composition root, navegação por sidebar, tema claro/escuro, strings externalizadas (pt-BR) | M | ⬜ |
| M3.2 | Itens: lista, busca, filtros, formulário com campos personalizados dinâmicos (RF-001, RF-004) | G | ⬜ |
| M3.3 | Locais (árvore) e partes | M | ⬜ |
| M3.4 | Tela de movimentação: entrada, saída, transferência, ajuste, perda, com validação e feedback | G | ⬜ |
| M3.5 | **Modo scanner**: campo sempre focado, Enter confirma, feedback visual/sonoro (RF-017) | M | ⬜ |
| M3.6 | Extrato do item (ledger) com filtros e exportação | M | ⬜ |
| M3.7 | Dashboard v1: KPIs (itens, valor em estoque, abaixo do mínimo) e um gráfico | M | ⬜ |
| M3.8 | Importar/exportar CSV com pré-visualização e relatório de erros por linha (RF-015) | M | ⬜ |
| M3.9 | Primeiro uso: escolha de perfil; **modo demo** (RF-028); backup pela interface (RF-014) | M | ⬜ |
| M3.10 | Paleta de comandos `Ctrl+K` e atalhos de teclado (RNF-005) | M | ⬜ |
| M3.11 | Presenters com teste e smoke test de UI | M | ⬜ |
| M3.12 | Empacotamento PyInstaller e teste em ambiente sem Python instalado | M | ⬜ |

**Portão M3 — plano de teste**

| Caso | Descrição | Esperado |
|---|---|---|
| TP-M3-01 ★ | Smoke de UI: abrir, navegar por todas as telas, fechar | Zero exceções |
| TP-M3-02 ★ | Fluxo completo: criar item → entrada → saída → conferir saldo e extrato | Saldo da tela == saldo do serviço == soma do extrato |
| TP-M3-03 ★ | Saída acima do saldo | Mensagem clara; nada gravado |
| TP-M3-04 ★ | Importar CSV com 3 linhas inválidas entre 100 | 97 importadas; relatório indica linha e motivo das 3 |
| TP-M3-05 ★ | Operação completa só pelo teclado (inclui scanner simulado) | Possível sem mouse (RNF-005) |
| TP-M3-06 | Tema claro/escuro e redimensionamento | Sem corte nem texto ilegível |
| TP-M3-07 ★ | `.exe` em máquina/venv limpa, com dataset demo | Abre; abertura < 3 s (RNF-003) ou meta recalibrada |
| TP-M3-08 | Roteiro exploratório de 20 min (checklist em `docs/test-plan/`) | Achados viram bugs em §15 |
| TP-M3-09 ★ | Regressão M0–M2 | Verde |

**Saída:** portão aprovado, `v0.3.0`, GIFs para o README, manual curto.

---

### M4 — Inteligência de estoque · tamanho G · `v0.4.0`
**Objetivo:** o diferencial do projeto: o sistema ajuda a decidir.

| ID | Etapa | Tam. | Status |
|---|---|---|---|
| M4.1 | Ponto de reposição e estoque de segurança (consumo médio × lead time + segurança), configuráveis por item | M | ⬜ |
| M4.2 | Alertas: abaixo do mínimo, a vencer, sem giro | M | ⬜ |
| M4.3 | Curva ABC por período configurável | M | ⬜ |
| M4.4 | Giro e cobertura em dias | P | ⬜ |
| M4.5 | Previsão de ruptura (média móvel; regressão linear opcional) com **indicador de confiança** quando o histórico é curto | G | ⬜ |
| M4.6 | Sugestão de compra por fornecedor (EOQ opcional) | M | ⬜ |
| M4.7 | Inventário cíclico: contagem, divergência, geração de ajustes como movimentos | M | ⬜ |
| M4.8 | Telas no desktop (dashboard v2, alertas, ABC, sugestão de compra, contagem) | G | ⬜ |
| M4.9 | Relatórios em PDF e etiquetas com QR/código de barras | M | ⬜ |
| M4.10 | ADR dos algoritmos: fórmulas, premissas e limitações | P | ⬜ |

**Portão M4 — plano de teste**

| Caso | Descrição | Esperado |
|---|---|---|
| TP-M4-01 ★ | Cenários dourados calculados à mão (planilha anexa) para reposição, giro e cobertura | Resultado == planilha (tolerância declarada) |
| TP-M4-02 ★ | Propriedade: a curva ABC particiona 100% dos itens e é monotônica | Sem item fora das classes |
| TP-M4-03 ★ | Previsão com histórico < mínimo | Marca confiança baixa; nunca retorna valor negativo |
| TP-M4-04 ★ | Contagem com divergência | Gera movimentos de ajuste; saldo final == contado |
| TP-M4-05 ★ | Item sem consumo | Sem divisão por zero; cobertura "indefinida" tratada na UI |
| TP-M4-06 | PDF e etiqueta abrem e o código lido por leitor/app confere | QR/código == SKU |
| TP-M4-07 | Desempenho: ABC e previsão sobre o dataset demo | Dentro da meta registrada em §13 |
| TP-M4-08 ★ | Regressão M0–M3 | Verde |

**Saída:** portão aprovado, `v0.4.0`, ADR dos algoritmos publicado.

---

### M5 — Backend web · tamanho G · `v0.5.0`
**Objetivo:** a web tem o **mesmo** comportamento do desktop, provado por testes.

| ID | Etapa | Tam. | Status |
|---|---|---|---|
| M5.1 | Projeto Django (settings por ambiente, segredos fora do repo) e app `inventory` | M | ⬜ |
| M5.2 | Models e migrações Django; adaptador `django_orm` implementando as portas | G | ⬜ |
| M5.3 | **Suíte de contrato** rodando também contra `django_orm` (pytest-django) | M | ⬜ |
| M5.4 | DRF: endpoints finos que chamam `core.services`; paginação, filtros, ordenação | G | ⬜ |
| M5.5 | Autenticação e papéis (admin, operador, leitor) — ADR de sessão × token | M | ⬜ |
| M5.6 | Erros padronizados (problem+json) mapeados dos erros de domínio | P | ⬜ |
| M5.7 | OpenAPI (drf-spectacular) e teste que falha se o schema divergir do versionado | M | ⬜ |
| M5.8 | Endpoints de importação CSV, relatórios e inteligência (M4) | M | ⬜ |
| M5.9 | Execução local: Docker Compose / script; WhiteNoise; guia em `docs/` | M | ⬜ |
| M5.10 | **Teste de paridade**: dataset de referência nas duas plataformas ⇒ JSON dourado idêntico | M | ⬜ |

**Portão M5 — plano de teste**

| Caso | Descrição | Esperado |
|---|---|---|
| TP-M5-01 ★ | Contrato nos 3 adaptadores | 100% verde |
| TP-M5-02 ★ | Paridade: saldos, ABC e sugestão de compra do dataset demo | Idênticos ao dourado nas duas plataformas (RNF-004) |
| TP-M5-03 ★ | Authz: leitor tenta movimentar; anônimo acessa API | 403 / 401 |
| TP-M5-04 ★ | Erro de domínio (saldo negativo) via API | Resposta padronizada; nada gravado |
| TP-M5-05 ★ | Mudar endpoint sem atualizar o schema | Teste de OpenAPI falha |
| TP-M5-06 | Throttling e CSRF configurados | Verificados em teste |
| TP-M5-07 | `docker compose up` em máquina limpa | API responde; docs em `/api/docs` |
| TP-M5-08 ★ | Regressão M0–M4 | Verde |

**Saída:** portão aprovado, `v0.5.0`, OpenAPI publicado em `docs/api/`.

---

### M6 — Frontend web · tamanho G · `v0.6.0`
**Objetivo:** a mesma experiência de uso do desktop, no navegador.

| ID | Etapa | Tam. | Status |
|---|---|---|---|
| M6.1 | Vite + React + TS; cliente tipado gerado do OpenAPI; TanStack Query | M | ⬜ |
| M6.2 | Layout, rotas, tema claro/escuro, i18n pt-BR | M | ⬜ |
| M6.3 | Itens (lista, busca, formulário com campos personalizados dinâmicos) | G | ⬜ |
| M6.4 | Locais, partes e movimentação com modo scanner | G | ⬜ |
| M6.5 | Extrato, importação CSV com relatório de erros | M | ⬜ |
| M6.6 | Dashboard e telas de inteligência (ABC, alertas, previsão, compra, contagem) | G | ⬜ |
| M6.7 | Acessibilidade (teclado, foco, contraste AA) e responsivo | M | ⬜ |
| M6.8 | Testes de componente (Vitest) e E2E (Playwright) dos fluxos críticos | G | ⬜ |
| M6.9 | **Matriz de paridade funcional** desktop × web em `docs/` | P | ⬜ |

**Portão M6 — plano de teste**

| Caso | Descrição | Esperado |
|---|---|---|
| TP-M6-01 ★ | E2E: criar item → entrada → saída → extrato | Saldo na web == saldo da API == extrato |
| TP-M6-02 ★ | E2E: importação CSV com linhas inválidas | Relatório por linha |
| TP-M6-03 ★ | Matriz de paridade | Nenhuma função "só em uma plataforma" sem justificativa registrada |
| TP-M6-04 ★ | Operação por teclado e auditoria de acessibilidade | Sem violação grave (meta: Lighthouse a11y ≥ 90) |
| TP-M6-05 | Telas em 360 px, 768 px e 1440 px | Sem rolagem horizontal nem corte |
| TP-M6-06 | Roteiro exploratório de 20 min | Achados em §15 |
| TP-M6-07 ★ | Regressão M0–M5 | Verde |

**Saída:** portão aprovado, `v0.6.0`.

---

### M7 — Polimento e entrega · tamanho M · `v1.0.0`
**Objetivo:** transformar o projeto em vitrine de portfólio verificável.

| ID | Etapa | Tam. | Status |
|---|---|---|---|
| M7.1 | Modo demo nas duas plataformas (botão "carregar dados de exemplo") | P | ⬜ |
| M7.2 | Release do desktop: `.exe` em GitHub Releases, com checksum | M | ⬜ |
| M7.3 | Deploy da demo web em plano gratuito (reset a cada boot) | M | ⬜ |
| M7.4 | Vitrine estática (React + MSW) no GitHub Pages | M | ⬜ |
| M7.5 | README final: GIFs, diagrama, seção "decisões técnicas", matriz de rastreabilidade | M | ⬜ |
| M7.6 | Revisão de segurança (`security-review`) e de dependências | P | ⬜ |
| M7.7 | Revisão final de docs: ADRs, C4, ER, requisitos, glossário alinhados ao código | M | ⬜ |
| M7.8 | Card do portfólio atualizado (descrição, stack, links, screenshots) | P | ⬜ |

**Portão M7 — plano de teste**

| Caso | Descrição | Esperado |
|---|---|---|
| TP-M7-01 ★ | Regressão completa (todos os portões, automatizados) | Verde |
| TP-M7-02 ★ | Instalação do `.exe` em máquina sem Python | Funciona; checksum confere |
| TP-M7-03 ★ | Demo online: abrir link, carregar dados, registrar movimento | Funciona do zero |
| TP-M7-04 ★ | Matriz de rastreabilidade | 100% dos RF/RNF com teste ou justificativa |
| TP-M7-05 ★ | Varredura de segredos e dependências | Nada sensível; sem vulnerabilidade crítica conhecida |
| TP-M7-06 | Um terceiro segue o README do zero | Roda sem ajuda |

**Saída:** portão aprovado, `v1.0.0`, projeto publicado e linkado no portfólio.

---

## 11. Registro de execução dos portões

> Preencher ao rodar cada portão. Sem linha aqui, o portão não aconteceu.

| Data | Milestone | Commit/versão | Casos executados | Falhas (IDs) | Bugs abertos | Decisão |
|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — |

**Template de caso de teste manual** (usar em `docs/test-plan/`):
`ID · Título · Pré-condição · Passos · Resultado esperado · Evidência (print/log) · Status · Observações`.

---

## 12. Backlog pós-v1.0 (ideias vivas, fora do roadmap)

| ID | Ideia | Observação |
|---|---|---|
| B-01 | Sincronização desktop ↔ web (pacote de exportação/importação ou modo "conectado" via API) | Exige resolução de conflitos; adiado (ver §16, P-05) |
| B-02 | Leitura de código de barras pela câmera (web) | `BarcodeDetector` + fallback |
| B-03 | FIFO como política de valoração | Depois do custo médio móvel |
| B-04 | Sistema de plugins para relatórios/importadores | Inspirado no InvenTree |
| B-05 | Multiusuário no desktop (trilha de auditoria por usuário) | Hoje só campo "autor" |
| B-06 | Consulta em linguagem natural ("o que acaba esta semana?") | Camada opcional sobre os serviços |
| B-07 | Anexos e fotos por item | Armazenamento em disco/objeto |
| B-08 | Previsão sazonal | Só se houver histórico real que justifique |

---

## 13. Medições

> Número sem condição de medição (máquina, dataset, commit) não entra.

| Data | Métrica | Valor | Condição | Meta |
|---|---|---|---|---|
| — | Saldo de item com 100 mil movimentos | — | — | < 100 ms (RNF-002, inicial) |
| — | Abertura do desktop com dataset demo | — | — | < 3 s (RNF-003, inicial) |
| — | Cobertura do `core` | — | — | ≥ 90% (RNF-001) |
| — | Tempo do `make check` | — | — | acompanhar |

**Ritmo (preencher ao concluir milestones):**

| Milestone | Etapas entregues | Esforço real | Tamanho previsto | Observações |
|---|---|---|---|---|
| — | — | — | — | — |

---

## 14. Diário de alterações (mais recente primeiro)

> Formato: **data · o que foi feito/tentado · resultado · causa · lição.** Registrar também o que não funcionou.

| Data | Registro |
|---|---|
| 2026-10-27 | **M0.2 concluída.** Feito: verificadas no PyPI as versões e o suporte a Python 3.14 de Django, DRF, PyInstaller, CustomTkinter, setuptools e pip; CustomTkinter 6.0.0 testado de verdade num venv descartável (abre janela no 3.14.3). Criados `pyproject.toml` (distribuição `stockit`, `core` sem dependências, extras `desktop`/`web`/`package` com versões exatas), esqueleto `core/{domain,services,ports}` com `py.typed`, `.python-version` (3.14) e `.nvmrc` (24). Venv `.venv` com 3.14.3, `pip install -e .` ok; `import core` de fora do repositório resolve para o código-fonte (editável confirmado). README ganhou o passo a passo de setup. Decisões: D-03 = CustomTkinter (usuário); D-04 = Python 3.14, Node 24 LTS, Django 5.2.18 LTS. Lição: a versão mais nova do Django (6.1.2) não é LTS; o documento pede LTS, por isso 5.2. Pendência registrada em §5.1: lock de dependências transitivas. |
| 2026-10-27 | **M0.1 concluída.** Feito: `git init` na pasta definida (D-06), `.gitignore` (Python, Node, Django, bancos `.db`/`.sqlite3`, `.env`, caches de ferramentas), `.gitattributes` (LF no repo, CRLF em `.bat`/`.cmd`/`.ps1`), LICENSE MIT, README mínimo, commit inicial na `main` e branch `dev` criada a partir dela (trabalho segue na `dev`). Este arquivo já estava na raiz da pasta; atualizado o nome para **StocKit**. Resultado: ok, nada publicado (sem remoto, sem push). Decisões: D-01 = StocKit (escolha do usuário); D-05 = MIT (usuário sem preferência → recomendação do documento); D-06 = pasta atual. Lição: o titular do copyright na LICENSE usa o usuário GitHub `KaueChristian` (§2) — *hipótese* de que é o nome desejado; ajustar se não for. |
| 2026-10-27 | **Planejamento inicial.** Revisado o portfólio (`kauechristian.github.io`): a seção de projetos só renderiza placeholders de template e **não há repositório do Inventory Manager**; confirmado pelo usuário que o projeto começa do zero. Pesquisadas referências no GitHub (§21). Decisões tomadas: universal (sem nicho), duas plataformas com núcleo compartilhado, sem servidor dedicado, desktop primeiro. Este arquivo criado com o roadmap M0–M7 e portões de integridade. Nenhum código escrito. |

---

## 15. Bugs encontrados

> Um bug por linha. Status: `ABERTO` · `EM ANÁLISE` · `CORRIGIDO` · `NÃO REPRODUZIDO` · `ADIADO`.
> Antes de corrigir: causa raiz comprovada (fato) — hipótese não vira correção.

| ID | Data | Milestone/Etapa | Descrição e passos | Severidade | Causa raiz (fato/hipótese) | Status | Correção / teste de regressão |
|---|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — | — |

---

## 16. Planos descartados e por quê

> Antes de propor algo, procure aqui. Reabrir exige evidência nova, registrada em §19.

| ID | Ideia | Decisão | Motivo | Data |
|---|---|---|---|---|
| P-01 | Projeto voltado a um nicho (salão/barbearia, ficha técnica por serviço) | 🗑️ Descartado | As demos do portfólio não geraram venda; o usuário prefere um sistema universal e integrável. O nicho vira **perfil** configurável, não código | 2026-10-27 |
| P-02 | Saldo como coluna editável do item | 🗑️ Descartado | Perde auditoria e permite inconsistência; o livro imutável dá histórico, saldo em uma data e previsão de graça (INV-01/02) | 2026-10-27 |
| P-03 | Campos personalizados em modelo EAV puro | 🗑️ Descartado | Consultas e validação complexas e lentas; JSON validado por definição basta para o escopo | 2026-10-27 |
| P-04 | Exigir servidor dedicado para a web | 🗑️ Descartado | Contraria o objetivo de rodar sem servidor; web local + demo em plano gratuito + vitrine estática cobrem a exibição | 2026-10-27 |
| P-05 | Sincronização desktop ↔ web no escopo inicial | ⏸️ Adiado (B-01) | Resolução de conflitos é um projeto à parte; a paridade por testes entrega o valor de "duas plataformas" com muito menos risco | 2026-10-27 |
| P-06 | Começar pela web | 🗑️ Descartado | A stack do desktop já é conhecida e deixa o núcleo amadurecer; o contrato fica testado antes do Django entrar | 2026-10-27 |
| P-07 | Microsserviços / API separada para o desktop | 🗑️ Descartado | Complexidade sem ganho no escopo; hexagonal já isola o núcleo | 2026-10-27 |
| P-08 | Desktop com Django ORM headless | 🔁 Plano B (não descartado) | Schema único, porém executável pesado e fuga da stack SQLite puro. Reavaliar só se o escopo do M2/M5 estourar (D-02) | 2026-10-27 |

---

## 17. Riscos

| ID | Risco | Mitigação |
|---|---|---|
| R-01 | Persistência dupla diverge (SQLite × Django ORM) | Suíte de contrato + teste de paridade (M2.6, M5.3, M5.10) |
| R-02 | Escopo grande para uma pessoa; milestones demorados | Portões menores (dividir milestone, §9.1); entregar desktop (M3) antes de iniciar a web |
| R-03 | Aparência "padrão Tkinter" enfraquece o portfólio | CustomTkinter, tema, dashboard e paleta de comandos já no M3; revisão visual no portão |
| R-04 | Previsão passa falsa sensação de precisão | Indicador de confiança obrigatório (M4.5) e ADR de limitações |
| R-05 | Documento desatualizado em relação ao código | Regra §0.7; checklist de PR; rastreabilidade automatizada |
| R-06 | Plano gratuito de hospedagem muda ou desliga | Vitrine estática (M7.4) e modo local como garantia |
| R-07 | PyInstaller disparando antivírus/SmartScreen | Checksum no release, instruções no README; assinatura só se valer o custo |
| R-08 | SQLite concorrente (web + várias abas) | WAL + `busy_timeout` no desktop; na web, banco do Django em Postgres se um dia houver uso real |
| R-09 | `float` escapando em quantidades/custos | Tipos `Decimal` no domínio; teste de propriedade e mypy estrito |

---

## 18. Dúvidas e decisões em aberto (dependem do usuário)

| ID | Pergunta | Recomendação | Prazo |
|---|---|---|---|
| ~~D-01~~ | ~~Nome definitivo do projeto~~ | ✅ **StocKit** (§19, 2026-10-27) | M0.1 |
| D-02 | Persistência do desktop: repositório SQLite próprio ou Django ORM headless | **SQLite próprio** (stack e demonstração de portas/adaptadores) | M0.6 (ADR-002) |
| ~~D-03~~ | ~~Tkinter puro ou CustomTkinter~~ | ✅ **CustomTkinter 6.0.0** (§19, 2026-10-27) | M0.2 |
| ~~D-04~~ | ~~Versões fixas de Python, Node, Django~~ | ✅ Python 3.14, Node 24 LTS, Django 5.2.18 LTS (§5.1, §19) | M0.2 |
| ~~D-05~~ | ~~Licença do repositório~~ | ✅ **MIT** (§19, 2026-10-27) | M0.1 |
| ~~D-06~~ | ~~Pasta local do projeto~~ | ✅ `C:\Users\Desenvolvedor\Documents\port\StocKit` (§19, 2026-10-27) | M0.1 |
| D-07 | Método de valoração inicial | **Custo médio móvel**; FIFO depois (B-03) | M1.14 |
| D-08 | Auth da web: sessão ou token | Sessão para a SPA servida pelo Django (CSRF); token só se houver cliente externo | M5.5 |

---

## 19. Registro de decisões

| Data | Decisão | Motivo |
|---|---|---|
| 2026-10-27 | Sistema **universal**, sem nicho; variações por perfis configuráveis | Ver P-01 |
| 2026-10-27 | Duas plataformas: desktop (Tkinter + SQLite) e web (Django + DRF + React) | Demonstrar arquitetura portável e domínio de duas stacks |
| 2026-10-27 | Núcleo Python puro (hexagonal) compartilhado; adaptadores por plataforma | Mesmo comportamento garantido por contrato e paridade |
| 2026-10-27 | Sem servidor dedicado (local + demo em plano gratuito + vitrine estática) | Ver §5.3 e P-04 |
| 2026-10-27 | Estoque como livro de movimentações imutáveis | Ver P-02 |
| 2026-10-27 | Roadmap em milestones M0–M7; cada um fecha só após portão de integridade | Pedido do usuário: conjunto de melhorias seguido de validação por plano de teste |
| 2026-10-27 | Desktop antes da web | Ver P-06 |
| 2026-10-27 | Este arquivo é o documento-chefe; vive na raiz do repo a partir da M0.1 | Alinhamento código ↔ documento ↔ desenvolvimento |
| 2026-10-27 | Nome definitivo: **StocKit** (D-01) | Escolha do usuário; coincide com a pasta do projeto |
| 2026-10-27 | Licença **MIT** (D-05) | Usuário sem preferência; recomendação do documento (permissiva, comum em portfólio) |
| 2026-10-27 | Pasta do projeto: `C:\Users\Desenvolvedor\Documents\port\StocKit` (D-06) | Pasta onde o documento já estava; fora de Downloads |
| 2026-10-27 | Finais de linha normalizados em LF via `.gitattributes` | Evita diffs falsos entre Windows e CI (Linux) |
| 2026-10-27 | Desktop com **CustomTkinter 6.0.0** (D-03) | Escolha do usuário; mitiga R-03; testado no Python 3.14 |
| 2026-10-27 | **Python 3.14** como versão única (D-04) | Já instalado; Django 5.2 LTS, DRF, PyInstaller e CustomTkinter suportam (verificado em §5.1) |
| 2026-10-27 | **Django 5.2 LTS** em vez do 6.1 | O documento pede LTS; 5.2 tem suporte até 2028 e já cobre o Python 3.14 |
| 2026-10-27 | **Node 24 LTS** para o frontend | Já instalado; linha LTS |
| 2026-10-27 | Um único `pyproject.toml` (distribuição `stockit`) com extras por plataforma | O `core` fica sem dependências; cada app instala só o extra dele |

**Índice de ADRs** (`docs/adr/`, preencher na M0.6): ADR-001 núcleo hexagonal · ADR-002 SQLite no desktop · ADR-003 Django ORM na web · ADR-004 livro de movimentações · ADR-005 campos personalizados em JSON.

---

## 20. Glossário

| Termo | Significado |
|---|---|
| **Item** | Qualquer coisa controlada em estoque (produto, insumo, ativo, peça) |
| **Movimentação** | Registro imutável de entrada, saída, transferência, ajuste, perda ou devolução |
| **Livro (ledger)** | Sequência de movimentações da qual o saldo é derivado |
| **Saldo** | Soma assinada das movimentações de (item, local, lote) |
| **FEFO** | *First Expired, First Out*: sai primeiro o lote que vence primeiro |
| **Ponto de reposição** | Saldo a partir do qual se deve repor |
| **Estoque de segurança** | Margem para absorver variação de consumo/prazo |
| **Curva ABC** | Classificação dos itens por valor de consumo (A mais relevante) |
| **Giro** | Quantas vezes o estoque se renova num período |
| **Cobertura** | Dias que o estoque atual dura no ritmo de consumo |
| **Perfil** | JSON que pré-configura rótulos, campos e unidades de um tipo de negócio |
| **Porta / Adaptador** | Interface do núcleo / implementação concreta (SQLite, Django ORM) |
| **Contrato (teste)** | Suíte que todo adaptador de uma porta deve passar |
| **Paridade** | Mesmo cenário produz mesmos resultados no desktop e na web |
| **Portão** | Execução do plano de teste que fecha um milestone |
| **ADR** | *Architecture Decision Record*: decisão arquitetural com contexto e consequências |

---

## 21. Referências

> Levantadas em 2026-10-27 por busca; **qualidade e licença não foram verificadas** — checar antes de reutilizar qualquer código.

- Estrutura de apps de estoque em Tkinter/SQLite: [Zynox-Tech/Inventory-Management-System](https://github.com/Zynox-Tech/Inventory-Management-System), [nishant0820/Inventory-Management-System](https://github.com/nishant0820/Inventory-Management-System), [datapro/inventory-system-with-python](https://github.com/datapro/inventory-system-with-python) (exportação CSV), [For-Community/Inventory-Management-System](https://github.com/For-Community/Inventory-Management-System) (tema claro/escuro).
- Domínio e histórico de estoque: [InvenTree](https://github.com/inventree/InvenTree) (histórico de rastreio, itens serializados, plugins); [Snipe-IT](https://www.alternativeto.net/software/snipe-it/about/) (atribuição, localização e histórico completo do ativo).
- Fórmulas (ABC, EOQ, ponto de reposição, estoque de segurança): [supplychainpy](https://pypi.org/project/supplychainpy/0.0.5rc3/), [invcalc](https://pypi.org/project/invcalc/).
- Previsão de ruptura: [InvenTrack](https://dev.to/eymenozt/pen-source-grocery-store-management-app-with-python-tkinter-20ca) (abordagem sobre histórico de movimentações).
- Documentos-modelo deste arquivo: `C:\Users\Desenvolvedor\Documents\port\site3d\project_context.md` e `C:\PROJETOS\Folha\Projeto\Library_Tron\DOCUMENTO_CHEFE_140388.md`.
