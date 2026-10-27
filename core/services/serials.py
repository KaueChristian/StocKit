"""Consultas de números de série (M1.10, RF-009).

Estado de uma série: em estoque num local, ou fora do estoque (``None``). Derivado do livro, como
o saldo; aceita ``at`` para o estado em uma data (por ``occurred_at``, inclusive).
"""

from datetime import datetime

from core.domain.ids import ItemId, LocationId
from core.domain.location import LocationTree
from core.domain.movement import normalize_serial
from core.domain.serials import serial_positions
from core.ports.unit_of_work import UnitOfWork


def serial_location(
    uow: UnitOfWork, item_id: ItemId, serial: str, *, at: datetime | None = None
) -> LocationId | None:
    """Onde a série está (ou ``None`` se está fora ou nunca entrou)."""
    wanted = normalize_serial(serial)
    with uow:
        uow.items.get(item_id)
        movements = [
            m for m in uow.movements.list(item_id=item_id, until=at) if wanted in m.serials
        ]
        return serial_positions(movements).get(wanted)


def serials_in_stock(
    uow: UnitOfWork,
    item_id: ItemId,
    *,
    location_id: LocationId | None = None,
    at: datetime | None = None,
    include_sublocations: bool = True,
) -> frozenset[str]:
    """Séries em estoque: em qualquer lugar, ou num local (com sublocais, por padrão)."""
    with uow:
        uow.items.get(item_id)
        positions = serial_positions(uow.movements.list(item_id=item_id, until=at))
        if location_id is None:
            return frozenset(s for s, where in positions.items() if where is not None)
        uow.locations.get(location_id)
        scope = {location_id}
        if include_sublocations:
            tree = LocationTree(uow.locations.list())
            scope |= {loc.id for loc in tree.descendants(location_id)}
        return frozenset(s for s, where in positions.items() if where in scope)
