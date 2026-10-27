"""Lotes e validade (M1.9, RF-008, INV-06).

Um lote agrupa unidades de um item com o mesmo código e, se o item controla validade, a mesma data
de validade. O saldo do lote vem do livro, como qualquer saldo (ADR-004).

FEFO (*First Expired, First Out*): numa saída sem lote informado, consome primeiro o lote que vence
primeiro. ``fefo_order`` define essa ordem; lotes sem validade vão para o fim, por código.
"""

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date, datetime
from uuid import UUID

from core.domain.entity import Entity, require_type, set_field
from core.domain.errors import ValidationError
from core.domain.ids import ItemId, LotId, new_lot_id

LOT_CODE_MAX_LENGTH = 40


@dataclass(frozen=True, slots=True, kw_only=True, eq=False)
class Lot(Entity):
    """Lote de um item. ``expires_on`` é o último dia em que o lote ainda vale (inclusive)."""

    item_id: ItemId
    code: str
    expires_on: date | None = None
    id: LotId = field(default_factory=new_lot_id)

    def __post_init__(self) -> None:
        set_field(self, "code", _clean_code(self.code))
        require_type(self.item_id, UUID, "item_id", "item")
        require_type(self.id, UUID, "id", "identificador do lote")
        if self.expires_on is not None and (
            not isinstance(self.expires_on, date) or isinstance(self.expires_on, datetime)
        ):
            raise ValidationError(
                "expires_on", f"validade precisa ser uma data (dia), não {self.expires_on!r}"
            )

    def is_expired_on(self, day: date) -> bool:
        """Vencido se a validade já passou: no próprio dia da validade ainda vale."""
        return self.expires_on is not None and self.expires_on < day


def _clean_code(value: object) -> str:
    if not isinstance(value, str):
        raise ValidationError("code", "código do lote precisa ser texto")
    code = value.strip().upper()
    if not code:
        raise ValidationError("code", "código do lote não pode ficar vazio")
    if len(code) > LOT_CODE_MAX_LENGTH or any(ch.isspace() for ch in code):
        raise ValidationError(
            "code", f"código do lote {code!r}: sem espaços, até {LOT_CODE_MAX_LENGTH} caracteres"
        )
    return code


def fefo_order(lots: Iterable[Lot]) -> list[Lot]:
    """Ordem FEFO: validade mais próxima primeiro; sem validade por último; empate pelo código."""
    return sorted(
        lots, key=lambda lot: (lot.expires_on is None, lot.expires_on or date.max, lot.code)
    )
