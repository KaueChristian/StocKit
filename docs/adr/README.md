# Registros de decisão de arquitetura (ADRs)

Cada ADR registra uma decisão de arquitetura: contexto, decisão, consequências e alternativas descartadas.
Para criar um novo, copie o [template](template.md). Decisões menores ficam só no `PROJECT_CONTEXT.md` §19.

| ADR | Título | Status |
|---|---|---|
| [ADR-001](001-nucleo-hexagonal.md) | Núcleo hexagonal em Python puro compartilhado pelas duas plataformas | Aceito |
| [ADR-002](002-sqlite-no-desktop.md) | Desktop persiste em SQLite com repositórios próprios | Aceito |
| [ADR-003](003-django-orm-na-web.md) | Web persiste pelo Django ORM, como adaptador das mesmas portas | Aceito |
| [ADR-004](004-livro-de-movimentacoes.md) | Estoque como livro de movimentações imutáveis; saldo sempre derivado | Aceito |
| [ADR-005](005-campos-personalizados-em-json.md) | Campos personalizados guardados em JSON e validados por definição | Aceito |
