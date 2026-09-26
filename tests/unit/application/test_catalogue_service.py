from decimal import Decimal
from uuid import uuid4

import pytest

from neosys_pharma.application.dto import (
    AjouterConditionnement,
    CreerFournisseur,
    CreerMedicament,
    CreerProduitCosmetique,
    DefinirTarifFournisseur,
    ModifierConditionnement,
    ModifierFournisseur,
    ModifierProduit,
)
from neosys_pharma.application.services import CatalogueService
from neosys_pharma.domain.shared import DomainError
from neosys_pharma.infrastructure.persistence import InMemoryCatalogueRepository


def test_creer_un_medicament_et_son_conditionnement() -> None:
    depot = InMemoryCatalogueRepository()
    service = CatalogueService(depot)

    produit = service.creer_medicament(
        CreerMedicament(
            reference="MED-API-001",
            designation="Paracétamol",
            principe_actif="Paracétamol",
        )
    )
    conditionnement = service.ajouter_conditionnement(
        AjouterConditionnement(
            produit_id=produit.id,
            code="BTE-20",
            libelle="Boîte de 20 comprimés",
            prix_vente=Decimal("2500"),
        )
    )

    assert depot.obtenir_produit(produit.id) is produit
    assert depot.obtenir_conditionnement(conditionnement.id) is conditionnement


def test_creer_un_cosmetique() -> None:
    depot = InMemoryCatalogueRepository()
    service = CatalogueService(depot)

    produit = service.creer_produit_cosmetique(
        CreerProduitCosmetique(
            reference="COS-API-001",
            designation="Lait corporel",
            marque="NeoCare",
        )
    )

    assert depot.obtenir_produit(produit.id) is produit


def test_une_reference_produit_doit_etre_unique() -> None:
    service = CatalogueService(InMemoryCatalogueRepository())
    commande = CreerMedicament(
        reference="MED-DOUBLON",
        designation="Produit A",
        principe_actif="Molécule A",
    )
    service.creer_medicament(commande)

    with pytest.raises(DomainError, match="existe déjà"):
        service.creer_medicament(commande)


def test_ajouter_un_conditionnement_a_un_produit_inconnu_est_refuse() -> None:
    service = CatalogueService(InMemoryCatalogueRepository())

    with pytest.raises(DomainError, match="produit est inconnu"):
        service.ajouter_conditionnement(
            AjouterConditionnement(
                produit_id=uuid4(),
                code="UNI",
                libelle="Unité",
                prix_vente=Decimal("1000"),
            )
        )


def test_modifier_produits_conditionnements_et_principes_actifs() -> None:
    service = CatalogueService(InMemoryCatalogueRepository())
    service.initialiser_principes_actifs()
    service.initialiser_principes_actifs()
    principes = service.lister_principes_actifs()
    paracetamol = next(item for item in principes if item.libelle == "Paracétamol")
    medicament = service.creer_medicament(
        CreerMedicament(
            reference="MED-MOD-001",
            designation="Paracétamol",
            principe_actif_id=paracetamol.id,
        )
    )
    cosmetique = service.creer_produit_cosmetique(
        CreerProduitCosmetique(
            reference="COS-MOD-001",
            designation="Lait",
            marque="NeoCare",
        )
    )
    article = service.ajouter_conditionnement(
        AjouterConditionnement(
            produit_id=cosmetique.id,
            code="LAIT-250",
            libelle="Flacon 250 ml",
            prix_vente=Decimal("4000"),
        )
    )
    service.ajouter_conditionnement(
        AjouterConditionnement(
            produit_id=cosmetique.id,
            code="LAIT-500",
            libelle="Flacon 500 ml",
            prix_vente=Decimal("7000"),
        )
    )

    modifie = service.modifier_produit(
        ModifierProduit(
            produit_id=cosmetique.id,
            reference="COS-MOD-001",
            designation="Lait hydratant",
            information="Nouvelle marque",
        )
    )
    conditionnement = service.modifier_conditionnement(
        ModifierConditionnement(
            conditionnement_id=article.id,
            code="LAIT-250",
            libelle="Flacon pompe 250 ml",
            prix_vente=Decimal("4200"),
        )
    )

    assert modifie.designation == "Lait hydratant"
    assert conditionnement.prix_vente == Decimal("4200")
    with pytest.raises(DomainError, match="référence produit"):
        service.modifier_produit(
            ModifierProduit(
                produit_id=cosmetique.id,
                reference=medicament.reference,
                designation="Doublon",
                information="Marque",
            )
        )
    with pytest.raises(DomainError, match="conditionnement"):
        service.modifier_conditionnement(
            ModifierConditionnement(
                conditionnement_id=article.id,
                code="LAIT-500",
                libelle="Doublon",
                prix_vente=Decimal("1000"),
            )
        )
    with pytest.raises(DomainError, match="conditionnement est inconnu"):
        service.modifier_conditionnement(
            ModifierConditionnement(
                conditionnement_id=uuid4(),
                code="INCONNU",
                libelle="Inconnu",
                prix_vente=Decimal("1000"),
            )
        )
    with pytest.raises(DomainError, match="principe actif est inconnu"):
        service.creer_medicament(
            CreerMedicament(
                reference="MED-INCONNU",
                designation="Inconnu",
                principe_actif_id=uuid4(),
            )
        )


def test_gerer_fournisseurs_et_mettre_a_jour_un_tarif() -> None:
    service = CatalogueService(InMemoryCatalogueRepository())
    produit = service.creer_medicament(
        CreerMedicament(
            reference="MED-ACH-001",
            designation="Paracétamol",
            principe_actif="Paracétamol",
        )
    )
    article = service.ajouter_conditionnement(
        AjouterConditionnement(
            produit_id=produit.id,
            code="PARA-B20",
            libelle="Boîte de 20",
            prix_vente=Decimal("1500"),
        )
    )
    fournisseur = service.creer_fournisseur(
        CreerFournisseur(code="FOUR-001", raison_sociale="Pharma Distribution")
    )
    tarif = service.definir_tarif_fournisseur(
        DefinirTarifFournisseur(
            fournisseur_id=fournisseur.id,
            conditionnement_id=article.id,
            prix_achat=Decimal("900"),
            reference_fournisseur="PD-01",
        )
    )
    actualise = service.definir_tarif_fournisseur(
        DefinirTarifFournisseur(
            fournisseur_id=fournisseur.id,
            conditionnement_id=article.id,
            prix_achat=Decimal("950"),
            reference_fournisseur="PD-02",
        )
    )
    modifie = service.modifier_fournisseur(
        ModifierFournisseur(
            fournisseur_id=fournisseur.id,
            code="FOUR-001",
            raison_sociale="Pharma Distribution Gabon",
            telephone="01234567",
            email="contact@example.ga",
            actif=False,
        )
    )

    assert actualise.id == tarif.id
    assert actualise.prix_achat == Decimal("950")
    assert service.lister_tarifs_fournisseurs() == (actualise,)
    assert service.lister_fournisseurs() == (modifie,)
    with pytest.raises(DomainError, match="code fournisseur"):
        service.creer_fournisseur(CreerFournisseur(code="FOUR-001", raison_sociale="Doublon"))
    with pytest.raises(DomainError, match="fournisseur est inconnu"):
        service.modifier_fournisseur(
            ModifierFournisseur(
                fournisseur_id=uuid4(),
                code="ABSENT",
                raison_sociale="Absent",
            )
        )
    with pytest.raises(DomainError, match="fournisseur est inconnu"):
        service.definir_tarif_fournisseur(
            DefinirTarifFournisseur(
                fournisseur_id=uuid4(),
                conditionnement_id=article.id,
                prix_achat=Decimal("100"),
            )
        )


def test_generer_les_codes_et_utiliser_une_marque_du_referentiel() -> None:
    service = CatalogueService(InMemoryCatalogueRepository())
    service.initialiser_marques()
    service.initialiser_marques()
    marque = next(item for item in service.lister_marques() if item.libelle == "NEOCARE")
    produit = service.creer_produit_cosmetique(
        CreerProduitCosmetique(
            designation="LAIT CORPOREL",
            cip7="7654321",
            marque_id=marque.id,
        )
    )
    article = service.ajouter_conditionnement(
        AjouterConditionnement(
            produit_id=produit.id,
            libelle="FLACON 250 ML",
            prix_vente=Decimal("4000"),
        )
    )
    fournisseur = service.creer_fournisseur(CreerFournisseur(raison_sociale="CENTRALE PHARMA"))

    assert produit.reference == "COS-00001"
    assert produit.marque_id == marque.id
    assert article.code == "ART-000001"
    assert fournisseur.code == "FOUR-0001"
    with pytest.raises(DomainError, match="CIP7 existe"):
        service.creer_medicament(
            CreerMedicament(
                designation="DOUBLON",
                cip7="7654321",
                principe_actif="MOLÉCULE",
            )
        )
    with pytest.raises(DomainError, match="marque est inconnue"):
        service.creer_produit_cosmetique(
            CreerProduitCosmetique(
                designation="INCONNU",
                cip7="1111111",
                marque_id=uuid4(),
            )
        )
    with pytest.raises(DomainError, match="conditionnement est inconnu"):
        service.definir_tarif_fournisseur(
            DefinirTarifFournisseur(
                fournisseur_id=fournisseur.id,
                conditionnement_id=uuid4(),
                prix_achat=Decimal("100"),
            )
        )
