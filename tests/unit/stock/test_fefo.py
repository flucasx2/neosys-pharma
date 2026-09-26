from datetime import date
from uuid import UUID, uuid4

import pytest

from neosys_pharma.domain.shared import DomainError
from neosys_pharma.domain.stock import (
    Emplacement,
    EtatLot,
    Inventaire,
    Lot,
    StockInsuffisant,
    TypeMouvement,
)
from tests.unit.stock.conftest import creer_lot


def test_fefo_prend_d_abord_le_lot_qui_expire_le_plus_tot(
    inventaire: Inventaire,
    rayon: Emplacement,
    conditionnement_id: UUID,
) -> None:
    lot_proche = creer_lot(conditionnement_id, "LOT-PROCHE", date(2026, 12, 31))
    lot_lointain = creer_lot(conditionnement_id, "LOT-LOIN", date(2027, 6, 30))
    inventaire.ajouter_lot(lot_proche)
    inventaire.ajouter_lot(lot_lointain)
    inventaire.receptionner(
        lot_id=lot_lointain.id, emplacement_id=rayon.id, quantite=10, motif="Réception"
    )
    inventaire.receptionner(
        lot_id=lot_proche.id, emplacement_id=rayon.id, quantite=4, motif="Réception"
    )

    allocations = inventaire.reserver_fefo(
        conditionnement_id=conditionnement_id,
        emplacement_id=rayon.id,
        quantite=7,
        au=date(2026, 9, 19),
        motif="Préparation de vente V-001",
    )

    assert [(item.lot_id, item.quantite) for item in allocations] == [
        (lot_proche.id, 4),
        (lot_lointain.id, 3),
    ]
    assert inventaire.stock(lot_proche.id, rayon.id).quantite_disponible == 0
    assert inventaire.stock(lot_lointain.id, rayon.id).quantite_disponible == 7
    reservations = [
        mouvement
        for mouvement in inventaire.mouvements
        if mouvement.type is TypeMouvement.RESERVATION
    ]
    assert len(reservations) == 2


def test_fefo_ignore_les_lots_expires_et_bloques(
    inventaire: Inventaire,
    rayon: Emplacement,
    conditionnement_id: UUID,
) -> None:
    expire = creer_lot(conditionnement_id, "EXP", date(2026, 8, 31))
    bloque = creer_lot(conditionnement_id, "BLQ", date(2027, 1, 31))
    inventaire.ajouter_lot(expire)
    inventaire.ajouter_lot(bloque)
    inventaire.changer_etat_lot(bloque.id, EtatLot.BLOQUE)
    for lot in (expire, bloque):
        inventaire.receptionner(
            lot_id=lot.id, emplacement_id=rayon.id, quantite=10, motif="Réception"
        )

    with pytest.raises(StockInsuffisant):
        inventaire.proposer_fefo(
            conditionnement_id=conditionnement_id,
            emplacement_id=rayon.id,
            quantite=1,
            au=date(2026, 9, 19),
        )


def test_fefo_ne_complete_pas_avec_le_stock_d_un_autre_emplacement(
    inventaire: Inventaire,
    rayon: Emplacement,
    reserve: Emplacement,
    conditionnement_id: UUID,
) -> None:
    lot = creer_lot(conditionnement_id, "LOT-EMPL", date(2027, 3, 31))
    inventaire.ajouter_lot(lot)
    inventaire.receptionner(
        lot_id=lot.id, emplacement_id=rayon.id, quantite=2, motif="Réception rayon"
    )
    inventaire.receptionner(
        lot_id=lot.id, emplacement_id=reserve.id, quantite=20, motif="Réception réserve"
    )

    with pytest.raises(StockInsuffisant):
        inventaire.proposer_fefo(
            conditionnement_id=conditionnement_id,
            emplacement_id=rayon.id,
            quantite=3,
            au=date(2026, 9, 19),
        )


def test_fefo_peut_servir_un_stock_de_reserve(
    inventaire: Inventaire,
    reserve: Emplacement,
    conditionnement_id: UUID,
) -> None:
    lot = Lot(
        conditionnement_id=conditionnement_id,
        numero="LOT-RESERVE",
        date_expiration=date(2027, 12, 31),
    )
    inventaire.ajouter_lot(lot)
    inventaire.receptionner(
        lot_id=lot.id, emplacement_id=reserve.id, quantite=3, motif="Réception réserve"
    )

    allocations = inventaire.proposer_fefo(
        conditionnement_id=conditionnement_id,
        emplacement_id=reserve.id,
        quantite=1,
        au=date(2026, 9, 19),
    )

    assert allocations[0].lot_id == lot.id


def test_fefo_refuse_un_emplacement_inconnu(
    inventaire: Inventaire,
    conditionnement_id: UUID,
) -> None:
    with pytest.raises(DomainError, match="inconnu"):
        inventaire.proposer_fefo(
            conditionnement_id=conditionnement_id,
            emplacement_id=uuid4(),
            quantite=1,
            au=date(2026, 9, 19),
        )


def test_changer_l_etat_d_un_lot_inconnu_est_refuse(inventaire: Inventaire) -> None:
    with pytest.raises(DomainError, match="lot est inconnu"):
        inventaire.changer_etat_lot(uuid4(), EtatLot.BLOQUE)
