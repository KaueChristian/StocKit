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
7. Se a etapa mudou comportamento: atualizar requisito (`docs/requirements.md`), teste vinculado e a documentação em
   `docs/` **no mesmo commit**.

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
| Milestone aberto | **M1 — Núcleo de domínio** (11 de 14 etapas) |
| Última etapa concluída | **M1.11** — campos personalizados (definição por tipo de item, 5 tipos, regras, validação com o campo identificado, JSON) e serviços `register_item`/`update_item` (2026-10-27) |
| Próxima etapa | **M1.12** — configuração do sistema (políticas) e loader de perfis com validação por JSON Schema; perfis varejo, cozinha, oficina e TI |
| Bloqueios | Nenhum |
| Último portão aprovado | **M0** — 2026-10-27, 6 de 6 casos, BUG-01 achado e corrigido (§11) |
| Versão | **0.0.1** — tag `v0.0.1` na `main` ([KaueChristian/StocKit](https://github.com/KaueChristian/StocKit)) |
| Bugs abertos | 0 (BUG-01 e BUG-02 corrigidos) |

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
| Repositório | <https://github.com/KaueChristian/StocKit> — **público** desde 2026-10-27 (`main` e `dev`) |
| Licença | MIT (D-05) |
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

- **Ferramentas de qualidade (M0.3)**, no `[dependency-groups] dev` do `pyproject.toml` e repetidas no
  `.pre-commit-config.yaml`: ruff 0.17.3, mypy 2.4.0, pytest 9.1.1, pytest-cov 7.1.0, coverage 7.17.0,
  hypothesis 6.170.12, pre-commit 4.7.0, import-linter 2.15 (M0.4); ganchos pre-commit-hooks v6.0.0,
  ruff-pre-commit v0.17.3 e check-jsonschema 0.38.2 (M0.5).
- **GitHub Actions (M0.5)**, fixadas por hash: `actions/checkout` v7.0.1 (`3d3c42e5…`), `actions/setup-python` v7.0.0
  (`5fda3b95…`). Havia `setup-python` v7.1.0 e `check-jsonschema` 0.39.0, com menos de 14 dias de publicação:
  ficaram de fora pela regra de quarentena (§19).
- **Sem GNU make no Windows (fato, 2026-10-27):** o único `make` no PATH é o do Embarcadero RAD Studio, com sintaxe
  incompatível. Por isso o comando oficial é `python tools/check.py`; o `Makefile` é só atalho para Linux/CI.
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

Diagramas: [C4 nível 1 — contexto](docs/c4/01-contexto.md) · [C4 nível 2 — containers](docs/c4/02-containers.md).

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
- Dentro do `core`: `services` → `ports` → `domain` (contrato `core-camadas`, M0.4).
- **Estado dos contratos (M1.5):** ativos `core-puro`, `core-camadas` e `adapters-sem-apps` (adaptadores não importam
  `apps` nem `core.services`). `apps-independentes` está escrito e comentado no `pyproject.toml`; **ativar** ao criar
  `apps` (M3.1), incluindo o pacote em `root_packages`. Limitação conhecida: imports dinâmicos (`importlib`, `__import__`) não são detectados.

### 6.3 Persistência dupla e como mantê-la honesta
Há dois adaptadores (SQLite puro e Django ORM) para as mesmas portas. A defesa é a **suíte de contrato**: os mesmos testes
rodam parametrizados contra memória, SQLite e Django ORM. A **suíte de paridade** (M5) roda o mesmo cenário do dataset de
referência nas duas plataformas e compara os saldos com um JSON dourado.
*Decidido em D-02 / [ADR-002](docs/adr/002-sqlite-no-desktop.md):* desktop com repositórios próprios sobre `sqlite3`.
*Plano B (não descartado, P-08):* o desktop usar o Django ORM sem servidor (`django.setup()` sem `runserver`), com schema
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
- INV-04 Conversão de unidade ida e volta preserva o valor (com `Decimal` e arredondamento definido: 6 casas,
  half-even, um único arredondamento; erro máximo ½·10⁻⁶·(1 + f_B/f_A), zero para unidade divisível — ADR-006).
- INV-05 Saldo negativo só ocorre se a política do sistema permitir (padrão: proibido).
- INV-06 Saída de item com lote segue FEFO quando o lote não é informado.
- INV-07 Item serializado nunca tem saldo fracionário nem número de série repetido.
- INV-08 Soma dos saldos por local = saldo total do item.

### 7.3 Valoração do estoque
Padrão proposto: **custo médio móvel** (D-07). FIFO fica como política opcional posterior. Decisão pendente em §18.

---

## 8. Requisitos (rastreáveis)

> **Movido para [`docs/requirements.md`](docs/requirements.md) na M0.6** — fonte única dos requisitos (RF-001..RF-028,
> RNF-001..RNF-006), com milestone, invariantes relacionadas, casos de portão que os verificam e status.
> Cada RF/RNF tem **pelo menos um teste** marcado com `@pytest.mark.req("RF-xxx")` (ou equivalente no
> Vitest/Playwright); o script de rastreabilidade (M0.9) gera a matriz requisito × teste × status.
> `tests/docs/test_docs_consistency.py` falha se este arquivo ou `docs/` citarem requisito, caso de portão, invariante
> ou ADR que não existe. Requisitos ainda **sem caso de portão** estão listados em "Lacunas conhecidas" naquele arquivo.

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
6. **Definição de pronto de uma etapa:** código com teste, requisito referenciado, doc atualizada, `make check` /
   `python tools/check.py` (ruff + mypy + pytest com cobertura + import-linter a partir da M0.4) verde, entrada no
   diário (§14).

---

## 10. Roadmap por milestones

Legenda: ⬜ não iniciado · 🔄 em andamento · ✅ concluído · ⛔ bloqueado · 🗑️ descartado.
Tamanhos: **P** ≤ 1 dia · **M** 2–4 dias · **G** 1–2 semanas (estimativas iniciais; recalibrar com §13).
Ordem de execução = ordem de leitura. IDs de etapa (`M3.4`) são para commits, issues e conversas.

---

### M0 — Fundação · tamanho M · `v0.0.x` · ✅ fechado em 2026-10-27 (`v0.0.1`)
**Objetivo:** poder evoluir rápido sem perder o alinhamento entre código, doc e processo.

| ID | Etapa | Tam. | Status |
|---|---|---|---|
| M0.1 | Criar repositório (pasta definida em D-06), `git init`, branches `main`/`dev`, `.gitignore`, LICENSE (D-05), README mínimo; **mover este arquivo para a raiz** | P | ✅ |
| M0.2 | `pyproject.toml` com `core` instalável em modo editável; venv; **fixar versões** de Python/Node/Django e registrar em §5.1 | P | ✅ |
| M0.3 | Ferramentas: ruff, mypy (estrito no `core`), pytest, pytest-cov, hypothesis, pre-commit; alvo único `make check` (ou script equivalente no Windows) | P | ✅ |
| M0.4 | Contratos do `import-linter` (`core` não importa adaptadores/apps/frameworks) | P | ✅ |
| M0.5 | CI no GitHub Actions: lint, tipos, testes, import-linter em push na `dev` e PRs | P | ✅ (validado localmente; 1ª execução real no GitHub pendente → TP-M0-03) |
| M0.6 | `docs/`: estrutura, glossário (§20), `requirements.md` (a partir de §8), template de ADR e **ADRs 001–005** (núcleo hexagonal; SQLite no desktop; Django ORM na web; livro de movimentações; campos personalizados em JSON) | M | ✅ |
| M0.7 | Diagramas C4 níveis 1–2 em Mermaid (`docs/c4/`) | P | ✅ (renderiza no GitHub: TP-M0-04 ok) |
| M0.8 | Template de PR (checklist de §9.3.6), templates de issue, `CONTRIBUTING.md` curto | P | ✅ |
| M0.9 | Marker `req` no pytest + script `tools/traceability.py` que gera a matriz requisito × teste × status | M | ✅ |
| M0.10 | Teste "sentinela" do import-linter (prova que um import proibido quebra o CI) e teste dummy anotado com `req` | P | ✅ (no lugar do teste dummy: testes reais da RNF-006, ver §19) |

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
| M1.1 | Value objects: `Quantity` (`Decimal` + unidade), `UnidadeDeMedida` e conversões (INV-04) | M | ✅ (no código: `UnitOfMeasure`, ver §19) |
| M1.2 | Entidades `Item`, `Categoria`, `Local` (hierarquia), `Parte` com validações | M | ✅ (`Category`, `Location`, `Party` no código) |
| M1.3 | `Movimentacao` imutável e tipos (entrada, saída, transferência, ajuste, perda, devolução) | M | ✅ (`Movement` no código) |
| M1.4 | Portas: repositórios, `UnitOfWork`, `Clock` (`Protocol`) | P | ✅ |
| M1.5 | Repositórios **em memória** (`adapters/memory`) usados pelos testes | M | ✅ |
| M1.6 | Serviço `registrar_movimento` com política de saldo negativo (INV-05) e atomicidade via UoW | M | ✅ (`record_movement` no código) |
| M1.7 | Serviço de saldo por item/local/lote e **saldo em uma data** (INV-01, INV-08) | M | ✅ |
| M1.8 | Transferência atômica (INV-03) | P | ✅ (`transfer_stock`) |
| M1.9 | Lotes e validade; **FEFO** na saída sem lote informado (INV-06) | M | ✅ |
| M1.10 | Itens serializados (INV-07) | P | ✅ |
| M1.11 | Campos personalizados: definição, tipos, validação no `Item` | M | ✅ |
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
| TP-M1-12 | Hierarquia de 3 níveis (depósito › corredor › prateleira); mover um local para dentro do próprio descendente; dois irmãos com o mesmo nome (maiúsculas diferentes) | Caminho completo correto; ciclo e nome repetido recusados com erro de domínio (RF-002) |
| TP-M1-13 | Parte com cada papel e com dois papéis; papel inválido; sem papel; nome vazio | Válidas aceitas; inválidas recusadas com erro de domínio que cita o campo (RF-003) |

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
| 2026-10-27 | M0 | `3e55ded` (`dev`), local, Windows 11 / Python 3.14.3 | TP-M0-01 ★, TP-M0-02 ★ (parte local), TP-M0-05 ★, TP-M0-06 — 4 de 6 | nenhuma | 0 | **Sem decisão (parcial).** TP-M0-03 ★ e TP-M0-04 pendentes (exigem GitHub). M0 **não fecha** e `v0.0.1` não é marcado até executá-los. Detalhes e evidências: [`docs/test-plan/M0-portao.md`](docs/test-plan/M0-portao.md) |
| 2026-10-27 | M0 | `cad3790` → `4d6867b` (`dev`), GitHub Actions (Ubuntu + Windows, Python 3.14.8/3.14.9) + navegador | TP-M0-02 ★ (parte CI), TP-M0-03 ★, TP-M0-04 — completam 6 de 6 | TP-M0-03 no 1º run (BUG-01) → corrigido e repetido: ok | 0 (BUG-01 corrigido em `4d6867b`) | **Go — portão M0 aprovado.** Críticos 100%. Regressão após a correção: CI verde na `dev` (`4d6867b`, instalação do zero nos dois sistemas) e check local verde (138 testes). Saída: `main` avançada até a `dev` (fast-forward) e tag `v0.0.1`, a pedido do usuário. Evidências: [`TP-M0-03.md`](docs/test-plan/evidencias/M0/TP-M0-03.md) |

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
| 2026-10-27 | Cobertura do `core` | 100% (0 instruções; só docstrings) | Commit da M0.3, 5 testes; valor sem significado até a M1 | ≥ 90% (RNF-001) |
| 2026-10-27 | Tempo do `check` | 8,5 s (mypy 4,1 s com cache frio) | Windows 11, Python 3.14.3, commit da M0.3, 5 testes, primeira execução | acompanhar |
| 2026-10-27 | TP-M0-01: clone limpo → venv → instalar → check (passos do README) | 36 s (check: 10,1 s; 128 testes) | Windows 11 local, PowerShell, cache do pip aquecido, commit `3e55ded` | acompanhar |
| 2026-10-27 | Job `check` no GitHub Actions (instalação do zero + check) | Ubuntu 25–27 s · Windows 43–49 s | Runners padrão `ubuntu-latest`/`windows-latest`, sem cache do pip, commits `4d6867b`/`2e92f95`, 138 testes | acompanhar |
| 2026-10-27 | Simulação do CI (clone limpo → venv → instalar → check → higiene) | 43 s | Windows 11 local, cache do pip já aquecido, commit da M0.5; **não** é tempo do GitHub Actions | acompanhar |

**Ritmo (preencher ao concluir milestones):**

| Milestone | Etapas entregues | Esforço real | Tamanho previsto | Observações |
|---|---|---|---|---|
| M0 | 10 de 10 (M0.1–M0.10) + portão | 1 dia corrido (2026-10-27), em várias sessões | M | Portão achou 1 bug (BUG-01, CI no Windows); nenhuma etapa descartada |

---

## 14. Diário de alterações (mais recente primeiro)

> Formato: **data · o que foi feito/tentado · resultado · causa · lição.** Registrar também o que não funcionou.

| Data | Registro |
|---|---|
| 2026-10-27 | **M1.11 concluída.** Feito: `core/domain/custom_fields.py` com `CustomFieldDefinition` (chave `snake_case` única, rótulo, tipo — texto, número, data, sim/não, lista —, `kinds` = tipos de item que têm o campo, obrigatório, regras: tamanho máximo, mínimo/máximo, opções; regras incoerentes com o tipo são recusadas), `validate_custom_fields` (campo sem definição, de outro tipo de item, obrigatório ausente, tipo errado e fora das regras recusados; texto vazio = ausente; inteiro vira `Decimal`; todo erro com `field = custom_fields.<chave>`, TP-M1-07) e `encode_values`/`decode_values` (JSON com número como texto decimal e data AAAA-MM-DD, ADR-005). `Item.custom_fields`: mapa congelado; a entidade só confere a forma. Porta `CustomFieldRepository` + `uow.custom_fields` + repositório em memória. Serviços novos em `core/services/catalog.py`: `define_custom_field`, `register_item` e `update_item` (categoria precisa existir; campos conferidos contra as definições do tipo do item). 64 testes novos (RF-004, RF-001), com propriedade de ida e volta pelo JSON sem perda. Cobertura total 100%. **Achado pelos testes:** o `Item` recusava inteiro no mapa de campos, mas a validação aceita inteiro para número — o inteiro nunca chegava à validação; o `Item` passou a aceitar `int`. **Mutações:** sem obrigatório, sem checar tipo de item, sem mínimo, sem conferir opções, serviço sem validar, número como `float` no JSON e vazio contando como valor — as 7 pegas. CI da M1.10 verde antes de começar. |
| 2026-10-27 | **M1.10 concluída.** Feito: `Movement.serials` (conjunto de números de série normalizados em maiúsculas; repetido na mesma movimentação é recusado; com séries, a quantidade é exatamente quantas são) e `make_transfer(serials=...)`; o par de transferência compara as séries. `core/domain/serials.py`: `serial_positions` (onde cada série está) e `first_serial_conflict` (simula o livro e acha a primeira entrada de série já em estoque ou saída de onde ela não está, inclusive em retroativos). Serviços: item serializado exige séries e recusa quantidade fracionária com mensagem própria; item comum recusa séries; `check_serials` roda no registro e na transferência (erro novo `SerialNumberError`, dizendo onde a série estava); consultas `serial_location` e `serials_in_stock` (com sublocais e `at`). Item serializado não pode controlar lote (regra nova no `Item`). 33 testes novos (RF-009), com o TP-M1-06 (série repetida; quantidade fracionária) e a propriedade da INV-07: em operações aleatórias de entrada, saída e transferência (retroativas), cada série fica num lugar só e o saldo por local é exatamente o número de séries lá — sempre inteiro. Cobertura total 100%. **Mutações:** sem conferir série, saída de qualquer local, entrada de série em estoque, sem mensagem de fração, posição sem registrar saída e serializado com lote — as 6 pegas. CI da M1.9 verde antes de começar. Lição: no Windows, texto com acento passado na linha de comando chega embaralhado ao script de edição; para trechos com acento, usar a ferramenta de edição. |
| 2026-10-27 | **M1.9 concluída.** Feito: entidade `Lot` (item, código único no item em maiúsculas, validade como `date` — vale até o dia, inclusive) e `fefo_order` (validade mais próxima primeiro, sem validade por último, empate pelo código); porta `LotRepository` (`find_by_code`, `list_for_item`) e `uow.lots`; `MemoryLotRepository`; serviço `create_lot` (item com lote; validade obrigatória se o item controla validade, recusada se não). Regras comuns dos serviços movidas para `core/services/_rules.py`; lote informado agora precisa **existir e ser do item**. **FEFO:** saída sem lote em item com lote é repartida entre os lotes do local, na ordem FEFO, pulando lote vencido na data da saída; cada lote cede no máximo `available_at` — o menor saldo dele dali em diante, para não estourar saída posterior. Faltando saldo: `FORBID` recusa e avisa quanto há em lote vencido; `ALLOW` põe o que falta no último lote válido. `record_movement` passou a devolver uma **tupla** (uma movimentação por lote). Transferência continua exigindo o lote. 34 testes novos (RF-008), com o TP-M1-05 (3 lotes de validades distintas + vencido sinalizado) e a propriedade da INV-06: um lote só é consumido quando todos os válidos que vencem antes ficaram vazios, e nunca um vencido. Cobertura total 100%. **Achado pelos testes antes do commit:** as partes do FEFO, criadas com `dataclasses.replace`, herdavam o **mesmo id** da movimentação pedida e o livro recusava a segunda (`ConflictError`); cada parte agora ganha id novo. **Mutações:** não pular vencido, ordem invertida, dia da validade como vencido, `available_at` sem olhar saídas posteriores, lote de outro item aceito e falta no primeiro lote — as 6 pegas. CI da M1.8 verde antes de começar. Lição: `replace` numa entidade copia o `id`; para criar outra entidade a partir de uma, passar `id` novo. |
| 2026-10-27 | **M1.8 concluída.** Feito: `TransferStock` e `transfer_stock(uow, clock, pedido, policy)` em `core/services/movements.py`, ao lado de `record_movement`; as regras comuns viraram funções internas (`_active_item`, `_active_location`, `_check_balance`, `_in_base_unit`, `_check_lot`). A transferência confere item, origem e destino ativos, lote, converte para a unidade base sem arredondar, aplica a política de saldo **na origem** (inclusive retroativa) e grava as duas pontas na mesma UoW com um `commit` só. `make_transfer` passou a aceitar `recorded_at`. 13 testes novos (RF-005, RF-007): exemplos (total mantido, conversão, datas, política com `FORBID` e `ALLOW`, inativos, inexistentes), **atomicidade** com um livro que quebra ao gravar a ponta de entrada (nada fica gravado) e propriedade com transferências aleatórias retroativas: total constante, nenhum local negativo em ponto nenhum e todo `transfer_id` com exatamente 2 pontas (INV-03, INV-05, TP-M1-02). **Mutações:** `commit` entre as pontas, política no destino, destino inativo aceito, quantidade sem conversão e par sem `recorded_at` — as 5 pegas. CI da M1.7 verde na `dev` antes de começar. Lição: o `ruff format` em modo Python 3.14 reescreve `except (A, B):` como `except A, B:` (PEP 758); scripts que editam código formatado precisam procurar a forma nova. |
| 2026-10-27 | **M1.7 concluída.** Feito: `core/services/balances.py` com `item_balance` (total; num local, somando sublocais pela `LocationTree` ou não; num lote; combinações), `balances_by_location` (saldo próprio de cada local que já teve movimentação, inclusive os que zeraram) e `balances_by_lot` (chave `None` = sem lote; opcionalmente num local). Todas aceitam `at` (saldo em uma data, por `occurred_at`, inclusive), só leem e nunca fazem `commit`; item ou local inexistente é `NotFoundError`, não saldo zero. 19 testes novos (RF-006): exemplos sobre Depósito › Corredor A › Prateleira 1 + Loja, lançamento retroativo mudando o passado, transferência sem mudar o total, e 3 propriedades sobre livros aleatórios com transferências (podendo ficar negativos): saldo == soma assinada em qualquer data (INV-01, TP-M1-01); soma por local e por lote == total (INV-08, TP-M1-02); local com sublocais == soma da subárvore. Cobertura total 100%. **Mutações:** sem sublocais, sem data, só um nível da árvore, sem lote e saldo por local sem data — as 5 pegas. RF-006 → Atendido. CI da M1.6 verde na `dev` antes de começar. |
| 2026-10-27 | **M1.6 concluída.** Feito: `core/services/movements.py` com `RecordMovement` (pedido) e `record_movement(uow, clock, pedido, policy=FORBID)`: recusa transferência (serviço próprio, M1.8), item/local/parte inexistente (`NotFoundError`) ou inativo (`InactiveRecordError`), lote em item sem lote e item com lote sem lote; converte a quantidade para a unidade base e **recusa conversão que arredondaria** (1 un num item em caixa com 12); carimba `recorded_at` com o `Clock` (data futura cai na regra `occurred_at ≤ recorded_at`); com `FORBID`, simula o livro e recusa (`InsufficientStockError`) se **qualquer ponto a partir da movimentação** ficar negativo — inclusive saída retroativa que estoura um ponto posterior; grava e faz `commit` na UoW (erro = nada gravado). Domínio: `NegativeStockPolicy`, `ledger.py` (`balance`, `in_ledger_order`, `first_negative_from`), `Movement.recorded_at`. `str(Quantity)` agora sem zeros à direita (a mensagem saía "-2.000000 un"). 41 testes novos (RF-005, RF-006, RF-007, RF-010), com propriedade da INV-05: sequências aleatórias de entradas, saídas, perdas e ajustes retroativos nunca deixam o livro gravado negativo em ponto nenhum — base do TP-M1-04; cobertura total 100%. **Mutações:** política ignorada (10 testes caem), conferir só na data da saída, nova movimentação antes no empate, aceitar conversão que arredonda, sem `commit` (11), sem `recorded_at` e local inativo aceito — as 7 pegas. CI da M1.5 verde na `dev` antes de começar. Risco novo R-10 (conferir-e-gravar concorrente). |
| 2026-10-27 | **M1.5 concluída.** Feito: pacote `adapters` (na distribuição, no mypy, na cobertura e em `root_packages` do import-linter); contrato `adapters-sem-apps` **ativado**, proibindo também `core.services` (§6.2: adaptador usa só portas e domínio); a sentinela copia `adapters` e ganhou 2 casos (adaptador importando `apps` e `core.services`). `adapters/memory`: `MemoryState` (dicionários + lista do livro), repositórios com as regras das portas (`NotFoundError`, `ConflictError`, SKU único em `add`/`update`, `list` ordenado; livro filtrável e ordenado por data e, no empate, por lançamento; `transfer_pair`) e `MemoryUnitOfWork`: várias UoWs compartilham o estado confirmado, cada bloco `with` trabalha numa cópia; `commit` publica, `rollback`/sair sem `commit`/exceção descartam; usar fora do `with` e aninhar dão erro. `adapters/clock.py`: `SystemClock` (UTC) e `FixedClock` (exige fuso, só anda para frente). 20 testes novos, incluindo propriedade que compara o livro com um modelo sob sequências aleatórias de lançamento/commit/rollback; cobertura total 100%. **Mutações:** sair grava sem commit (4 testes caem), filtro "até" exclusivo, SKU sem unicidade e commit sem recopiar o rascunho — pegas. Uma mutação **sobreviveu** (commit sem `.copy()`): era redundante, porque o `_begin` seguinte já recopia; código simplificado e comentado. Também removido `new_lot_id`, criado na M1.3 sem uso (a cobertura acusou): volta com o lote na M1.9. O push da M1.4 falhou uma vez por erro momentâneo do GitHub; repetido, CI verde. |
| 2026-10-27 | **M1.4 concluída.** Feito: `core/ports/clock.py` (`Clock.now()` com fuso, em UTC), `core/ports/repositories.py` (`Repository[E, K]` genérico com `get`/`add`/`update`/`list`; `ItemRepository` com `find_by_sku`; categorias, locais e partes; `MovementRepository` só com `append`, `get`, `list` filtrável por item/local/lote/até uma data e `transfer_pair`) e `core/ports/unit_of_work.py` (repositórios + `commit`/`rollback`; sair sem `commit` desfaz). Semântica de cada método escrita nas docstrings (o que levanta `NotFoundError`/`ConflictError`, ordem do `list`), para a suíte de contrato da M2.6 cobrar. Erros novos: `NotFoundError`, `ConflictError`. 11 testes: membros exatos de cada porta (livro sem `update`/`delete` — INV-02 por construção, RF-005; nenhum cadastro com `delete`), implementação mínima usada como um serviço usaria, e o mypy rodando sobre 3 trechos (UoW completa passa; `commit` com assinatura errada e classe vazia são recusados). **Mutações:** `delete` no livro e `UnitOfWork` sem `commit` — ambas pegas. CI da M1.3 verde na `dev` antes de começar. **Achado no commit:** o gancho `pytest` do pre-commit roda num ambiente próprio sem mypy, e o teste novo falhou lá ("No module named mypy") — o mesmo caso do import-linter na M0.10; mypy 2.4.0 acrescentado ao gancho (versão conferida pelo teste de pins). Lições: (1) teste que chama uma ferramenta em subprocesso precisa dela também no ambiente do gancho; (2) gerar código Python com `
` dentro de um script Python em heredoc vira quebra de linha real — escrever o trecho direto no arquivo. |
| 2026-10-27 | **M1.3 concluída.** Feito: `core/domain/movement.py`. `MovementKind` com 9 tipos, cada um com direção fixa: entrada, saída, transferência (saída/entrada), ajuste (para mais/para menos), perda, devolução de cliente (entra) e devolução a fornecedor (sai). `Movement` imutável: item, local, quantidade **positiva** (`signed_quantity` dá o sinal pelo tipo), `occurred_at` com fuso e gravado em UTC, autor obrigatório, e opcionais lote, parte, custo unitário (`Decimal` ≥ 0, até 6 casas) e motivo — obrigatório em ajuste e perda. Transferência: `make_transfer` monta o par com o mesmo `transfer_id` e `check_transfer_pair` confere um par lido (tipos opostos, mesmo item/lote/quantidade/data, locais diferentes); só transferência tem `transfer_id`. IDs novos: `LotId`, `MovementId`, `TransferId`. 73 testes novos (RF-005), com propriedades para o sinal e para a conservação no par (INV-03); cobertura do `core` 100%. **Mutações:** perda como entrada, perda sem motivo, data sem UTC, par sem comparar quantidade e quantidade zero aceita — todas pegas. CI da M1.2 verde na `dev` antes de começar. Lição: em teste que monta o objeto por um helper que já lê o campo (`kind`), o caso de tipo errado tem de passar por `replace`, que revalida. |
| 2026-10-27 | **M1.2 concluída.** Feito: `core/domain/{ids,entity,catalog,location,party}.py`. IDs são UUIDs com tipo próprio por entidade (`ItemId`, `LocationId`…); entidades são dataclasses congeladas com igualdade por tipo + `id`; editar = `dataclasses.replace`, que valida de novo. `Item`: SKU sem espaços e em maiúsculas (letras, dígitos, `. _ / -`, até 64), nome até 200, tipo (`ItemKind`), unidade base, categoria opcional, `tracks_lots`/`tracks_expiry`/`active`; validade exige lote; serializado exige contagem com fator 1. `Category` simples. `Location` conhece só o pai; `LocationTree` recusa pai inexistente, ciclo e irmãos com o mesmo nome (sem diferenciar maiúsculas), e dá `path`, `full_name` ("Depósito › Corredor A › Prateleira 3"), `children` e `descendants`. `Party` com um ou mais papéis (`PartyRole`). Erros novos: `ValidationError` (com o campo) e `HierarchyError`. 78 testes novos (RF-001, RF-002, RF-003), com propriedades do hypothesis sobre florestas aleatórias de locais; cobertura do `core` 100%. **Prova de que os testes pegam erro:** 4 mutações (sem checagem de ciclo, nomes sem `casefold`, validade sem lote, serializado com qualquer contagem) — todas derrubaram testes. Lacunas RF-002 e RF-003 fechadas com TP-M1-12 e TP-M1-13. CI da M1.1 verde na `dev` antes de começar. Lição: o ruff marca "›" como caractere ambíguo; liberado em `allowed-confusables`, como o "×". |
| 2026-10-27 | **M1.1 concluída.** Feito: `core/domain/quantity.py` com `Dimension` (contagem, massa, volume, comprimento), `UnitOfMeasure` (símbolo, nome, grandeza, fator para a base) e `Quantity` (`Decimal` até 6 casas e 12 dígitos inteiros; conversão `to()`; soma, subtração, negação e comparação só na mesma unidade); catálogo `STANDARD_UNITS` (un, dz, kg, g, mg, L, mL, m, cm, mm); `core/domain/errors.py` com `DomainError` e três erros específicos. 54 testes novos ligados ao RF-010, com propriedades do hypothesis para a INV-04 (limite de ida e volta, ida e volta exata para unidade divisível, arredondamento único) — verdes nos perfis `dev` e `ci`; cobertura do `core` 100%. **Prova de que os testes pegam erro:** trocar half-even por "meio para cima" derrubou o teste do caso do meio; arredondar para 5 casas derrubou 6 testes. Decisões: ADR-006 (escala e arredondamento) e nomes em inglês (§19). **Achado ao gerar a matriz:** BUG-02 (redirecionar a matriz para arquivo quebrava no Windows), corrigido em commit próprio. Lição: o caso do meio exato precisa de teste de exemplo; propriedades com limite de erro não distinguem half-even de half-up. |
| 2026-10-27 | **M0 fechado — `v0.0.1`.** A pedido do usuário: versão do `pyproject.toml` 0.0.0 → 0.0.1, `main` avançada até a `dev` por fast-forward (sem commit de merge; histórico igual nas duas) e tag anotada `v0.0.1` publicada. CI verde na `dev` antes de mover a `main`. Milestone aberto passa a ser o M1. Lição: nenhuma nova. |
| 2026-10-27 | **Portão M0 aprovado (execução 2, GitHub).** Repositório criado **público** em `KaueChristian/StocKit` a pedido do usuário; `main` e `dev` publicadas. **Achado:** o 1º CI da `dev` falhou só no Windows — `tools/check.py` quebrou com `FileNotFoundError` ao chamar `lint-imports`. **Causa (fato, pelo log e pelo código):** o script procurava executáveis ao lado do `python.exe`, o que só vale num venv; no runner, que usa o Python sem venv, eles ficam em `Scripts\`. Localmente nunca apareceu porque o check sempre rodou no `.venv`. **Correção** (`4d6867b`, BUG-01): caminho via `sysconfig.get_path("scripts")`; ferramenta ausente vira "FALHA" no resumo em vez de traceback; 2 testes novos. CI da `dev` verde nos dois sistemas. **TP-M0-02 (CI):** PR #1 com `import tkinter` usado → `check` falhou no Ubuntu e no Windows pelo contrato `core-puro`. **TP-M0-03:** sem o import, 3 jobs verdes; PR fechado sem merge e branch apagada. Os commits da branch de teste foram feitos pela API do GitHub, para o import chegar ao CI sem pular ganchos locais. **TP-M0-04:** os dois C4 renderizam no GitHub. Resultado: **6 de 6, go.** Lições: (1) o CI em outro SO e sem venv achou um defeito que nenhum teste local podia achar — vale para o empacotamento (M3); (2) IDs de bug passam a usar `BUG-xx`, porque `B-xx` já é do backlog (§12). Pendente: tag `v0.0.1` e merge na `main`, só com pedido do usuário. |
| 2026-10-27 | **Portão M0 — execução parcial (local).** Sobre o commit `3e55ded`: **TP-M0-01** ★ passou (clone limpo seguindo só o README, check verde em 36 s); **TP-M0-02** ★ passou na parte local (`lint-imports` e `tools/check.py` saíram com 1, commit bloqueado); **TP-M0-05** ★ passou (matriz com RNF-006 ligada a 18 testes verdes); **TP-M0-06** passou (estrutura automática + revisão das afirmações dos ADRs contra o repositório; revisão feita pelo autor). **Achado no TP-M0-02:** com `import tkinter` sem uso, o gancho `ruff check --fix` apagou o import antes do import-linter rodar, e o gancho do import-linter apareceu "Passed" (commit barrado pelo ruff). Causa comprovada pelo log ("1 fixed") e pelo arquivo vazio depois do commit; rodando o gancho isolado, ele acusa a violação. Repetido com import usado: gancho do import-linter falhou como esperado. **Não é bug** — lição: casos de violação usam import usado. TP-M0-03 ★ e TP-M0-04 **pendentes** (GitHub). Evidências em `docs/test-plan/evidencias/M0/`; registro no §11. Corrigida também a linha "Bloqueios" do painel (§1), que tinha uma célula sobrando por uma edição incompleta na M0.10 (o teste de coerência não confere o formato das tabelas). |
| 2026-10-27 | **M0.10 concluída — todas as etapas do M0 prontas.** Feito: `tests/architecture/test_import_contracts.py` — copia `core` e `pyproject.toml` para pasta temporária, planta imports proibidos e roda o import-linter em subprocesso com `PYTHONPATH` apontando para a cópia (confirmado antes, por experimento, que a cópia vence a instalação editável); 1 caso de controle (cópia limpa passa) + 6 violações (tkinter, django, sqlite3, adapters, domain→services, ports→services), cada uma quebrando o contrato certo; 2,1 s. **Prova inversa:** tirar `tkinter` da lista de proibidos fez falhar exatamente o caso `tkinter` (configuração restaurada). `tests/project/test_dependency_pins.py` com `@pytest.mark.req("RNF-006")`: toda dependência declarada com `==`, versões do pre-commit e do workflow iguais às do grupo `dev`, `rev` do ruff igual ao ruff do grupo, actions por hash, `.env`/`*.db`/`*.sqlite3` no `.gitignore` (18 casos); com versão divergente e uma dependência sem pin plantadas, falharam os casos esperados. pre-commit: gancho do pytest ganhou `import-linter` (a sentinela precisa dele). Matriz de rastreabilidade: **1 de 34** requisitos com teste (RNF-006, 18 testes, todos verdes). Total: 128 testes. |
| 2026-10-27 | **M0.9 concluída.** Feito: marker `req(*ids)` registrado no pytest (`--strict-markers` já ativo); `tests/conftest.py` valida na coleta que todo `req` cita requisito existente em `docs/requirements.md` (senão `UsageError`, código 4); `tools/traceability.py` roda a suíte em processo com um plugin que guarda testes ligados e resultados (pior resultado prevalece: falha > pulado > passou), cruza com os requisitos e gera Markdown (padrão) ou JSON; resumo com cobertura, aviso para requisito "Atendido" sem teste verde, saída 1 se teste ligado falhar. 17 testes unitários novos em `tests/tools/` (103 no total). **Verificação com testes temporários (removidos):** `req` com ID inexistente parou a coleta (o teste de coerência também barrou o primeiro rascunho deste registro, que citava esse ID falso); teste ligado falhando apareceu como "falhando" e o script saiu com 1; teste com dois IDs apareceu nas duas linhas. **Defeito achado e corrigido antes do commit:** a saída de progresso do pytest ia para o stdout junto com a matriz e quebrava o `--json` (`JSONDecodeError`) — causa comprovada; pytest agora escreve em stderr. Ajuste: ruff passou a aceitar o caractere `×` (usado de propósito em "requisito × teste"). Estado atual da matriz: **0 de 34** requisitos com teste (esperado até a M0.10/M1). |
| 2026-10-27 | **M0.8 concluída.** Feito: `.github/pull_request_template.md` (etapa, requisitos/testes e checklist da definição de pronto do §9.3.6 + atualização do §1/§10/§14), formulários de issue `bug.yml` (campos do §15: passos, plataforma, severidade, etapa) e `etapa.yml` (etapa, requisitos, critério de pronto, confirmação de que não está no §16), `config.yml` (sem issue em branco) e `CONTRIBUTING.md` (setup, fluxo, regras de código, Conventional Commits, "publicar é ato deliberado"). Novos ganchos do check-jsonschema: formulários e configuração de issue, e `timeout-minutes` obrigatório nos workflows. **Verificação:** ganchos verdes; um formulário com erro proposital (`lable`) foi rejeitado. O teste de coerência passou a ler também README, CONTRIBUTING e o template de PR, e confere que o checklist do PR cita check, `req`, §1, §10, §14 e Conventional Commits. **Não verificado:** aparência dos formulários no GitHub (sem remoto). |
| 2026-10-27 | **M0.7 concluída.** Feito: `docs/c4/README.md` (índice e notação), `01-contexto.md` (3 pessoas, StocKit, leitor de código de barras, planilhas/CSV, impressora/PDF) e `02-containers.md` (app desktop, arquivo `.db`, núcleo como biblioteca, SPA, API, banco da web), cada um com tabela de elementos, requisitos ligados e o que fica fora de propósito (sem sincronização, P-05). **Verificação:** página temporária com Mermaid 11.4.1 servida por `http.server` local e aberta no navegador do app; os 2 diagramas renderizaram sem erro nos temas claro e escuro, com o número esperado de nós e ligações. **O que falhou e foi corrigido:** (1) títulos longos dos grupos ("Web: local ou demo em plano gratuito") saíam cortados → encurtados; (2) o núcleo ficava no canto inferior direito com ligações longas cruzando o desenho → testadas 4 variações (ordem de declaração, layout horizontal, ligação invisível); escolhida a ligação invisível `db_desktop ~~~ core ~~~ db_web`, que centraliza o núcleo sem mudar o significado. O layout horizontal ficou largo e ilegível. Abrir `file://` direto no navegador do app só mostra snapshot estático (sem scripts) — por isso o servidor local. Teste de coerência ganhou checagens do C4 (73 casos). **Não verificado:** renderização no próprio GitHub (TP-M0-04), que usa sua própria versão do Mermaid. |
| 2026-10-27 | **M0.6 concluída.** Feito: `docs/README.md` (índice), `docs/requirements.md` (34 requisitos do antigo §8, com invariantes, casos de portão e status), `docs/glossary.md` (antigo §20 ampliado com termos de domínio, arquitetura e processo), `docs/test-plan/README.md` (template de caso manual), `docs/adr/template.md`, índice e **ADRs 001–005** (todos *Aceito*; ADR-002 registra a escolha do usuário em D-02). §8 e §20 deste arquivo viraram ponteiros. Novo `tests/docs/test_docs_consistency.py` (57 casos): todo RF/RNF, TP, INV e ADR citado existe; IDs de requisito únicos; requisitos sem caso de portão estão em "Lacunas"; ADRs seguem o template e estão no índice. **Testes negativos:** RF, TP, INV e ADR inexistentes e um ADR sem seção obrigatória — os 5 foram pegos; arquivos restaurados. Dois falsos alarmes do próprio teste corrigidos antes (o `★` dos casos críticos e a tabela de lacunas contada como duplicata). **Achado:** RF-002, RF-003, RF-016 e RF-019 **não têm caso de portão**; listados em "Lacunas conhecidas" com sugestão de caso — precisam entrar nos planos de M1, M3 e M4 antes desses portões. pre-commit agora roda o pytest também quando um `.md` muda. |
| 2026-10-27 | **M0.5 concluída (sem remoto, por pedido do usuário).** Feito: `.github/workflows/ci.yml` com job `check` em matriz Ubuntu + Windows (instala do zero e roda `tools/check.py`, hypothesis no perfil `ci`) e job `higiene` (pre-commit sem os ganchos que o check já cobre). Gatilhos: push e PR em `dev`/`main` e disparo manual. Segurança: `permissions: contents: read`, `persist-credentials: false`, actions fixadas por hash, cancelamento de execuções antigas da mesma branch. Shell `bash` também no Windows (o `pwsh` padrão não para no primeiro erro). Novo gancho `check-github-workflows` (schema oficial). **Verificação:** schema ok; workflow com erro proposital (`stepz`) rejeitado; **simulação dos passos do CI num clone limpo** (venv, instalação, check, higiene) verde em 43 s. **Não verificado (fato):** execução no GitHub — sem repositório remoto; fica para TP-M0-03 no portão. Hipótese não testada: `default_language_version: python3.14` do pre-commit acha o `python3.14` no runner Ubuntu (o setup-python costuma criar esse executável). |
| 2026-10-27 | **M0.4 concluída.** Feito: import-linter 2.15 no grupo `dev`, no `tools/check.py` (via executável do venv, pois o pacote não roda com `python -m`) e no pre-commit. Contratos: `core-puro` (forbidden: adapters, apps, tools, tests, Tkinter/CustomTkinter, Django/DRF/drf-spectacular, sqlite3, reportlab, qrcode, barcode, Faker, PyInstaller, socket/ssl/http/urllib/subprocess/multiprocessing, pytest/hypothesis) e `core-camadas` (layers: services → ports → domain). **Verificado antes de escrever:** com `include_external_packages`, o import-linter detecta módulos da biblioteca padrão e aceita proibir pacotes que ainda não existem. **Testes negativos** (arquivo temporário em `core/domain`, removido depois): `import tkinter`, `from django.db import models`, `import core.services` dentro do domain e `from adapters.sqlite import repo` — cada um quebrou o contrato certo (saída 1); `tools/check.py` também falhou. Check de volta ao verde (2,5 s). Ajuste extra: `tools/check.py` força UTF-8 nas ferramentas (acentos saíam embaralhados com a saída redirecionada no Windows). Limitação registrada em §6.2: imports dinâmicos não são detectados. |
| 2026-10-27 | **M0.3 concluída.** Feito: ferramentas em `[dependency-groups] dev` com versões exatas (verificadas no PyPI); configuração de ruff (inclui `DTZ` para datas sem fuso e `S` de segurança), mypy `strict` (testes/scripts podem ter funções sem anotação), pytest (`--strict-markers`, warnings viram erro, `importlib`), cobertura com ramos e mínimo de 90% no `core`; `tests/conftest.py` com perfis do hypothesis `dev`/`ci`; teste de pacote (`core` e subcamadas importáveis, `py.typed` presente); `tools/check.py` + `Makefile`; `.pre-commit-config.yaml` (higiene, ruff, mypy e pytest) instalado no `.git/hooks`. Resultado: check verde (8,5 s) e `pre-commit run --all-files` verde. **Teste negativo:** um arquivo proposital com import sem uso e função sem tipo fez falhar ruff, mypy e cobertura, com código de saída 1; arquivo removido em seguida. Causa da escolha do script Python: não há GNU make no Windows (o `make` do PATH é do Embarcadero). Lição: a instalação pelo PyPI teve timeouts de leitura com novas tentativas; terminou, mas a rede pode atrasar a configuração em máquina limpa (TP-M0-01). |
| 2026-10-27 | **M0.2 concluída.** Feito: verificadas no PyPI as versões e o suporte a Python 3.14 de Django, DRF, PyInstaller, CustomTkinter, setuptools e pip; CustomTkinter 6.0.0 testado de verdade num venv descartável (abre janela no 3.14.3). Criados `pyproject.toml` (distribuição `stockit`, `core` sem dependências, extras `desktop`/`web`/`package` com versões exatas), esqueleto `core/{domain,services,ports}` com `py.typed`, `.python-version` (3.14) e `.nvmrc` (24). Venv `.venv` com 3.14.3, `pip install -e .` ok; `import core` de fora do repositório resolve para o código-fonte (editável confirmado). README ganhou o passo a passo de setup. Decisões: D-03 = CustomTkinter (usuário); D-04 = Python 3.14, Node 24 LTS, Django 5.2.18 LTS. Lição: a versão mais nova do Django (6.1.2) não é LTS; o documento pede LTS, por isso 5.2. Pendência registrada em §5.1: lock de dependências transitivas. |
| 2026-10-27 | **M0.1 concluída.** Feito: `git init` na pasta definida (D-06), `.gitignore` (Python, Node, Django, bancos `.db`/`.sqlite3`, `.env`, caches de ferramentas), `.gitattributes` (LF no repo, CRLF em `.bat`/`.cmd`/`.ps1`), LICENSE MIT, README mínimo, commit inicial na `main` e branch `dev` criada a partir dela (trabalho segue na `dev`). Este arquivo já estava na raiz da pasta; atualizado o nome para **StocKit**. Resultado: ok, nada publicado (sem remoto, sem push). Decisões: D-01 = StocKit (escolha do usuário); D-05 = MIT (usuário sem preferência → recomendação do documento); D-06 = pasta atual. Lição: o titular do copyright na LICENSE usa o usuário GitHub `KaueChristian` (§2) — *hipótese* de que é o nome desejado; ajustar se não for. |
| 2026-10-27 | **Planejamento inicial.** Revisado o portfólio (`kauechristian.github.io`): a seção de projetos só renderiza placeholders de template e **não há repositório do Inventory Manager**; confirmado pelo usuário que o projeto começa do zero. Pesquisadas referências no GitHub (§21). Decisões tomadas: universal (sem nicho), duas plataformas com núcleo compartilhado, sem servidor dedicado, desktop primeiro. Este arquivo criado com o roadmap M0–M7 e portões de integridade. Nenhum código escrito. |

---

## 15. Bugs encontrados

> Um bug por linha. Status: `ABERTO` · `EM ANÁLISE` · `CORRIGIDO` · `NÃO REPRODUZIDO` · `ADIADO`.
> Antes de corrigir: causa raiz comprovada (fato) — hipótese não vira correção.

| ID | Data | Milestone/Etapa | Descrição e passos | Severidade | Causa raiz (fato/hipótese) | Status | Correção / teste de regressão |
|---|---|---|---|---|---|---|---|
| BUG-01 | 2026-10-27 | M0 / portão (TP-M0-03) | `python tools/check.py` quebra com `FileNotFoundError` na etapa import-linter quando roda num Python **sem venv** no Windows (caso do runner `windows-latest`). Passos: instalar o projeto no Python do sistema, rodar o check | Alta (CI do Windows sempre vermelho) | **Fato:** `SCRIPTS = Path(sys.executable).parent`; fora de venv, no Windows, os scripts ficam em `<python>\Scripts\` (log do run 40553841261) | CORRIGIDO | `4d6867b`: `sysconfig.get_path("scripts")` + ferramenta ausente vira falha no resumo; `tests/tools/test_check.py`; CI verde no Windows (run 40554318491) |
| BUG-02 | 2026-10-27 | M1.1 (achado ao conferir a matriz) | `python tools/traceability.py > m.md` sai com `UnicodeEncodeError` no Windows: com stdout redirecionado, o Python usa cp1252, que não tem o "≥" do texto da RNF-001. Com `--output` funciona | Baixa (o portão M0 usou `--output`; o README ensina o redirecionamento) | **Fato:** traceback aponta `sys.stdout.write`; reproduzido com `PYTHONIOENCODING=cp1252` | CORRIGIDO | `write_stdout` reconfigura o stdout para UTF-8; teste `test_write_stdout_survives_a_cp1252_console` (falha sem a correção) |

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
| R-10 | Duas saídas simultâneas passam pela conferência de saldo antes de qualquer uma gravar (conferir-e-gravar) | Na memória não há concorrência; no SQLite a UoW abre transação com `BEGIN IMMEDIATE` (M2.5) e a suíte de contrato testa duas UoWs concorrentes; na web, transação `SELECT ... FOR UPDATE`/serializável (M5) |

---

## 18. Dúvidas e decisões em aberto (dependem do usuário)

| ID | Pergunta | Recomendação | Prazo |
|---|---|---|---|
| ~~D-01~~ | ~~Nome definitivo do projeto~~ | ✅ **StocKit** (§19, 2026-10-27) | M0.1 |
| ~~D-02~~ | ~~Persistência do desktop~~ | ✅ **SQLite próprio** (escolha do usuário; ADR-002, 2026-10-27) | M0.6 |
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
| 2026-10-27 | Comando de qualidade = `python tools/check.py`; `make check` só chama o script | Funciona igual no Windows (sem GNU make) e no CI |
| 2026-10-27 | Ferramentas de dev em `[dependency-groups]` (PEP 735), não em extras | Não fazem parte do pacote publicado; `pip install --group dev` (pip ≥ 25.1) |
| 2026-10-27 | Cobertura mínima de 90% já ativa desde a M0 | Mais simples ligar agora do que lembrar de ligar na M1 (RNF-001) |
| 2026-10-27 | Repositório **público** em `github.com/KaueChristian/StocKit` (conta `KaueChristian`, a mesma do LICENSE); commits publicados com o e-mail do autor como estão | Pedido do usuário: projeto de desenvolvimento/portfólio, sem nada sensível. Antes do push: busca por segredos em todo o histórico (nenhum) |
| 2026-10-27 | PR de teste de portão: commits de violação feitos pela API do GitHub; PR fechado sem merge | Simula uma edição feita no site (sem pre-commit), que é o caso que o CI precisa barrar; não exige pular ganchos locais |
| 2026-10-27 | Nomes de código em **inglês** no domínio (`UnitOfMeasure`, `Dimension`, `Quantity`), mesmo onde o roadmap escreveu em PT-BR (`UnidadeDeMedida`); o glossário liga termo ↔ código | Regra do §2 (identificadores em inglês, interface em PT-BR); o roadmap usa nomes de trabalho |
| 2026-10-27 | Quantidades: 6 casas, 12 dígitos inteiros, conversão exata com um arredondamento half-even; operações só na mesma unidade (**ADR-006**) | Define o "arredondamento definido" da INV-04 e garante o mesmo resultado nas duas plataformas (RNF-004) |
| 2026-10-27 | Embalagem (caixa com 12) é uma unidade de **contagem** comum, sem conversão por item | Mais simples; caixas de tamanhos diferentes viram unidades diferentes. *Hipótese* de que basta — reavaliar na M1.2 (`Item`) e na M1.12 (perfis) |
| 2026-10-27 | Definição de campo vale para um **conjunto de tipos de item** (`kinds`), não por categoria | O ADR-005 fala em "tipo de item"; tipos são poucos e estáveis, e os perfis (M1.12) configuram por tipo |
| 2026-10-27 | Campo obrigatório novo **não** revalida itens existentes; é cobrado na próxima edição de cada item | Revalidar tudo ao criar uma definição travaria o cadastro inteiro; a regra fica visível na primeira edição |
| 2026-10-27 | Serviços de cadastro de item (`register_item`, `update_item`) nascem na M1.11 | Validar campos personalizados precisa das definições, que estão no repositório; o serviço é o lugar dessa regra (§0: regra só em `core/services`) |
| 2026-10-27 | Conversão de/para JSON dos campos (`encode_values`/`decode_values`) fica no domínio | A regra "número vira texto decimal" (ADR-005) é a mesma no SQLite e no Django; os dois adaptadores só chamam |
| 2026-10-27 | Números de série vão **na movimentação** (`serials`), e a posição de cada série é derivada do livro | Mesmo princípio do saldo (ADR-004): nada de "tabela de séries" editável que possa discordar do livro |
| 2026-10-27 | Para serializado, a política `ALLOW` **não** se aplica: a série tem de estar onde sai | Uma unidade física não sai de onde não está; saldo negativo de serializado não tem significado |
| 2026-10-27 | Item serializado não controla lote | Cada unidade já é rastreada pela série; lote + série complicaria o FEFO sem caso de uso no escopo |
| 2026-10-27 | "Estado" do RF-009 = em estoque num local ou fora | É o que o livro sabe. Estados como "em manutenção" ou "emprestado" podem ser locais (ex.: local "Manutenção"); se precisar de mais, vira requisito novo |
| 2026-10-27 | Filtro por série feito em memória sobre as movimentações do item (a porta não filtra por série) | Simples e correto; se pesar, a porta ganha filtro e índice depois da medição (M2.7) |
| 2026-10-27 | FEFO **pula lote vencido** na data da saída; baixar estoque vencido (perda, devolução) exige informar o lote | Vender vencido por automatismo é o erro que o FEFO existe para evitar; a mensagem de falta avisa quando há estoque vencido |
| 2026-10-27 | Saída sem lote é **repartida** em várias movimentações (uma por lote); `record_movement` devolve tupla | Saldo por lote continua exato (INV-01 por lote); a tela mostra de quais lotes saiu |
| 2026-10-27 | Com `ALLOW`, o que faltar sai do **último lote válido** | Algum lote precisa receber a diferença; o último é o que menos atrapalha o FEFO das próximas saídas |
| 2026-10-27 | Lote é cadastrado antes da entrada (`create_lot`); entrada não cria lote sozinha | Código e validade são conferidos uma vez; evita lote duplicado por digitação. A tela da M3 pode fazer os dois passos num formulário |
| 2026-10-27 | Transferência de item com lote exige o lote (sem FEFO) | Transferência move um lote físico concreto; repartir automaticamente esconderia o que foi movido |
| 2026-10-27 | Transferência confere a política de saldo só na **origem** | O destino só ganha; a soma total não muda (INV-03), então só a origem pode ficar negativa |
| 2026-10-27 | `record_movement` e `transfer_stock` no mesmo módulo, com as regras comuns em funções internas | Uma regra (cadastro ativo, unidade exata, lote, saldo) tem um lugar só; os dois serviços não divergem |
| 2026-10-27 | Saldo de um local **inclui os sublocais** por padrão (`include_sublocations=False` para o saldo só dele) | "Quanto tem no depósito?" quer dizer o depósito inteiro; o saldo próprio serve ao extrato e à contagem |
| 2026-10-27 | Saldo em uma data usa `occurred_at` (inclusive), não `recorded_at` | A pergunta é "quanto havia naquele dia"; lançamento retroativo corrige o passado de propósito. Auditoria de quando foi lançado usa `recorded_at` |
| 2026-10-27 | Saldo por local lista locais que **zeraram** | "Zerou" e "nunca teve" são informações diferentes para quem repõe |
| 2026-10-27 | Saldo calculado somando todas as movimentações do item a cada consulta | Mais simples e correto por construção; desempenho é medido na M2.7 (RNF-002) antes de qualquer otimização (§0) |
| 2026-10-27 | Serviços com nomes em inglês (`record_movement`, `RecordMovement`) | Mesma regra do §2 aplicada às entidades; o roadmap usa nomes de trabalho |
| 2026-10-27 | Política de saldo negativo entra como **parâmetro** do serviço (padrão `FORBID`) até a configuração do sistema (M1.12) | INV-05 testável já; a M1.12 só passa a ler o valor da configuração |
| 2026-10-27 | Saldo conferido em **toda a linha do tempo** a partir da movimentação, não só no fim | Saída retroativa coberta na data dela pode deixar negativo um dia posterior; o extrato e o "saldo em uma data" (RF-006) mostrariam número negativo que a política proíbe |
| 2026-10-27 | Conversão de unidade no registro precisa ser **exata**; se arredondaria, o registro é recusado | O livro é a verdade (ADR-004): guardar 0,083333 cx no lugar de 1 un perde valor para sempre |
| 2026-10-27 | `recorded_at` na movimentação (confirma a hipótese da M1.3); data futura recusada | Auditoria de lançamento retroativo; `occurred_at ≤ recorded_at` impede lançar o futuro sem regra extra |
| 2026-10-27 | Item/local/parte inativos não recebem movimentação nova | Inativar é "não usar mais"; o histórico continua visível |
| 2026-10-27 | Item com lote exige lote em toda movimentação até a M1.9; existência do lote não é conferida ainda | FEFO (saída sem lote) e a entidade `Lote` chegam juntos na M1.9 |
| 2026-10-27 | `adapters-sem-apps` proíbe também `core.services` | §6.2 já dizia que adaptadores importam só `core.ports`/`core.domain`; agora é fiscalizado |
| 2026-10-27 | UoW em memória com estado confirmado compartilhado e rascunho por bloco | Imita várias conexões a um banco: só o `commit` publica, e os testes de atomicidade (M1.6, M1.8) ficam honestos antes do SQLite |
| 2026-10-27 | `FixedClock` e `SystemClock` em `adapters/clock.py` (fora de `memory`) | Relógio não é armazenamento; os dois servem a qualquer combinação de adaptadores |
| 2026-10-27 | Nenhum repositório tem `delete`; cadastro se **inativa** | Movimentações antigas apontam para itens, locais e partes; apagar quebraria o histórico (INV-02, RF-012) |
| 2026-10-27 | `get` nunca devolve `None` (levanta `NotFoundError`); `find_by_sku` é a única busca que devolve `None` | Ausência inesperada vira erro de domínio claro; busca por código lido no scanner é o caso em que "não achou" é normal |
| 2026-10-27 | Portas descrevem o comportamento nas docstrings; quem cobra é a suíte de contrato (M2.6). Na M1.4 os testes cobram a **forma** das portas | Interface sem implementação não tem comportamento para testar; a memória (M1.5) e o SQLite (M2) passam pelo mesmo contrato |
| 2026-10-27 | Repositório de lotes fica para a M1.9 | A entidade `Lote` nasce na M1.9; a porta nasce junto |
| 2026-10-27 | Movimentação com **quantidade sempre positiva** e direção dada pelo tipo; ajuste e devolução viram dois tipos cada (para mais/para menos; de cliente/a fornecedor) | Um sinal só, sem ambiguidade: não existe "saída de −5". O saldo soma `signed_quantity` (INV-01) |
| 2026-10-27 | Motivo obrigatório só em ajuste e perda | São os únicos tipos que mudam o saldo sem contraparte (fornecedor, cliente, outro local); auditoria |
| 2026-10-27 | Custo unitário **opcional** na movimentação por enquanto | Cozinha/oficina podem não controlar custo; se a entrada precisa de custo é decisão da valoração (M1.14, D-07) |
| 2026-10-27 | Movimentação guarda a quantidade **já na unidade base do item**; converter e conferir a unidade é do serviço (M1.6) | A movimentação não conhece o item; o serviço conhece os dois. *Hipótese:* `registrado_em` (hora do registro pelo `Clock`) será acrescentado na M1.6 para auditoria de lançamento retroativo |
| 2026-10-27 | Entidades imutáveis (dataclass congelada) com identidade por tipo + `id`; edição por `dataclasses.replace` | Nada muda "por baixo" de um repositório ou Unit of Work; a validação roda em toda versão nova; comparar duas versões da mesma entidade é trivial |
| 2026-10-27 | IDs = UUID gerado no domínio, com `NewType` por entidade | Desktop e web criam IDs sem coordenação (paridade, futura sincronização B-01); mypy impede trocar ID de local por ID de item. O dataset demo pode passar IDs fixos |
| 2026-10-27 | SKU normalizado para **maiúsculas**, sem espaços | Busca e leitor de código de barras não dependem de caixa; unicidade simples (garantida no repositório, M1.5) |
| 2026-10-27 | Regras que dependem do **conjunto** de locais (ciclo, pai existente, nome entre irmãos) ficam em `LocationTree`, não no `Location` | Um local sozinho não sabe se forma ciclo; a árvore é o ponto único de validação, usado pelos serviços e pelo saldo por local (INV-08) |
| 2026-10-27 | Categoria sem hierarquia; ponto de reposição e campos personalizados fora do `Item` por enquanto | O documento não pede categoria hierárquica; ponto de reposição é do M4 (RF-018) e campos personalizados da M1.11 — entram nas etapas deles |
| 2026-10-27 | Base de erros de domínio (`DomainError` e três subclasses) criada já na M1.1 | A conversão precisa recusar valores; a M1.13 completa a hierarquia em vez de começar do zero |
| 2026-10-27 | Ao fechar milestone, a `main` recebe a `dev` por **fast-forward**, e a tag é **anotada** e fica na `main` | A `main` só recebe trabalho já aprovado no portão, então não há divergência a mesclar; a tag anotada guarda data e autor do fechamento |
| 2026-10-27 | IDs de bug no §15 usam `BUG-xx` | `B-xx` já identifica o backlog (§12) |
| 2026-10-27 | M0.10: **testes reais da RNF-006** no lugar do "teste dummy" ligado a um RF; TP-M0-05 passa a ser verificado com RNF-006 | Um dummy marcado com um RF faria a matriz mostrar o requisito como coberto sem nada verificado; os testes da RNF-006 ainda fecham o risco de versões divergentes entre pyproject, pre-commit e CI |
| 2026-10-27 | Sentinela do import-linter roda em subprocesso sobre cópia temporária | Em processo, o `core` já importado pela suíte seria analisado no lugar da cópia; o repositório nunca é alterado pelo teste |
| 2026-10-27 | Rastreabilidade por plugin do pytest em processo (não junit XML) | Usa os próprios markers e resultados do pytest, sem formato intermediário nem configuração extra |
| 2026-10-27 | Matriz gerada sob demanda, **não versionada** | Resultado de testes muda a cada execução; uma cópia commitada ficaria velha. Versões "fotografadas" vão como evidência dos portões (§11, `docs/test-plan/`) e no README final (M7.5) |
| 2026-10-27 | ID de requisito inexistente no `req` interrompe a coleta | Erro de digitação num ID deixaria um requisito "sem teste" sem ninguém perceber |
| 2026-10-27 | C4 em Mermaid `flowchart` com cores do C4, não a sintaxe `C4Context` | `C4Context` ainda é experimental no Mermaid, com layout pouco previsível no GitHub; `flowchart` renderiza igual em todo lugar |
| 2026-10-27 | Só níveis 1 e 2 do C4 | Componentes e código já ficam claros pelo próprio código, ADRs e contratos do import-linter |
| 2026-10-27 | Núcleo desenhado como **biblioteca dentro dos containers**, não como container próprio | É o que acontece em execução: roda no mesmo processo do app desktop e da API |
| 2026-10-27 | Desktop com **repositórios próprios sobre `sqlite3`** (D-02, ADR-002) | Escolha do usuário; executável leve e demonstração de portas/adaptadores; Django ORM headless segue como plano B (P-08) |
| 2026-10-27 | Requisitos e glossário movidos para `docs/` (fonte única); §8 e §20 viram ponteiros | Duas cópias divergiriam (R-05); o teste de coerência impede citar ID inexistente |
| 2026-10-27 | Requisitos ganharam colunas "Invariantes" e "Portão" e uma tabela de lacunas | Rastreabilidade requisito ↔ caso de portão desde já; expôs 4 requisitos sem caso de portão |
| 2026-10-27 | ADRs numerados com 3 dígitos (`ADR-001`), seções obrigatórias checadas por teste | Mesmo padrão já citado neste arquivo; automatiza o TP-M0-06 |
| 2026-10-27 | CI em **Ubuntu e Windows** | Windows é a plataforma do desktop e do `.exe`; pega cedo problemas de caminho e encoding. Custo: minutos ×2 no Windows em repositório privado |
| 2026-10-27 | CI também em push na `main` (além de `dev` e PRs) | `main` é a branch estável; precisa provar que está verde |
| 2026-10-27 | **Quarentena de 14 dias** para actions e ganchos novos; actions fixadas por hash de commit | Reduz risco de cadeia de suprimentos (tag sequestrada ou versão comprometida recém-publicada) |
| 2026-10-27 | Contrato extra `core-camadas` (services → ports → domain) | Consequência direta do hexagonal (§6.1); barato de ligar agora, caro de consertar depois |
| 2026-10-27 | `core` também proíbe rede, subprocessos e bibliotecas de teste | Regra "nada de I/O" do §0; `os`/`pathlib` ficaram liberados por enquanto (reavaliar na M1.12, loader de perfis) |
| 2026-10-27 | pre-commit roda mypy e pytest em ambientes isolados do próprio pre-commit | Funciona sem venv ativo; o `core` não tem dependências, então o ambiente isolado basta. Custo: versões repetidas em dois arquivos |

**Índice de ADRs** ([`docs/adr/`](docs/adr/README.md), 001–005 criados na M0.6, todos *Aceito*):
[ADR-001](docs/adr/001-nucleo-hexagonal.md) núcleo hexagonal · [ADR-002](docs/adr/002-sqlite-no-desktop.md) SQLite no
desktop · [ADR-003](docs/adr/003-django-orm-na-web.md) Django ORM na web ·
[ADR-004](docs/adr/004-livro-de-movimentacoes.md) livro de movimentações ·
[ADR-005](docs/adr/005-campos-personalizados-em-json.md) campos personalizados em JSON ·
[ADR-006](docs/adr/006-quantidades-com-escala-fixa.md) escala e arredondamento das quantidades (M1.1).

---

## 20. Glossário

> **Movido para [`docs/glossary.md`](docs/glossary.md) na M0.6** — fonte única do vocabulário (domínio, arquitetura e
> processo).

---

## 21. Referências

> Levantadas em 2026-10-27 por busca; **qualidade e licença não foram verificadas** — checar antes de reutilizar qualquer código.

- Estrutura de apps de estoque em Tkinter/SQLite: [Zynox-Tech/Inventory-Management-System](https://github.com/Zynox-Tech/Inventory-Management-System), [nishant0820/Inventory-Management-System](https://github.com/nishant0820/Inventory-Management-System), [datapro/inventory-system-with-python](https://github.com/datapro/inventory-system-with-python) (exportação CSV), [For-Community/Inventory-Management-System](https://github.com/For-Community/Inventory-Management-System) (tema claro/escuro).
- Domínio e histórico de estoque: [InvenTree](https://github.com/inventree/InvenTree) (histórico de rastreio, itens serializados, plugins); [Snipe-IT](https://www.alternativeto.net/software/snipe-it/about/) (atribuição, localização e histórico completo do ativo).
- Fórmulas (ABC, EOQ, ponto de reposição, estoque de segurança): [supplychainpy](https://pypi.org/project/supplychainpy/0.0.5rc3/), [invcalc](https://pypi.org/project/invcalc/).
- Previsão de ruptura: [InvenTrack](https://dev.to/eymenozt/pen-source-grocery-store-management-app-with-python-tkinter-20ca) (abordagem sobre histórico de movimentações).
- Documentos-modelo deste arquivo: `C:\Users\Desenvolvedor\Documents\port\site3d\project_context.md` e `C:\PROJETOS\Folha\Projeto\Library_Tron\DOCUMENTO_CHEFE_140388.md`.
