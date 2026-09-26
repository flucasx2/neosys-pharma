from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from neosys_pharma.domain.catalogue import (
    CommandeAchat,
    LigneCommandeAchat,
    Medicament,
    ProduitCosmetique,
)
from neosys_pharma.domain.shared import DomainError


def test_un_medicament_peut_avoir_plusieurs_conditionnements_independants() -> None:
    produit = Medicament(
        reference="MED-001",
        designation="Paracétamol",
        principe_actif="Paracétamol",
    )

    boite = produit.ajouter_conditionnement(
        code="BTE-20", libelle="Boîte de 20 comprimés", prix_vente=Decimal("2500")
    )
    flacon = produit.ajouter_conditionnement(
        code="FLA-100", libelle="Flacon de 100 ml", prix_vente=Decimal("3200")
    )

    assert boite.produit_id == produit.id
    assert flacon.produit_id == produit.id
    assert boite.id != flacon.id
    assert boite.prix_vente == Decimal("2500")
    assert flacon.prix_vente == Decimal("3200")


def test_un_prix_nul_ou_negatif_est_refuse() -> None:
    produit = ProduitCosmetique(reference="COS-001", designation="Lait corporel", marque="NeoCare")

    with pytest.raises(DomainError, match="strictement positif"):
        produit.ajouter_conditionnement(
            code="FLA-250", libelle="Flacon de 250 ml", prix_vente=Decimal("0")
        )


def test_deux_conditionnements_d_un_produit_ne_peuvent_pas_avoir_le_meme_code() -> None:
    produit = ProduitCosmetique(reference="COS-002", designation="Savon doux", marque="NeoCare")
    produit.ajouter_conditionnement(code="UNI", libelle="Unité", prix_vente=Decimal("1000"))

    with pytest.raises(DomainError, match="existe déjà"):
        produit.ajouter_conditionnement(
            code="UNI", libelle="Autre unité", prix_vente=Decimal("1200")
        )


def test_les_informations_obligatoires_ne_peuvent_pas_etre_vides() -> None:
    with pytest.raises(DomainError, match="référence"):
        Medicament(reference=" ", designation="Produit", principe_actif="Molécule")

    with pytest.raises(DomainError, match="principe actif"):
        Medicament(reference="MED-002", designation="Produit", principe_actif=" ")


def test_le_cip7_doit_contenir_exactement_sept_chiffres() -> None:
    with pytest.raises(DomainError, match="CIP7"):
        Medicament(
            reference="MED-CIP",
            designation="Produit",
            cip7="ABC1234",
            principe_actif="Molécule",
        )


def test_la_couverture_cnamgs_exige_un_taux_valide() -> None:
    produit = Medicament(
        reference="MED-CNAMGS",
        designation="Produit couvert",
        principe_actif="Molécule",
        pris_en_charge_cnamgs=True,
        taux_prise_en_charge_cnamgs=Decimal("80"),
    )

    assert produit.pris_en_charge_cnamgs is True
    assert produit.taux_prise_en_charge_cnamgs == Decimal("80")
    with pytest.raises(DomainError, match="strictement positif"):
        produit.modifier_couverture_cnamgs(pris_en_charge=True, taux=Decimal("0"))
    with pytest.raises(DomainError, match="compris entre"):
        produit.modifier_couverture_cnamgs(pris_en_charge=True, taux=Decimal("101"))


def test_les_regles_d_une_ligne_et_d_une_commande_achat() -> None:
    ligne = LigneCommandeAchat(
        conditionnement_id=uuid4(),
        designation="PARACÉTAMOL",
        cip7="3232018",
        quantite_commandee=20,
        quantite_recue=18,
        numero_lot="LOT-001",
        date_expiration=date(2028, 12, 31),
        prix_unitaire=Decimal("950"),
    )
    commande = CommandeAchat(
        numero_interne="CMD-2026-00001",
        fournisseur_id=uuid4(),
        emplacement_id=uuid4(),
        date_commande=date(2026, 9, 18),
        date_arrivee=date(2026, 9, 20),
        lignes=[ligne],
    )

    assert ligne.total == Decimal("17100")
    assert commande.total_general == Decimal("17100")
    with pytest.raises(DomainError, match="quantité commandée"):
        LigneCommandeAchat(
            conditionnement_id=uuid4(),
            designation="PRODUIT",
            cip7="1234567",
            quantite_commandee=0,
            quantite_recue=0,
            numero_lot="LOT",
            date_expiration=date(2028, 1, 1),
            prix_unitaire=Decimal("100"),
        )
    with pytest.raises(DomainError, match="quantité reçue"):
        LigneCommandeAchat(
            conditionnement_id=uuid4(),
            designation="PRODUIT",
            cip7="1234567",
            quantite_commandee=2,
            quantite_recue=3,
            numero_lot="LOT",
            date_expiration=date(2028, 1, 1),
            prix_unitaire=Decimal("100"),
        )
    with pytest.raises(DomainError, match="prix unitaire"):
        LigneCommandeAchat(
            conditionnement_id=uuid4(),
            designation="PRODUIT",
            cip7="1234567",
            quantite_commandee=2,
            quantite_recue=1,
            numero_lot="LOT",
            date_expiration=date(2028, 1, 1),
            prix_unitaire=Decimal("0"),
        )
    with pytest.raises(DomainError, match="date d'arrivée"):
        CommandeAchat(
            numero_interne="CMD-2",
            fournisseur_id=uuid4(),
            emplacement_id=uuid4(),
            date_commande=date(2026, 9, 20),
            date_arrivee=date(2026, 9, 19),
            lignes=[ligne],
        )
    with pytest.raises(DomainError, match="au moins une ligne"):
        CommandeAchat(
            numero_interne="CMD-3",
            fournisseur_id=uuid4(),
            emplacement_id=uuid4(),
            date_commande=date(2026, 9, 20),
            date_arrivee=date(2026, 9, 20),
        )
