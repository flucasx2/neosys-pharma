from datetime import date
from uuid import UUID

import pytest

from neosys_pharma.domain.shared import DomainError
from neosys_pharma.domain.stock import (
    Emplacement,
    EtatLot,
    Inventaire,
    TypeMouvement,
)
from tests.unit.stock.conftest import creer_lot


def _reserver(
    inventaire: Inventaire,
    rayon: Emplacement,
    conditionnement_id: UUID,
    quantite_stock: int = 5,
):
    lot = creer_lot(conditionnement_id, "LOT-RES", date(2027, 4, 30))
    inventaire.ajouter_lot(lot)
    inventaire.receptionner(
        lot_id=lot.id,
        emplacement_id=rayon.id,
        quantite=quantite_stock,
        motif="Réception",
    )
    allocations = inventaire.reserver_fefo(
        conditionnement_id=conditionnement_id,
        emplacement_id=rayon.id,
        quantite=quantite_stock,
        au=date(2026, 9, 19),
        motif="Vente V-001",
    )
    return lot, allocations


def test_liberer_une_reservation_rend_le_stock_disponible(
    inventaire: Inventaire,
    rayon: Emplacement,
    conditionnement_id: UUID,
) -> None:
    lot, allocations = _reserver(inventaire, rayon, conditionnement_id)

    mouvements = inventaire.liberer_reservations(
        allocations=allocations,
        emplacement_id=rayon.id,
        motif="Annulation de la vente V-001",
    )

    position = inventaire.stock(lot.id, rayon.id)
    assert position.quantite_physique == 5
    assert position.quantite_reservee == 0
    assert position.quantite_disponible == 5
    assert mouvements[0].type is TypeMouvement.LIBERATION


def test_confirmer_la_sortie_deduit_le_physique_et_la_reservation(
    inventaire: Inventaire,
    rayon: Emplacement,
    conditionnement_id: UUID,
) -> None:
    lot, allocations = _reserver(inventaire, rayon, conditionnement_id)

    mouvements = inventaire.confirmer_sortie(
        allocations=allocations,
        emplacement_id=rayon.id,
        motif="Encaissement de la vente V-001",
    )

    position = inventaire.stock(lot.id, rayon.id)
    assert position.quantite_physique == 0
    assert position.quantite_reservee == 0
    assert lot.etat is EtatLot.EPUISE
    assert mouvements[0].type is TypeMouvement.SORTIE_VENTE


def test_une_sortie_non_reservee_est_refusee_sans_modifier_le_stock(
    inventaire: Inventaire,
    rayon: Emplacement,
    conditionnement_id: UUID,
) -> None:
    lot, allocations = _reserver(inventaire, rayon, conditionnement_id, 2)
    inventaire.liberer_reservations(
        allocations=allocations,
        emplacement_id=rayon.id,
        motif="Annulation",
    )

    with pytest.raises(DomainError, match="dépasse"):
        inventaire.confirmer_sortie(
            allocations=allocations,
            emplacement_id=rayon.id,
            motif="Sortie invalide",
        )

    assert inventaire.stock(lot.id, rayon.id).quantite_physique == 2
