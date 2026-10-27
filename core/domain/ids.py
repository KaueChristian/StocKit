"""Identificadores tipados das entidades.

São UUIDs para que desktop e web gerem IDs sem coordenação e o mesmo dado sirva às duas
plataformas. O tipo próprio de cada entidade impede, no mypy, passar o ID de um local onde se espera
o de um item.
"""

from typing import NewType
from uuid import UUID, uuid4

ItemId = NewType("ItemId", UUID)
CategoryId = NewType("CategoryId", UUID)
LocationId = NewType("LocationId", UUID)
PartyId = NewType("PartyId", UUID)


def new_item_id() -> ItemId:
    return ItemId(uuid4())


def new_category_id() -> CategoryId:
    return CategoryId(uuid4())


def new_location_id() -> LocationId:
    return LocationId(uuid4())


def new_party_id() -> PartyId:
    return PartyId(uuid4())
