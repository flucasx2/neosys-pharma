from datetime import date
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from neosys_pharma.domain.catalogue import (
    CommandeAchat,
    Fournisseur,
    LigneCommandeAchat,
    Marque,
    Medicament,
    OrganismePriseEnCharge,
    PrincipeActif,
    ProduitCosmetique,
    TarifFournisseur,
)
from neosys_pharma.domain.stock import (
    Emplacement,
    Lot,
    MouvementStock,
    StockEmplacement,
    TypeMouvement,
)
from neosys_pharma.infrastructure.persistence import (
    SqlAlchemyCatalogueRepository,
    SqlAlchemyStockRepository,
)
from neosys_pharma.infrastructure.persistence.database import create_session_factory
from neosys_pharma.infrastructure.persistence.models import Base


def _repositories() -> tuple[SqlAlchemyCatalogueRepository, SqlAlchemyStockRepository]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = create_session_factory(engine)
    return SqlAlchemyCatalogueRepository(factory), SqlAlchemyStockRepository(factory)


def test_catalogue_est_relu_depuis_la_base() -> None:
    catalogue, _ = _repositories()
    produit = Medicament(
        reference="MED-SQL-001",
        designation="Paracétamol",
        principe_actif="Paracétamol",
    )
    conditionnement = produit.ajouter_conditionnement(
        code="BTE-20",
        libelle="Boîte de 20 comprimés",
        prix_vente=Decimal("2500"),
    )

    catalogue.enregistrer_produit(produit)
    recharge = catalogue.obtenir_produit(produit.id)

    assert recharge is not None
    assert recharge.reference == "MED-SQL-001"
    assert recharge.conditionnements[0].id == conditionnement.id
    assert catalogue.obtenir_produit_par_reference("MED-SQL-001") is not None
    assert catalogue.obtenir_conditionnement(conditionnement.id) is not None


def test_principe_fournisseur_et_tarif_sont_relus_depuis_la_base() -> None:
    catalogue, _ = _repositories()
    principe = PrincipeActif(libelle="Paracétamol")
    catalogue.enregistrer_principe_actif(principe)
    marque = Marque(libelle="NEOCARE")
    catalogue.enregistrer_marque(marque)
    produit = Medicament(
        reference="MED-ACH-001",
        designation="Paracétamol 500 mg",
        cip7="3232018",
        principe_actif=principe.libelle,
        principe_actif_id=principe.id,
    )
    conditionnement = produit.ajouter_conditionnement(
        code="PARA-B20",
        libelle="Boîte de 20 comprimés",
        prix_vente=Decimal("1500"),
    )
    catalogue.enregistrer_produit(produit)
    fournisseur = Fournisseur(
        code="FOUR-SQL",
        raison_sociale="Pharma Distribution",
    )
    catalogue.enregistrer_fournisseur(fournisseur)
    tarif = TarifFournisseur(
        fournisseur_id=fournisseur.id,
        conditionnement_id=conditionnement.id,
        prix_achat=Decimal("950"),
        reference_fournisseur="PD-PARA-20",
    )
    catalogue.enregistrer_tarif_fournisseur(tarif)
    commande = CommandeAchat(
        numero_interne="CMD-2026-00001",
        fournisseur_id=fournisseur.id,
        emplacement_id=uuid4(),
        date_commande=date(2026, 9, 18),
        date_arrivee=date(2026, 9, 20),
        lignes=[
            LigneCommandeAchat(
                conditionnement_id=conditionnement.id,
                designation="Paracétamol — Boîte de 20 comprimés",
                cip7="3232018",
                quantite_commandee=20,
                quantite_recue=18,
                numero_lot="LOT-001",
                date_expiration=date(2028, 12, 31),
                prix_unitaire=Decimal("950"),
            )
        ],
    )
    catalogue.enregistrer_commande_achat(commande)

    assert catalogue.obtenir_principe_actif(principe.id) == principe
    assert catalogue.obtenir_principe_actif_par_libelle("Paracétamol") == principe
    assert catalogue.lister_principes_actifs() == (principe,)
    assert catalogue.lister_marques() == (marque,)
    assert catalogue.obtenir_marque(marque.id) == marque
    assert catalogue.obtenir_produit_par_cip7("3232018") is not None
    assert catalogue.obtenir_fournisseur(fournisseur.id) == fournisseur
    assert catalogue.obtenir_fournisseur_par_code("FOUR-SQL") == fournisseur
    assert catalogue.lister_fournisseurs() == (fournisseur,)
    assert (
        catalogue.obtenir_tarif_fournisseur(
            fournisseur_id=fournisseur.id,
            conditionnement_id=conditionnement.id,
        )
        == tarif
    )
    assert catalogue.lister_tarifs_fournisseurs() == (tarif,)
    assert catalogue.lister_commandes_achat()[0].total_general == Decimal("17100")
    assert catalogue.lister_produits()[0].principe_actif_id == principe.id  # type: ignore[union-attr]


def test_cip_cosmetique_couverture_et_organisme_sont_relus_depuis_la_base() -> None:
    catalogue, _ = _repositories()
    produit = ProduitCosmetique(
        reference="COS-SQL-CIP",
        designation="Lait couvert",
        cip7="7654321",
        marque="NEOCARE",
        pris_en_charge_cnamgs=True,
        taux_prise_en_charge_cnamgs=Decimal("60"),
    )
    organisme = OrganismePriseEnCharge(
        code="ORG-0001",
        nom="CNAMGS",
        type_organisme="CNAMGS",
        documents_requis=("CARTE CNAMGS", "ORDONNANCE"),
    )
    catalogue.enregistrer_produit(produit)
    catalogue.enregistrer_organisme(organisme)

    recharge = catalogue.obtenir_produit(produit.id)
    assert recharge is not None
    assert recharge.cip7 == "7654321"
    assert recharge.taux_prise_en_charge_cnamgs == Decimal("60")
    assert catalogue.obtenir_organisme_par_code("ORG-0001") == organisme
    assert catalogue.lister_organismes() == (organisme,)


def test_stock_et_mouvements_sont_relus_depuis_la_base() -> None:
    catalogue, stock = _repositories()
    produit = Medicament(
        reference="MED-SQL-002",
        designation="Amoxicilline",
        principe_actif="Amoxicilline",
    )
    conditionnement = produit.ajouter_conditionnement(
        code="BTE-12",
        libelle="Boîte de 12 gélules",
        prix_vente=Decimal("5000"),
    )
    catalogue.enregistrer_produit(produit)
    emplacement = Emplacement(code="RAY-SQL", libelle="Rayon SQL")
    lot = Lot(
        conditionnement_id=conditionnement.id,
        numero="LOT-SQL-001",
        date_expiration=date(2028, 1, 31),
    )
    position = StockEmplacement(
        lot_id=lot.id,
        emplacement_id=emplacement.id,
        quantite_physique=15,
    )
    mouvement = MouvementStock(
        type=TypeMouvement.RECEPTION,
        lot_id=lot.id,
        quantite=15,
        emplacement_destination_id=emplacement.id,
        motif="Réception SQL",
    )

    stock.enregistrer_emplacement(emplacement)
    stock.enregistrer_lot(lot)
    stock.enregistrer_position(position)
    stock.enregistrer_mouvement(mouvement)

    assert stock.obtenir_lot(lot.id) is not None
    assert stock.obtenir_emplacement(emplacement.id) is not None
    assert (
        stock.obtenir_position(lot_id=lot.id, emplacement_id=emplacement.id).quantite_physique == 15
    )  # type: ignore[union-attr]
    assert (
        stock.lister_positions(
            conditionnement_id=conditionnement.id,
            emplacement_id=emplacement.id,
        )[0].quantite_disponible
        == 15
    )
    assert stock.lister_mouvements()[0].motif == "Réception SQL"
    assert len(stock.lister_lots()) == 1
    assert len(stock.lister_emplacements()) == 1
    assert len(stock.lister_toutes_positions()) == 1
