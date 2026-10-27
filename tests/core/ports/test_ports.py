"""Forma das portas (M1.4). O comportamento de cada método é cobrado dos adaptadores pela suíte de
contrato (M2.6); aqui só se garante o que as portas expõem — e o que **não** expõem.
"""

import subprocess
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from types import TracebackType
from typing import Self, get_protocol_members

import pytest

from core.domain.catalog import Category, Item
from core.domain.ids import (
    CategoryId,
    ItemId,
    LocationId,
    LotId,
    MovementId,
    PartyId,
    TransferId,
)
from core.domain.location import Location
from core.domain.lot import Lot
from core.domain.movement import Movement
from core.domain.party import Party
from core.ports.clock import Clock
from core.ports.repositories import (
    CategoryRepository,
    ItemRepository,
    LocationRepository,
    LotRepository,
    MovementRepository,
    PartyRepository,
)
from core.ports.unit_of_work import UnitOfWork

ROOT = Path(__file__).resolve().parents[3]
CRUD = {"get", "add", "update", "list"}
FORBIDDEN = {"delete", "remove", "clear", "update_movement", "set", "edit"}


@pytest.mark.req("RF-005")
def test_ledger_only_appends() -> None:
    """INV-02 por construção: o livro não tem como alterar nem apagar movimentações."""
    assert get_protocol_members(MovementRepository) == {"append", "get", "list", "transfer_pair"}


@pytest.mark.parametrize(
    ("port", "extra"),
    [
        (ItemRepository, {"find_by_sku"}),
        (CategoryRepository, set()),
        (LocationRepository, set()),
        (PartyRepository, set()),
        (LotRepository, {"find_by_code", "list_for_item"}),
    ],
    ids=["item", "categoria", "local", "parte", "lote"],
)
def test_registry_ports_have_crud_without_delete(port: type, extra: set[str]) -> None:
    """Cadastro se inativa, não se apaga: o histórico de movimentações aponta para ele."""
    members = get_protocol_members(port)
    assert members == CRUD | extra
    assert not members & FORBIDDEN


def test_unit_of_work_exposes_every_repository_and_the_transaction() -> None:
    assert get_protocol_members(UnitOfWork) == {
        "items",
        "categories",
        "locations",
        "parties",
        "lots",
        "movements",
        "__enter__",
        "__exit__",
        "commit",
        "rollback",
    }


def test_clock_has_only_now() -> None:
    assert get_protocol_members(Clock) == {"now"}


# --- uma implementação mínima satisfaz as portas (conferido pelo mypy no check) ----------


class _Registry[E, K]:
    def get(self, entity_id: K) -> E:
        raise NotImplementedError

    def add(self, entity: E) -> None: ...

    def update(self, entity: E) -> None: ...

    def list(self) -> Sequence[E]:
        return ()


class _Items(_Registry[Item, ItemId]):
    def find_by_sku(self, sku: str) -> Item | None:
        return None


class _Lots(_Registry[Lot, LotId]):
    def find_by_code(self, item_id: ItemId, code: str) -> Lot | None:
        return None

    def list_for_item(self, item_id: ItemId) -> Sequence[Lot]:
        return ()


class _Movements:
    def append(self, movement: Movement) -> None: ...

    def get(self, movement_id: MovementId) -> Movement:
        raise NotImplementedError

    def list(
        self,
        *,
        item_id: ItemId | None = None,
        location_id: LocationId | None = None,
        lot_id: object = None,
        until: datetime | None = None,
    ) -> Sequence[Movement]:
        return ()

    def transfer_pair(self, transfer_id: TransferId) -> tuple[Movement, Movement]:
        raise NotImplementedError


class _Uow:
    items = _Items()
    categories = _Registry[Category, CategoryId]()
    locations = _Registry[Location, LocationId]()
    parties = _Registry[Party, PartyId]()
    lots = _Lots()
    movements = _Movements()
    committed = False

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None: ...


class _FixedClock:
    def now(self) -> datetime:
        return datetime(2026, 10, 27, tzinfo=UTC)


def _service_like(uow: UnitOfWork, clock: Clock) -> datetime:
    """Como um serviço usará as portas: só pelos tipos dos Protocols."""
    with uow:
        assert uow.items.find_by_sku("PAR-001") is None
        assert uow.movements.list(until=clock.now()) == ()
        uow.commit()
    return clock.now()


def test_minimal_implementations_satisfy_the_ports() -> None:
    uow = _Uow()
    assert _service_like(uow, _FixedClock()).tzinfo is UTC
    assert uow.committed


MYPY_HEADER = (
    "from core.ports.unit_of_work import UnitOfWork\n"
    "from tests.core.ports.test_ports import _Uow\n\n"
)
MYPY_CASES = {
    "completa": ("uow: UnitOfWork = _Uow()\n", 0),
    "commit-com-parametro": (
        "class CommitErrado(_Uow):\n"
        "    def commit(self, force: bool) -> None: ...  # type: ignore[override]\n\n"
        "uow: UnitOfWork = CommitErrado()\n",
        1,
    ),
    "vazia": ("class Vazia: ...\n\nuow: UnitOfWork = Vazia()\n", 1),
}


@pytest.mark.parametrize("case", MYPY_CASES)
def test_mypy_enforces_the_unit_of_work_port(case: str, tmp_path: Path) -> None:
    """Prova de que as portas são cobradas: o mesmo mypy do check recusa uma UoW incompatível."""
    body, expected = MYPY_CASES[case]
    snippet = tmp_path / f"uow_{case.replace('-', '_')}.py"
    snippet.write_text(MYPY_HEADER + body, encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "mypy", "--no-error-summary", str(snippet)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == expected, result.stdout + result.stderr
    if expected:
        assert '"UnitOfWork"' in result.stdout
