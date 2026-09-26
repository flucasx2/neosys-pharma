from datetime import date
from uuid import UUID

import pytest

from neosys_pharma.domain.stock import Emplacement, Inventaire, Lot


@pytest.fixture
def conditionnement_id() -> UUID:
    return UUID("00000000-0000-0000-0000-000000000101")


@pytest.fixture
def rayon() -> Emplacement:
    return Emplacement(code="RAY-A", libelle="Rayon A")


@pytest.fixture
def reserve() -> Emplacement:
    return Emplacement(code="RES-1", libelle="Réserve", autorise_vente=False)


@pytest.fixture
def inventaire(rayon: Emplacement, reserve: Emplacement) -> Inventaire:
    stock = Inventaire()
    stock.ajouter_emplacement(rayon)
    stock.ajouter_emplacement(reserve)
    return stock


def creer_lot(conditionnement_id: UUID, numero: str, expiration: date) -> Lot:
    return Lot(
        conditionnement_id=conditionnement_id,
        numero=numero,
        date_expiration=expiration,
    )
