from datetime import date
from uuid import UUID

import pytest

from neosys_pharma.domain.shared import DomainError
from neosys_pharma.domain.stock import (
    Emplacement,
    Inventaire,
    Lot,
    MouvementStock,
    StockEmplacement,
    StockInsuffisant,
    TypeMouvement,
)
from tests.unit.stock.conftest import creer_lot


def test_receptionner_un_lot_augmente_le_stock_et_trace_le_mouvement(
    inventaire: Inventaire,
    rayon: Emplacement,
    conditionnement_id: UUID,
) -> None:
    lot = creer_lot(conditionnement_id, "LOT-001", date(2027, 5, 31))
    inventaire.ajouter_lot(lot)

    mouvement = inventaire.receptionner(
        lot_id=lot.id,
        emplacement_id=rayon.id,
        quantite=30,
        motif="Bon de livraison BL-001",
    )

    assert inventaire.stock(lot.id, rayon.id).quantite_physique == 30
    assert mouvement.type is TypeMouvement.RECEPTION
    assert mouvement.quantite == 30
    assert inventaire.mouvements == (mouvement,)


def test_transfert_deplace_uniquement_le_stock_disponible_et_cree_deux_traces(
    inventaire: Inventaire,
    rayon: Emplacement,
    reserve: Emplacement,
    conditionnement_id: UUID,
) -> None:
    lot = creer_lot(conditionnement_id, "LOT-002", date(2027, 6, 30))
    inventaire.ajouter_lot(lot)
    inventaire.receptionner(
        lot_id=lot.id, emplacement_id=reserve.id, quantite=20, motif="Réception"
    )

    sortie, entree = inventaire.transferer(
        lot_id=lot.id,
        source_id=reserve.id,
        destination_id=rayon.id,
        quantite=8,
        motif="Réassort du rayon",
    )

    assert inventaire.stock(lot.id, reserve.id).quantite_physique == 12
    assert inventaire.stock(lot.id, rayon.id).quantite_physique == 8
    assert sortie.type is TypeMouvement.TRANSFERT_SORTANT
    assert entree.type is TypeMouvement.TRANSFERT_ENTRANT


def test_un_transfert_est_refuse_si_le_stock_source_est_insuffisant(
    inventaire: Inventaire,
    rayon: Emplacement,
    reserve: Emplacement,
    conditionnement_id: UUID,
) -> None:
    lot = creer_lot(conditionnement_id, "LOT-003", date(2027, 7, 31))
    inventaire.ajouter_lot(lot)
    inventaire.receptionner(lot_id=lot.id, emplacement_id=reserve.id, quantite=5, motif="Réception")

    with pytest.raises(StockInsuffisant):
        inventaire.transferer(
            lot_id=lot.id,
            source_id=reserve.id,
            destination_id=rayon.id,
            quantite=6,
            motif="Réassort",
        )


def test_un_mouvement_refuse_une_quantite_nulle(
    inventaire: Inventaire,
    rayon: Emplacement,
    conditionnement_id: UUID,
) -> None:
    lot = creer_lot(conditionnement_id, "LOT-004", date(2027, 8, 31))
    inventaire.ajouter_lot(lot)

    with pytest.raises(DomainError, match="strictement positive"):
        inventaire.receptionner(lot_id=lot.id, emplacement_id=rayon.id, quantite=0, motif="Erreur")


def test_les_entites_de_stock_refusent_les_donnees_invalides(
    conditionnement_id: UUID,
    rayon: Emplacement,
) -> None:
    with pytest.raises(DomainError, match="obligatoires"):
        Emplacement(code=" ", libelle="Rayon")
    with pytest.raises(DomainError, match="numéro de lot"):
        Lot(conditionnement_id=conditionnement_id, numero=" ", date_expiration=date(2027, 1, 1))
    with pytest.raises(DomainError, match="négatives"):
        StockEmplacement(lot_id=conditionnement_id, emplacement_id=rayon.id, quantite_physique=-1)
    with pytest.raises(DomainError, match="dépasse"):
        StockEmplacement(
            lot_id=conditionnement_id,
            emplacement_id=rayon.id,
            quantite_physique=1,
            quantite_reservee=2,
        )
    with pytest.raises(DomainError, match="motif"):
        MouvementStock(
            type=TypeMouvement.RECEPTION,
            lot_id=conditionnement_id,
            quantite=1,
            motif=" ",
        )


def test_un_numero_de_lot_est_unique_par_conditionnement(
    inventaire: Inventaire,
    conditionnement_id: UUID,
) -> None:
    inventaire.ajouter_lot(creer_lot(conditionnement_id, "LOT-UNIQUE", date(2027, 1, 31)))

    with pytest.raises(DomainError, match="existe déjà"):
        inventaire.ajouter_lot(creer_lot(conditionnement_id, "LOT-UNIQUE", date(2028, 1, 31)))


def test_un_transfert_vers_le_meme_emplacement_est_refuse(
    inventaire: Inventaire,
    rayon: Emplacement,
    conditionnement_id: UUID,
) -> None:
    lot = creer_lot(conditionnement_id, "LOT-MEME", date(2027, 2, 28))
    inventaire.ajouter_lot(lot)
    inventaire.receptionner(lot_id=lot.id, emplacement_id=rayon.id, quantite=2, motif="Réception")

    with pytest.raises(DomainError, match="différentes"):
        inventaire.transferer(
            lot_id=lot.id,
            source_id=rayon.id,
            destination_id=rayon.id,
            quantite=1,
            motif="Transfert invalide",
        )
