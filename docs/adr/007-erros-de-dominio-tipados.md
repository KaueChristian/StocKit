# ADR-007: Erros de domínio com código estável, categoria e detalhes estruturados

## Status

Aceito — 2026-10-27

## Contexto

O núcleo recusa operações em muitos pontos (saldo insuficiente, número de série fora do lugar, campo
personalizado obrigatório ausente, cadastro inativo…). Até a M1.12 cada recusa era uma exceção com
mensagem em PT-BR, e só duas traziam dado estruturado (o campo e o caminho no perfil). Faltava:

- um identificador estável para a API (M5) e para os testes de contrato HTTP (TP-M5-04) — a
  mensagem muda de texto, o identificador não;
- uma categoria que diga à interface **como** reagir (destacar campo, "não encontrado", conflito,
  regra de negócio) sem conhecer cada regra (§6.2: views e presenters não contêm regra);
- os dados do erro (SKU, local, quanto falta) sem analisar texto.

O núcleo não pode conhecer HTTP nem Tkinter (ADR-001).

## Decisão

- Todo erro do núcleo é subclasse de `DomainError` (`core/domain/errors.py`) e tem:
  - `code`: texto estável, minúsculo, com o prefixo da categoria (`rule.insufficient_stock`);
  - `kind`: uma de quatro categorias (`ErrorKind`):
    - `invalid`: entrada inválida;
    - `not_found`: registro inexistente;
    - `conflict`: unicidade violada;
    - `rule`: regra de negócio recusou;
  - `message`: texto para o usuário final, em PT-BR;
  - `details`: dados estruturados, e `to_dict()` com tudo em JSON simples (`Decimal`, data, UUID,
    quantidade e enum viram texto ou número).
- Hierarquia: `ValidationError` (`invalid`, com `field`), `NotFoundError`, `ConflictError` e
  `BusinessRuleError` (`rule`), com subclasses específicas. A árvore completa está na docstring do
  módulo.
- O núcleo **só** levanta subclasses específicas: nada de `ValueError`, nem de `DomainError` crua.
  Isso é fiscalizado por um teste que lê o código-fonte do `core`.
- Código é contrato: mudar o significado de um código é quebra. Para mudar, cria-se um código novo.
- Mapeamento sugerido nas bordas (fora do núcleo):

| Categoria | Desktop (M3) | HTTP na API (M5) |
|---|---|---|
| `invalid` | Destaca o campo de `details.field` com a mensagem | 422 |
| `not_found` | Aviso "não encontrado" | 404 |
| `conflict` | Aviso perto do campo único (SKU, código) | 409 |
| `rule` | Diálogo com a mensagem; detalhes para ação (ex.: "repor") | 422 |

  O corpo de erro da API segue *problem details* (RFC 9457): `type`, `title`, `status` e `detail`,
  mais `code`, `kind` e `details` do `to_dict()`.

## Consequências

- **Positivas:**
  - telas e API tratam qualquer erro de domínio de um jeito só, por categoria;
  - testes de API comparam códigos, não textos;
  - mensagens podem ser reescritas sem quebrar clientes;
  - o mesmo dicionário serve para log.
- **Negativas / custos:**
  - cada erro novo precisa de classe e código;
  - os detalhes de cada código viram parte do contrato e precisam ser documentados quando a API
    for publicada (M5).
- **Como verificar:** `tests/core/domain/test_errors.py`:
  - códigos únicos, no formato certo e com o prefixo da categoria;
  - `to_dict()` serializável;
  - o núcleo só levanta erros específicos.

  Testes de serviço conferem os detalhes de saldo insuficiente, série, inativo e "não encontrado".
  Na M5, TP-M5-04.

## Alternativas consideradas

| Alternativa | Por que não |
|---|---|
| Exceções genéricas (`ValueError`) com mensagem | A borda teria de adivinhar a categoria pelo texto; erro de regra viraria erro 500 |
| Status HTTP dentro do núcleo | O núcleo não conhece HTTP (ADR-001); o desktop não usa HTTP |
| Devolver resultado (`Ok`/`Err`) em vez de exceção | Muda a assinatura de todos os serviços; Python idiomático usa exceção, e a Unit of Work já desfaz tudo quando uma exceção sai do bloco |
| Um código por mensagem (centenas de códigos) | Granularidade demais; a categoria e os detalhes já distinguem os casos que a interface trata diferente |

## Referências

- `PROJECT_CONTEXT.md` §6.2, §10 (M1.13, TP-M5-04)
- Requisitos: RF-026
- ADR-001 (núcleo sem frameworks)
