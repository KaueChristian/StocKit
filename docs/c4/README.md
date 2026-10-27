# Diagramas C4

Visão da arquitetura em dois níveis do [modelo C4](https://c4model.com/):

| Nível | Arquivo | Pergunta que responde |
|---|---|---|
| 1 — Contexto | [`01-contexto.md`](01-contexto.md) | Quem usa o StocKit e com o que ele conversa? |
| 2 — Containers | [`02-containers.md`](02-containers.md) | Quais aplicações e bancos formam o sistema, e como se ligam? |

Os níveis 3 (componentes) e 4 (código) não são desenhados: o código e os ADRs ([`../adr/`](../adr/README.md)) já
cobrem esse detalhe.

## Notação

Os diagramas usam `flowchart` do Mermaid com as cores do C4, e não a sintaxe `C4Context` (ainda experimental no
Mermaid e com layout pouco previsível no GitHub).

| Cor | Elemento |
|---|---|
| Azul escuro | Pessoa |
| Azul | O sistema StocKit (nível 1) ou um container dele (nível 2) |
| Azul com borda tracejada | Biblioteca que roda dentro de outro container (o núcleo) |
| Cinza | Sistema ou dispositivo externo |
| Cilindro | Armazenamento de dados |

Cada elemento traz `[tipo: tecnologia]` e, entre parênteses no texto, o milestone em que é construído.

## Como manter

- Mudou um container, uma tecnologia ou uma ligação → atualizar o diagrama **no mesmo commit** (§0.7).
- Para conferir a renderização antes do push: colar o bloco em <https://mermaid.live> ou abrir o arquivo no GitHub.
- `tests/docs/test_docs_consistency.py` confere que cada arquivo de nível tem exatamente um bloco `mermaid`.
