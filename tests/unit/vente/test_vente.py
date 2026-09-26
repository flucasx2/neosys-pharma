from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from neosys_pharma.domain.shared import DomainError
from neosys_pharma.domain.vente import AllocationLot, EtatVente, PosteVente, Vente


def test_une_vente_calcule_le_total_de_ses_lignes() -> None:
    vente = Vente(
        poste_id=uuid4(),
        secteur_id=uuid4(),
        emplacement_id=uuid4(),
        date_commerciale=date(2026, 9, 19),
    )
    vente.ajouter_ligne(
        conditionnement_id=uuid4(),
        designation="Boîte de médicament",
        quantite=2,
        prix_unitaire=Decimal("2500"),
    )
    vente.ajouter_ligne(
        conditionnement_id=uuid4(),
        designation="Lait corporel",
        quantite=1,
        prix_unitaire=Decimal("4000"),
    )

    assert vente.montant_total == Decimal("9000")


def test_une_vente_possede_un_numero_de_ticket_stable_et_lisible() -> None:
    vente = Vente(
        id=UUID("45da2e49-b574-4813-bfdd-8d59f36c841a"),
        poste_id=uuid4(),
        secteur_id=uuid4(),
        emplacement_id=uuid4(),
        date_commerciale=date(2026, 9, 20),
    )

    assert vente.numero_ticket == "T-20260920-45DA2E49"


def test_toutes_les_lignes_doivent_etre_entierement_allouees() -> None:
    vente = Vente(
        poste_id=uuid4(),
        secteur_id=uuid4(),
        emplacement_id=uuid4(),
        date_commerciale=date(2026, 9, 19),
    )
    ligne = vente.ajouter_ligne(
        conditionnement_id=uuid4(),
        designation="Produit",
        quantite=2,
        prix_unitaire=Decimal("1000"),
    )

    with pytest.raises(DomainError, match="entièrement réservées"):
        vente.placer_en_attente(
            [
                AllocationLot(
                    ligne_vente_id=ligne.id,
                    lot_id=uuid4(),
                    quantite=1,
                    date_expiration=date(2027, 1, 31),
                )
            ]
        )


def test_une_vente_en_attente_n_est_plus_modifiable() -> None:
    vente = Vente(
        poste_id=uuid4(),
        secteur_id=uuid4(),
        emplacement_id=uuid4(),
        date_commerciale=date(2026, 9, 19),
    )
    ligne = vente.ajouter_ligne(
        conditionnement_id=uuid4(),
        designation="Produit",
        quantite=1,
        prix_unitaire=Decimal("1000"),
    )
    vente.placer_en_attente(
        [
            AllocationLot(
                ligne_vente_id=ligne.id,
                lot_id=uuid4(),
                quantite=1,
                date_expiration=date(2027, 1, 31),
            )
        ]
    )

    assert vente.etat is EtatVente.EN_ATTENTE_PAIEMENT
    with pytest.raises(DomainError, match="plus modifiable"):
        vente.ajouter_ligne(
            conditionnement_id=uuid4(),
            designation="Autre",
            quantite=1,
            prix_unitaire=Decimal("500"),
        )


def test_un_poste_exige_un_code() -> None:
    with pytest.raises(DomainError, match="code"):
        PosteVente(code=" ", secteur_id=uuid4(), emplacement_id=uuid4())
