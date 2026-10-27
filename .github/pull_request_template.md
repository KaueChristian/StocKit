## Etapa

<!-- ID da etapa do roadmap (PROJECT_CONTEXT.md §10), ex.: M1.6. Um assunto por PR. -->
Etapa: M

## O que muda e por quê

<!-- Comportamento antes → depois. Fatos verificados; hipóteses marcadas como hipóteses. -->

## Requisitos e testes

<!-- Requisitos afetados (docs/requirements.md) e os testes marcados com @pytest.mark.req que os cobrem. -->
- Requisitos:
- Testes:

## Definição de pronto (PROJECT_CONTEXT.md §9.3.6)

- [ ] Código com teste (o teste falha sem a mudança)
- [ ] Requisito referenciado com `@pytest.mark.req("RF-xxx")` quando aplicável
- [ ] Documentação atualizada no mesmo PR (`docs/`, README, ADR se a decisão for arquitetural)
- [ ] `python tools/check.py` verde (ruff, mypy, import-linter, pytest + cobertura)
- [ ] `PROJECT_CONTEXT.md` atualizado: painel (§1), status da etapa (§10) e linha no diário (§14)
- [ ] Bugs (§15), ideias descartadas (§16) e decisões (§19) registrados, se houver
- [ ] Commits no padrão Conventional Commits, um assunto por commit

## Como verificar

<!-- Passos para quem revisa reproduzir o resultado. -->
