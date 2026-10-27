"""Serviço de registro de movimentação (M1.6, RF-005, RF-007, INV-05, caso TP-M1-04)."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from hypothesis import given
from hypothesis import strategies as st

from adapters.clock import FixedClock
from adapters.memory.repositories import MemoryState
from adapters.memory.unit_of_work import MemoryUnitOfWork
from core.domain.catalog import Item, ItemKind
from core.domain.errors import (
    InactiveRecordError,
    IncompatibleUnitsError,
    InsufficientStockError,
    NotFoundError,
    ValidationError,
)
from core.domain.ids import ItemId, LocationId, LotId, PartyId
from core.domain.ledger import in_ledger_order
from core.domain.location import Location
from core.domain.movement import MovementKind
from core.domain.party import Party, PartyRole
from core.domain.policy import NegativeStockPolicy
from core.domain.quantity import STANDARD_UNITS, Dimension, Quantity, UnitOfMeasure
from core.services.movements import RecordMovement, record_movement

UN, DZ, KG, G = (STANDARD_UNITS[s] for s in ("un", "dz", "kg", "g"))
CX12 = UnitOfMeasure("cx12", "caixa com 12", Dimension.COUNT, Decimal(12))
NOW = datetime(2026, 10, 27, 15, tzinfo=UTC)
IN, OUT = MovementKind.RECEIPT, MovementKind.ISSUE


class World:
    """Estoque em memória com um item (un), um item a granel (kg), uma loja e um fornecedor."""

    def __init__(self) -> None:
        self.state = MemoryState()
        self.clock = FixedClock(NOW)
        self.item = Item(sku="PAR-001", name="Parafuso", kind=ItemKind.RESALE, base_unit=UN)
        self.bulk = Item(sku="ARROZ", name="Arroz", kind=ItemKind.CONSUMABLE, base_unit=KG)
        self.shop = Location(name="Loja")
        self.supplier = Party(name="Fornecedor", roles=frozenset({PartyRole.SUPPLIER}))
        with self.uow() as uow:
            uow.items.add(self.item)
            uow.items.add(self.bulk)
            uow.locations.add(self.shop)
            uow.parties.add(self.supplier)
            uow.commit()

    def uow(self) -> MemoryUnitOfWork:
        return MemoryUnitOfWork(self.state)

    def record(
        self,
        kind: MovementKind,
        value: str,
        *,
        unit: UnitOfMeasure = UN,
        policy: NegativeStockPolicy = NegativeStockPolicy.FORBID,
        **changes: object,
    ) -> object:
        data: dict[str, object] = {
            "kind": kind,
            "item_id": self.item.id,
            "location_id": self.shop.id,
            "quantity": Quantity(Decimal(value), unit),
            "author": "Ana",
            "reason": "conferência" if kind.requires_reason else None,
        }
        data |= changes
        return record_movement(self.uow(), self.clock, RecordMovement(**data), policy=policy)  # type: ignore[arg-type]


@pytest.fixture
def world() -> World:
    return World()


# --- caminho feliz -----------------------------------------------------------------------


@pytest.mark.req("RF-005")
def test_receipt_is_recorded_with_both_timestamps(world: World) -> None:
    recorded = world.record(IN, "10", party_id=world.supplier.id, unit_cost=Decimal("0.35"))
    assert recorded == tuple(world.state.movements)
    assert len(world.state.movements) == 1
    stored = world.state.movements[0]
    assert stored.occurred_at == stored.recorded_at == NOW
    assert stored.party_id == world.supplier.id
    assert stored.unit_cost == Decimal("0.35")


@pytest.mark.req("RF-005")
def test_backdated_movement_keeps_both_dates(world: World) -> None:
    yesterday = NOW - timedelta(days=1)
    world.record(IN, "1", occurred_at=yesterday)
    stored = world.state.movements[0]
    assert (stored.occurred_at, stored.recorded_at) == (yesterday, NOW)


@pytest.mark.req("RF-005")
def test_future_movement_is_refused(world: World) -> None:
    with pytest.raises(ValidationError, match="depois de ser registrada"):
        world.record(IN, "1", occurred_at=NOW + timedelta(minutes=1))
    assert world.state.movements == []


@pytest.mark.req("RF-010")
@pytest.mark.parametrize(
    ("value", "unit", "item_attr", "expected"),
    [("2", DZ, "item", "24"), ("250", G, "bulk", "0.25"), ("1.5", KG, "bulk", "1.5")],
)
def test_quantity_is_stored_in_the_item_base_unit(
    world: World, value: str, unit: UnitOfMeasure, item_attr: str, expected: str
) -> None:
    item: Item = getattr(world, item_attr)
    world.record(IN, value, unit=unit, item_id=item.id)
    stored = world.state.movements[0].quantity
    assert stored == Quantity(Decimal(expected), item.base_unit)


@pytest.mark.req("RF-010")
def test_lossy_conversion_is_refused(world: World) -> None:
    boxed = Item(sku="CX-1", name="Em caixa", kind=ItemKind.RESALE, base_unit=CX12)
    with world.uow() as uow:
        uow.items.add(boxed)
        uow.commit()
    with pytest.raises(IncompatibleUnitsError, match="número exato"):
        world.record(IN, "1", unit=UN, item_id=boxed.id)
    world.record(IN, "24", unit=UN, item_id=boxed.id)
    assert world.state.movements[0].quantity == Quantity(Decimal(2), CX12)


@pytest.mark.req("RF-010")
def test_quantity_of_another_dimension_is_refused(world: World) -> None:
    with pytest.raises(IncompatibleUnitsError):
        world.record(IN, "1", unit=KG)


# --- política de saldo negativo (INV-05, TP-M1-04) ---------------------------------------


@pytest.mark.req("RF-007")
def test_forbid_policy_refuses_output_above_balance(world: World) -> None:
    world.record(IN, "5")
    with pytest.raises(InsufficientStockError, match=r"PAR-001.*'Loja'.*-2 un"):
        world.record(OUT, "7")
    assert len(world.state.movements) == 1, "nada gravado"
    world.record(OUT, "5")


@pytest.mark.req("RF-007")
def test_forbid_is_the_default_policy(world: World) -> None:
    with pytest.raises(InsufficientStockError):
        record_movement(
            world.uow(),
            world.clock,
            RecordMovement(
                kind=OUT,
                item_id=world.item.id,
                location_id=world.shop.id,
                quantity=Quantity(Decimal(1), UN),
                author="Ana",
            ),
        )


@pytest.mark.req("RF-007")
def test_allow_policy_lets_balance_go_negative(world: World) -> None:
    world.record(OUT, "3", policy=NegativeStockPolicy.ALLOW)
    assert world.state.movements[0].signed_quantity == Quantity(Decimal(-3), UN)


@pytest.mark.req("RF-007")
def test_backdated_output_that_breaks_a_later_balance_is_refused(world: World) -> None:
    world.record(IN, "10", occurred_at=NOW - timedelta(days=5))
    world.record(OUT, "8", occurred_at=NOW - timedelta(days=1))
    with pytest.raises(InsufficientStockError, match="-3 un"):
        world.record(OUT, "5", occurred_at=NOW - timedelta(days=3))


@pytest.mark.req("RF-007")
@pytest.mark.parametrize(
    "kind", [k for k in MovementKind if k.direction.value < 0 and not k.is_transfer]
)
def test_every_outgoing_kind_respects_the_policy(world: World, kind: MovementKind) -> None:
    with pytest.raises(InsufficientStockError):
        world.record(kind, "1")


@pytest.mark.req("RF-007")
def test_balance_is_checked_per_location(world: World) -> None:
    backroom = Location(name="Depósito")
    with world.uow() as uow:
        uow.locations.add(backroom)
        uow.commit()
    world.record(IN, "5", location_id=backroom.id)
    with pytest.raises(InsufficientStockError):
        world.record(OUT, "1")


@pytest.mark.req("RF-007")
@given(
    operations=st.lists(
        st.tuples(
            st.sampled_from([IN, OUT, MovementKind.LOSS, MovementKind.ADJUSTMENT_IN]),
            st.integers(min_value=1, max_value=20),
            st.integers(min_value=0, max_value=30),
        ),
        max_size=25,
    )
)
def test_forbid_never_lets_any_point_of_the_ledger_go_negative(
    operations: list[tuple[MovementKind, int, int]],
) -> None:
    """INV-05: aceite ou recuse o que for, o livro gravado nunca passa por saldo negativo."""
    world = World()
    accepted = 0
    for kind, amount, days_ago in operations:
        try:
            world.record(kind, str(amount), occurred_at=NOW - timedelta(days=days_ago))
            accepted += 1
        except InsufficientStockError:
            pass
    running = Decimal(0)
    for movement in in_ledger_order(world.state.movements):
        running += movement.signed_quantity.value
        assert running >= 0
    assert len(world.state.movements) == accepted


# --- cadastros e regras de entrada -------------------------------------------------------


@pytest.mark.parametrize("target", ["item", "location", "party"])
def test_unknown_records_are_refused(world: World, target: str) -> None:
    options: dict[str, dict[str, object]] = {
        "item": {"item_id": ItemId(uuid4())},
        "location": {"location_id": LocationId(uuid4())},
        "party": {"party_id": PartyId(uuid4())},
    }
    changes = options[target]
    with pytest.raises(NotFoundError):
        world.record(IN, "1", **changes)  # type: ignore[arg-type]
    assert world.state.movements == []


@pytest.mark.parametrize("target", ["item", "shop", "supplier"])
def test_inactive_records_are_refused(world: World, target: str) -> None:
    with world.uow() as uow:
        if target == "item":
            uow.items.update(world.item.deactivated())
        elif target == "shop":
            uow.locations.update(world.shop.deactivated())
        else:
            uow.parties.update(world.supplier.deactivated())
        uow.commit()
    with pytest.raises(InactiveRecordError, match="inativ"):
        world.record(IN, "1", party_id=world.supplier.id)
    assert world.state.movements == []


@pytest.mark.parametrize("kind", [MovementKind.TRANSFER_IN, MovementKind.TRANSFER_OUT])
def test_transfers_have_their_own_service(world: World, kind: MovementKind) -> None:
    with pytest.raises(ValidationError, match="serviço próprio"):
        world.record(kind, "1")


def test_lot_rules(world: World) -> None:
    with pytest.raises(ValidationError, match="não controla lote"):
        world.record(IN, "1", lot_id=LotId(uuid4()))
    lotted = replace(world.item, sku="LOTE-1", tracks_lots=True, id=ItemId(uuid4()))
    with world.uow() as uow:
        uow.items.add(lotted)
        uow.commit()
    with pytest.raises(ValidationError, match="informe o lote"):
        world.record(IN, "1", item_id=lotted.id)
    with pytest.raises(NotFoundError, match="lote"):
        world.record(IN, "1", item_id=lotted.id, lot_id=LotId(uuid4()))
    assert world.state.movements == []


def test_movement_rules_still_apply(world: World) -> None:
    with pytest.raises(ValidationError, match="motivo"):
        world.record(MovementKind.ADJUSTMENT_IN, "1", reason=None)
    with pytest.raises(ValidationError, match="autor"):
        world.record(IN, "1", author=" ")
    assert world.state.movements == []
