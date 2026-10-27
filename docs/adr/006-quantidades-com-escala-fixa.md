# ADR-006: Quantidades com escala fixa de 6 casas e conversão com um único arredondamento half-even

## Status

Aceito — 2026-10-27

## Contexto

A INV-04 exige que a conversão de unidade, de ida e volta, preserve o valor "com `Decimal` e arredondamento
definido", mas o arredondamento não estava definido. Fatos que pesam:

- algumas conversões não têm resultado exato em decimal (1 un em caixa com 12 = 0,0833…), então algum
  arredondamento é inevitável;
- o mesmo valor vai ser gravado no SQLite (texto decimal, ADR-002) e no Django ORM (`DecimalField`, ADR-003), e a
  paridade (RNF-004) exige resultados idênticos nas duas plataformas;
- contas com `Decimal` dependem do contexto global (precisão de 28 dígitos, modo de arredondamento), que qualquer
  biblioteca pode alterar; e arredondar duas vezes (contexto e depois escala) pode errar no último dígito.

## Decisão

- **Escala fixa:** toda `Quantity` tem no máximo **6 casas decimais** e **12 dígitos inteiros**
  (|valor| < 10¹²). Valor fora disso é recusado com `InvalidQuantityError`, sem arredondar em silêncio.
- **Unidades por grandeza:** cada `UnitOfMeasure` tem grandeza (`Dimension`: contagem, massa, volume,
  comprimento) e **fator** para a unidade base da grandeza (kg = 1, g = 0,001, dz = 12). Só se converte dentro
  da mesma grandeza. Embalagem (caixa com 12) é uma unidade de contagem como outra qualquer.
- **Conversão:** calcula o valor exato com `Fraction` e arredonda **uma única vez** para 6 casas com
  **ROUND_HALF_EVEN**. Não usa o contexto global do `decimal`.
- **Limite provado da INV-04:** ida e volta de A para B erra no máximo ½·10⁻⁶·(1 + f_B/f_A) na unidade A; o erro é
  **zero** quando A cabe um número inteiro de vezes em B (kg → g → kg, dz → un → dz).
- **Operações explícitas:** soma, subtração e comparação só entre quantidades da mesma unidade; para misturar
  unidades, converte-se antes (`q.to(unidade)`). Igualdade é de valor e unidade (1 kg ≠ 1000 g).

## Consequências

- **Positivas:** resultado igual em qualquer máquina e plataforma; sem `float`; o erro máximo de conversão é
  conhecido e testado; persistência simples (`DecimalField(max_digits=18, decimal_places=6)` na web e texto no
  SQLite).
- **Negativas / custos:** quantidades menores que 0,000001 não existem (suficiente para estoque: 1 mg em kg cabe);
  converter para uma unidade maior perde precisão dentro do limite acima; somar unidades diferentes exige
  conversão explícita no código que chama.
- **Como verificar:** `tests/core/domain/test_quantity.py` (marcados com `req("RF-010")`): propriedades do
  hypothesis para o limite de ida e volta, ida e volta exata e arredondamento único; caso do meio exato
  (half-even); caso de portão TP-M1-03.

## Alternativas consideradas

| Alternativa | Por que não |
|---|---|
| `float` | Proibido pelo princípio 4 (`PROJECT_CONTEXT.md` §4): erro binário em quantidade e dinheiro |
| `Decimal` com o contexto global | Resultado depende de configuração externa; risco de arredondamento duplo |
| `Fraction` como tipo da quantidade (sem arredondar) | Exato, mas não grava em `DecimalField` nem em texto decimal sem arredondar de qualquer jeito, e exibe mal |
| Escala de 3 casas | Não representa 1 mg em kg nem frações de embalagem com precisão útil |
| Somar unidades diferentes convertendo sozinho | Esconde um arredondamento dentro de uma soma; prefere-se a conversão explícita |

## Referências

- `PROJECT_CONTEXT.md` §4 (princípio 4), §7.2 (INV-04), §10 (M1.1, TP-M1-03)
- Requisitos: RF-010, RNF-004
- ADR-002, ADR-003 (persistência das quantidades)
