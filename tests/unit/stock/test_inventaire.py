from datetime import date
from uuid import UUID

import pytest

from neosys_pharma.domain.shared import DomainError
from neosys_pharma.domain.stock import Emplacement, Inventaire, TypeMouvement
from tests.unit.stock.conftest import creer_lot


def test_un_ecart_positif_cree_un_mouvement_d_ajustement(
    inventaire: Inventaire,
    rayon: Emplacement,
    conditionnement_id: UUID,
) -> None:
    lot = creer_lot(conditionnement_id, "LOT-INV", date(2027, 5, 31))
    inventaire.ajouter_lot(lot)
    inventaire.receptionner(lot_id=lot.id, emplacement_id=rayon.id, quantite=5, motif="Réception")

    mouvement = inventaire.ajuster_inventaire(
        lot_id=lot.id,
        emplacement_id=rayon.id,
        nouvelle_quantite=7,
        motif="Comptage physique du 19 septembre",
    )

    assert mouvement is not None
    assert mouvement.type is TypeMouvement.AJUSTEMENT_POSITIF
    assert mouvement.quantite == 2
    assert inventaire.stock(lot.id, rayon.id).quantite_physique == 7


def test_un_ecart_negatif_cree_un_mouvement_d_ajustement(
    inventaire: Inventaire,
    rayon: Emplacement,
    conditionnement_id: UUID,
) -> None:
    lot = creer_lot(conditionnement_id, "LOT-INV-2", date(2027, 6, 30))
    inventaire.ajouter_lot(lot)
    inventaire.receptionner(lot_id=lot.id, emplacement_id=rayon.id, quantite=5, motif="Réception")

    mouvement = inventaire.ajuster_inventaire(
        lot_id=lot.id,
        emplacement_id=rayon.id,
        nouvelle_quantite=3,
        motif="Casse constatée",
    )

    assert mouvement is not None
    assert mouvement.type is TypeMouvement.AJUSTEMENT_NEGATIF
    assert mouvement.quantite == 2


def test_un_comptage_identique_ne_cree_pas_de_mouvement(
    inventaire: Inventaire,
    rayon: Emplacement,
    conditionnement_id: UUID,
) -> None:
    lot = creer_lot(conditionnement_id, "LOT-INV-3", date(2027, 7, 31))
    inventaire.ajouter_lot(lot)
    inventaire.receptionner(lot_id=lot.id, emplacement_id=rayon.id, quantite=5, motif="Réception")

    mouvement = inventaire.ajuster_inventaire(
        lot_id=lot.id,
        emplacement_id=rayon.id,
        nouvelle_quantite=5,
        motif="Comptage conforme",
    )

    assert mouvement is None


def test_un_ajustement_ne_peut_pas_supprimer_du_stock_reserve(
    inventaire: Inventaire,
    rayon: Emplacement,
    conditionnement_id: UUID,
) -> None:
    lot = creer_lot(conditionnement_id, "LOT-INV-4", date(2027, 8, 31))
    inventaire.ajouter_lot(lot)
    inventaire.receptionner(lot_id=lot.id, emplacement_id=rayon.id, quantite=5, motif="Réception")
    inventaire.reserver_fefo(
        conditionnement_id=conditionnement_id,
        emplacement_id=rayon.id,
        quantite=3,
        au=date(2026, 9, 19),
        motif="Vente V-002",
    )

    with pytest.raises(DomainError, match="stock déjà réservé"):
        inventaire.ajuster_inventaire(
            lot_id=lot.id,
            emplacement_id=rayon.id,
            nouvelle_quantite=2,
            motif="Comptage erroné",
        )
