# ADR-003: Web persiste pelo Django ORM, como adaptador das mesmas portas

## Status

Aceito — 2026-10-27

## Contexto

A web usa Django + Django REST Framework (§5.2). O Django traz ORM, migrações, admin, autenticação e integração com o
DRF e o drf-spectacular. A regra de negócio, porém, mora no núcleo (ADR-001) e não pode depender do Django.

## Decisão

A web implementa as portas do núcleo num adaptador `adapters/django_orm`:

- models e migrações do Django só **representam dados**; nenhuma regra em `save()`, signals ou managers;
- o adaptador converte models ↔ objetos de domínio e implementa repositórios e `UnitOfWork`
  (`transaction.atomic`);
- movimentações são append-only também aqui: o repositório não expõe update/delete (ADR-004);
- quantidades e custos em `DecimalField`; datas com `USE_TZ = True` (UTC);
- views do DRF chamam `core.services` e traduzem erros de domínio em respostas padronizadas (M5.6).

Banco da web: SQLite em uso local e demo; Postgres só se um dia houver uso real (R-08). Versão: Django 5.2 LTS.

## Consequências

- **Positivas:** aproveita migrações, admin e o ecossistema do Django sem prender a regra a ele; a web herda o mesmo
  comportamento do desktop.
- **Negativas / custos:** mapeamento model ↔ domínio; não dá para usar recursos "mágicos" do ORM (signals,
  `save()` com regra) — exige disciplina e revisão.
- **Como verificar:** suíte de contrato também contra `django_orm` (M5.3, TP-M5-01); paridade com JSON dourado
  (M5.10, TP-M5-02); import-linter garante que o `core` não importa `django`.

## Alternativas consideradas

| Alternativa | Por que não |
|---|---|
| Regra nos models/serializers do Django (estilo "fat models") | Duplicaria a regra do desktop e quebraria a paridade |
| Reusar o adaptador SQLite (`sqlite3`) dentro do Django | Perderia migrações, admin e transações integradas; dois mecanismos de conexão no mesmo processo |
| FastAPI + SQLAlchemy | Stack escolhida para a web é Django + DRF (§5.2); trocar exigiria nova decisão |

## Referências

- `PROJECT_CONTEXT.md` §5.2, §6.2, §6.3, §17 (R-01, R-08)
- Requisitos: RF-026, RNF-004
