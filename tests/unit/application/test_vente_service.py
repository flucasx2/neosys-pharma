from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from neosys_pharma.application.dto import (
    AjouterConditionnement,
    AjouterLigneVente,
    CreerMedicament,
    CreerPosteVente,
    CreerProduitCosmetique,
    ReceptionnerLot,
)
from neosys_pharma.application.services import CatalogueService, StockService
from neosys_pharma.application.vente_service import VenteService
from neosys_pharma.domain.stock import Inventaire, StockInsuffisant
from neosys_pharma.domain.vente import EtatVente
from neosys_pharma.infrastructure.persistence import (
    InMemoryCatalogueRepository,
    InMemoryStockRepository,
    InMemoryVenteRepository,
)


def _contexte() -> tuple[
    CatalogueService,
    StockService,
    VenteService,
    InMemoryStockRepository,
    UUID,
]:
    catalogue_depot = InMemoryCatalogueRepository()
    stock_depot = InMemoryStockRepository()
    catalogue = CatalogueService(catalogue_depot)
    stock = StockService(stock_depot, Inventaire(), catalogue=catalogue_depot)
    ventes = VenteService(InMemoryVenteRepository(), catalogue_depot, stock)
    emplacement = stock.creer_emplacement(code="RAY-V", libelle="Rayon vente")
    return catalogue, stock, ventes, stock_depot, emplacement.id


def _creer_conditionnements(
    catalogue: CatalogueService,
) -> tuple[UUID, UUID]:
    medicament = catalogue.creer_medicament(
        CreerMedicament(
            reference="MED-V-001",
            designation="Paracétamol",
            principe_actif="Paracétamol",
        )
    )
    cosmetique = catalogue.creer_produit_cosmetique(
        CreerProduitCosmetique(
            reference="COS-V-001",
            designation="Lait corporel",
            marque="NeoCare",
        )
    )
    boite = catalogue.ajouter_conditionnement(
        AjouterConditionnement(
            produit_id=medicament.id,
            code="BTE-20",
            libelle="Boîte de 20 comprimés",
            prix_vente=Decimal("2500"),
        )
    )
    flacon = catalogue.ajouter_conditionnement(
        AjouterConditionnement(
            produit_id=cosmetique.id,
            code="FLA-250",
            libelle="Flacon de 250 ml",
            prix_vente=Decimal("4000"),
        )
    )
    return boite.id, flacon.id


def test_preparer_une_vente_mixte_reserve_le_stock_selon_fefo() -> None:
    catalogue, stock, ventes, stock_depot, emplacement_id = _contexte()
    medicament_id, cosmetique_id = _creer_conditionnements(catalogue)
    for conditionnement_id, numero, quantite in (
        (medicament_id, "LOT-MED", 5),
        (cosmetique_id, "LOT-COS", 3),
    ):
        stock.receptionner_lot(
            ReceptionnerLot(
                conditionnement_id=conditionnement_id,
                numero_lot=numero,
                date_expiration=date(2027, 6, 30),
                emplacement_id=emplacement_id,
                quantite=quantite,
                motif="Réception",
            )
        )
    poste = ventes.creer_poste(
        CreerPosteVente(
            code="POSTE-01",
            secteur_id=uuid4(),
            emplacement_id=emplacement_id,
        )
    )
    vente = ventes.creer_vente(
        poste_id=poste.id,
        date_commerciale=date(2026, 9, 19),
    )
    ventes.ajouter_ligne(
        AjouterLigneVente(
            vente_id=vente.id,
            conditionnement_id=medicament_id,
            quantite=2,
        )
    )
    ventes.ajouter_ligne(
        AjouterLigneVente(
            vente_id=vente.id,
            conditionnement_id=cosmetique_id,
            quantite=1,
        )
    )

    vente_preparee = ventes.preparer(vente.id)

    assert vente_preparee.etat is EtatVente.EN_ATTENTE_PAIEMENT
    assert vente_preparee.montant_total == Decimal("9000")
    assert len(vente_preparee.allocations) == 2
    assert (
        sum(position.quantite_reservee for position in stock_depot.lister_toutes_positions()) == 3
    )


def test_echec_d_une_ligne_libere_les_reservations_deja_effectuees() -> None:
    catalogue, stock, ventes, stock_depot, emplacement_id = _contexte()
    medicament_id, cosmetique_id = _creer_conditionnements(catalogue)
    stock.receptionner_lot(
        ReceptionnerLot(
            conditionnement_id=medicament_id,
            numero_lot="LOT-DISPONIBLE",
            date_expiration=date(2027, 6, 30),
            emplacement_id=emplacement_id,
            quantite=5,
            motif="Réception",
        )
    )
    poste = ventes.creer_poste(
        CreerPosteVente(
            code="POSTE-02",
            secteur_id=uuid4(),
            emplacement_id=emplacement_id,
        )
    )
    vente = ventes.creer_vente(
        poste_id=poste.id,
        date_commerciale=date(2026, 9, 19),
    )
    for conditionnement_id in (medicament_id, cosmetique_id):
        ventes.ajouter_ligne(
            AjouterLigneVente(
                vente_id=vente.id,
                conditionnement_id=conditionnement_id,
                quantite=1,
            )
        )

    with pytest.raises(StockInsuffisant):
        ventes.preparer(vente.id)

    assert (
        sum(position.quantite_reservee for position in stock_depot.lister_toutes_positions()) == 0
    )


def test_annuler_une_vente_libere_ses_reservations() -> None:
    catalogue, stock, ventes, stock_depot, emplacement_id = _contexte()
    medicament_id, _ = _creer_conditionnements(catalogue)
    stock.receptionner_lot(
        ReceptionnerLot(
            conditionnement_id=medicament_id,
            numero_lot="LOT-ANNULATION",
            date_expiration=date(2027, 6, 30),
            emplacement_id=emplacement_id,
            quantite=2,
            motif="Réception",
        )
    )
    poste = ventes.creer_poste(
        CreerPosteVente(
            code="POSTE-03",
            secteur_id=uuid4(),
            emplacement_id=emplacement_id,
        )
    )
    vente = ventes.creer_vente(
        poste_id=poste.id,
        date_commerciale=date(2026, 9, 19),
    )
    ventes.ajouter_ligne(
        AjouterLigneVente(
            vente_id=vente.id,
            conditionnement_id=medicament_id,
            quantite=1,
        )
    )
    ventes.preparer(vente.id)

    vente_annulee = ventes.annuler(vente.id)

    assert vente_annulee.etat is EtatVente.ANNULEE
    assert stock_depot.lister_toutes_positions()[0].quantite_reservee == 0


def test_un_poste_peut_preparer_avec_le_stock_d_un_autre_emplacement() -> None:
    catalogue, stock, ventes, _, emplacement_poste = _contexte()
    article_id, _ = _creer_conditionnements(catalogue)
    autre = stock.creer_emplacement(code="RAY-V-2", libelle="Deuxième rayon")
    stock.receptionner_lot(
        ReceptionnerLot(
            conditionnement_id=article_id,
            numero_lot="LOT-AUTRE-RAYON",
            date_expiration=date(2028, 1, 31),
            emplacement_id=autre.id,
            quantite=2,
            motif="Réception",
        )
    )
    poste = ventes.creer_poste(
        CreerPosteVente(code="POSTE-GLOBAL", secteur_id=uuid4(), emplacement_id=emplacement_poste)
    )
    vente = ventes.creer_vente(poste_id=poste.id, date_commerciale=date(2026, 9, 21))
    ventes.ajouter_ligne(
        AjouterLigneVente(vente_id=vente.id, conditionnement_id=article_id, quantite=1)
    )

    preparee = ventes.preparer(vente.id)

    assert preparee.etat is EtatVente.EN_ATTENTE_PAIEMENT
    assert preparee.allocations[0].emplacement_id == autre.id


def test_un_poste_peut_preparer_avec_le_stock_de_la_reserve() -> None:
    catalogue, stock, ventes, _, emplacement_poste = _contexte()
    article_id, _ = _creer_conditionnements(catalogue)
    reserve = stock.creer_emplacement(
        code="RESERVE", libelle="Réserve principale", autorise_vente=False
    )
    stock.receptionner_lot(
        ReceptionnerLot(
            conditionnement_id=article_id,
            numero_lot="LOT-RESERVE",
            date_expiration=date(2028, 1, 31),
            emplacement_id=reserve.id,
            quantite=9,
            motif="Réception",
        )
    )
    poste = ventes.creer_poste(
        CreerPosteVente(code="POSTE-RESERVE", secteur_id=uuid4(), emplacement_id=emplacement_poste)
    )
    vente = ventes.creer_vente(poste_id=poste.id, date_commerciale=date(2026, 9, 22))
    ventes.ajouter_ligne(
        AjouterLigneVente(vente_id=vente.id, conditionnement_id=article_id, quantite=2)
    )

    preparee = ventes.preparer(vente.id)

    assert preparee.allocations[0].emplacement_id == reserve.id
    assert preparee.allocations[0].quantite == 2


def test_stock_insuffisant_explique_un_lot_perime() -> None:
    catalogue, stock, ventes, _, emplacement_id = _contexte()
    article_id, _ = _creer_conditionnements(catalogue)
    stock.receptionner_lot(
        ReceptionnerLot(
            conditionnement_id=article_id,
            numero_lot="LOT-PERIME",
            date_expiration=date(2026, 8, 31),
            emplacement_id=emplacement_id,
            quantite=9,
            motif="Réception",
        )
    )
    poste = ventes.creer_poste(
        CreerPosteVente(code="POSTE-PERIME", secteur_id=uuid4(), emplacement_id=emplacement_id)
    )
    vente = ventes.creer_vente(poste_id=poste.id, date_commerciale=date(2026, 9, 22))
    ventes.ajouter_ligne(
        AjouterLigneVente(vente_id=vente.id, conditionnement_id=article_id, quantite=2)
    )

    with pytest.raises(
        StockInsuffisant,
        match=(
            r"2 unité\(s\) demandée\(s\).*9 physique\(s\).*"
            r"0 vendable\(s\).*9 unité\(s\) périmée\(s\)"
        ),
    ):
        ventes.preparer(vente.id)


def test_encaissement_multiple_finalise_les_tickets_et_sort_le_stock() -> None:
    catalogue, stock, ventes, stock_depot, emplacement_id = _contexte()
    article_id, _ = _creer_conditionnements(catalogue)
    stock.receptionner_lot(
        ReceptionnerLot(
            conditionnement_id=article_id,
            numero_lot="LOT-CAISSE",
            date_expiration=date(2028, 1, 31),
            emplacement_id=emplacement_id,
            quantite=5,
            motif="Réception",
        )
    )
    poste = ventes.creer_poste(
        CreerPosteVente(code="POSTE-CAISSE", secteur_id=uuid4(), emplacement_id=emplacement_id)
    )
    tickets = []
    for _ in range(2):
        vente = ventes.creer_vente(poste_id=poste.id, date_commerciale=date(2026, 9, 21))
        ventes.ajouter_ligne(
            AjouterLigneVente(vente_id=vente.id, conditionnement_id=article_id, quantite=1)
        )
        tickets.append(ventes.preparer(vente.id))

    finalisees = ventes.encaisser(
        vente_ids=[item.id for item in tickets],
        reglements=[{"mode": "ESPECES", "montant": "5000"}],
    )

    assert {item.etat for item in finalisees} == {EtatVente.FINALISEE}
    assert len({item.encaissement_id for item in finalisees}) == 1
    position = stock_depot.lister_toutes_positions()[0]
    assert position.quantite_physique == 3
    assert position.quantite_reservee == 0
