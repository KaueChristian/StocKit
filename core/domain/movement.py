"""Movimentações: o livro imutável do estoque (RF-005, ADR-004).

Toda mudança de estoque é uma ``Movement``. Ela nunca é alterada nem apagada (INV-02): erro se
corrige com outra movimentação, de ajuste. A quantidade é sempre positiva e o tipo diz a direção;
o saldo é a soma de ``signed_quantity`` (INV-01, M1.7).

Transferência é um **par** (saída no local de origem + entrada no destino) ligado pelo mesmo
``transfer_id`` e gravado de uma vez (INV-03): ``make_transfer`` monta o par e
``check_transfer_pair`` confere um par lido de algum lugar.

Fica para os serviços (M1.6): converter a quantidade para a unidade base do item, conferir política
de saldo negativo (INV-05) e carimbar ``recorded_at`` com o ``Clock``. ``occurred_at`` é quando
aconteceu; ``recorded_at``, quando foi lançado (auditoria de lançamento retroativo).
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum
from fractions import Fraction
from uuid import UUID

from core.domain.entity import Entity, clean_text, require_type, set_field
from core.domain.errors import ValidationError
from core.domain.ids import (
    ItemId,
    LocationId,
    LotId,
    MovementId,
    PartyId,
    TransferId,
    new_movement_id,
    new_transfer_id,
)
from core.domain.quantity import SCALE, Quantity


class Direction(Enum):
    IN = 1
    OUT = -1


class MovementKind(Enum):
    """Tipo de movimentação. O valor gravado é o primeiro item; o segundo é a direção."""

    RECEIPT = ("receipt", Direction.IN)
    ISSUE = ("issue", Direction.OUT)
    TRANSFER_OUT = ("transfer_out", Direction.OUT)
    TRANSFER_IN = ("transfer_in", Direction.IN)
    ADJUSTMENT_IN = ("adjustment_in", Direction.IN)
    ADJUSTMENT_OUT = ("adjustment_out", Direction.OUT)
    LOSS = ("loss", Direction.OUT)
    CUSTOMER_RETURN = ("customer_return", Direction.IN)
    SUPPLIER_RETURN = ("supplier_return", Direction.OUT)

    def __init__(self, code: str, direction: Direction) -> None:
        self.code = code
        self.direction = direction

    @classmethod
    def from_code(cls, code: str) -> MovementKind:
        for kind in cls:
            if kind.code == code:
                return kind
        raise ValidationError("kind", f"tipo de movimentação desconhecido: {code!r}")

    @property
    def is_transfer(self) -> bool:
        return self in (MovementKind.TRANSFER_IN, MovementKind.TRANSFER_OUT)

    @property
    def requires_reason(self) -> bool:
        """Ajuste e perda mudam o saldo sem uma contraparte: o motivo é obrigatório (auditoria)."""
        return self in (MovementKind.ADJUSTMENT_IN, MovementKind.ADJUSTMENT_OUT, MovementKind.LOSS)


REASON_MAX_LENGTH = 500


@dataclass(frozen=True, slots=True, kw_only=True, eq=False)
class Movement(Entity):
    """Uma linha do livro. Imutável: sem método de edição; o repositório não terá ``update``."""

    kind: MovementKind
    item_id: ItemId
    location_id: LocationId
    quantity: Quantity
    occurred_at: datetime
    author: str
    lot_id: LotId | None = None
    party_id: PartyId | None = None
    unit_cost: Decimal | None = None
    reason: str | None = None
    transfer_id: TransferId | None = None
    recorded_at: datetime | None = None
    id: MovementId = field(default_factory=new_movement_id)

    def __post_init__(self) -> None:
        require_type(self.kind, MovementKind, "kind", "tipo de movimentação")
        for name, label in (("item_id", "item"), ("location_id", "local"), ("id", "identificador")):
            require_type(getattr(self, name), UUID, name, label)
        for name, label in (
            ("lot_id", "lote"),
            ("party_id", "parte"),
            ("transfer_id", "transferência"),
        ):
            if getattr(self, name) is not None:
                require_type(getattr(self, name), UUID, name, label)

        require_type(self.quantity, Quantity, "quantity", "quantidade")
        if self.quantity.value <= 0:
            raise ValidationError(
                "quantity",
                f"a quantidade de uma movimentação precisa ser positiva: {self.quantity} "
                "(o tipo é que diz se entra ou sai)",
            )
        set_field(self, "occurred_at", _utc(self.occurred_at, "occurred_at"))
        if self.recorded_at is not None:
            set_field(self, "recorded_at", _utc(self.recorded_at, "recorded_at"))
            if self.recorded_at < self.occurred_at:
                raise ValidationError(
                    "occurred_at", "a movimentação não pode ter ocorrido depois de ser registrada"
                )
        set_field(self, "author", clean_text(self.author, "author", "autor", max_length=120))
        set_field(self, "unit_cost", _clean_cost(self.unit_cost))
        set_field(self, "reason", _clean_reason(self.reason, self.kind))

        if self.kind.is_transfer and self.transfer_id is None:
            raise ValidationError("transfer_id", "movimentação de transferência precisa do par")
        if not self.kind.is_transfer and self.transfer_id is not None:
            raise ValidationError(
                "transfer_id", f"só transferência tem par; este movimento é {self.kind.code}"
            )

    @property
    def direction(self) -> Direction:
        return self.kind.direction

    @property
    def signed_quantity(self) -> Quantity:
        """Quantidade com sinal: positiva se entra, negativa se sai. Saldo = soma disto (INV-01)."""
        return self.quantity if self.direction is Direction.IN else -self.quantity


def _utc(value: object, field: str) -> datetime:
    if not isinstance(value, datetime):
        raise ValidationError(field, f"data da movimentação inválida: {value!r}")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValidationError(
            field, "data da movimentação precisa de fuso horário (gravada em UTC)"
        )
    return value.astimezone(UTC)


def _clean_cost(value: object) -> Decimal | None:
    if value is None:
        return None
    if not isinstance(value, Decimal) or not value.is_finite():
        raise ValidationError("unit_cost", f"custo unitário precisa ser Decimal finito: {value!r}")
    if value < 0:
        raise ValidationError("unit_cost", f"custo unitário não pode ser negativo: {value}")
    if (Fraction(value) * 10**SCALE).denominator != 1:
        raise ValidationError("unit_cost", f"custo unitário com mais de {SCALE} casas: {value}")
    return value


def _clean_reason(value: object, kind: MovementKind) -> str | None:
    if value is None or (isinstance(value, str) and not value.strip()):
        if kind.requires_reason:
            raise ValidationError("reason", f"{kind.code} precisa de um motivo")
        return None
    return clean_text(value, "reason", "motivo", max_length=REASON_MAX_LENGTH)


def make_transfer(
    *,
    item_id: ItemId,
    from_location: LocationId,
    to_location: LocationId,
    quantity: Quantity,
    occurred_at: datetime,
    author: str,
    lot_id: LotId | None = None,
    reason: str | None = None,
) -> tuple[Movement, Movement]:
    """Monta o par (saída na origem, entrada no destino). Gravar os dois juntos: serviço (M1.8)."""
    if from_location == to_location:
        raise ValidationError("to_location", "transferência precisa de locais diferentes")
    transfer_id = new_transfer_id()

    def side(kind: MovementKind, location_id: LocationId) -> Movement:
        return Movement(
            kind=kind,
            item_id=item_id,
            location_id=location_id,
            quantity=quantity,
            occurred_at=occurred_at,
            author=author,
            lot_id=lot_id,
            reason=reason,
            transfer_id=transfer_id,
        )

    return side(MovementKind.TRANSFER_OUT, from_location), side(
        MovementKind.TRANSFER_IN, to_location
    )


def check_transfer_pair(first: Movement, second: Movement) -> None:
    """Confere que duas movimentações formam um par de transferência válido (INV-03)."""
    kinds = {first.kind, second.kind}
    if kinds != {MovementKind.TRANSFER_OUT, MovementKind.TRANSFER_IN}:
        raise ValidationError("kind", "um par de transferência tem uma saída e uma entrada")
    differences = [
        name
        for name in ("transfer_id", "item_id", "quantity", "lot_id", "occurred_at")
        if getattr(first, name) != getattr(second, name)
    ]
    if differences:
        raise ValidationError(
            differences[0], f"par de transferência diverge em: {', '.join(differences)}"
        )
    if first.location_id == second.location_id:
        raise ValidationError("location_id", "par de transferência com origem igual ao destino")
