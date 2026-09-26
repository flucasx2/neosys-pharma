from datetime import date
from decimal import Decimal
from uuid import uuid4

from neosys_pharma.application.ports import CatalogueRepository, StockRepository
from neosys_pharma.domain.catalogue import ProduitCosmetique
from neosys_pharma.domain.stock import Emplacement, Lot, StockEmplacement
from neosys_pharma.infrastructure.persistence import (
    InMemoryCatalogueRepository,
    InMemoryStockRepository,
)


def test_depot_catalogue_en_memoire_respecte_le_port() -> None:
    depot: CatalogueRepository = InMemoryCatalogueRepository()
    produit = ProduitCosmetique(reference="COS-100", designation="Crème", marque="NeoCare")
    conditionnement = produit.ajouter_conditionnement(
        code="POT-50", libelle="Pot de 50 ml", prix_vente=Decimal("4500")
    )

    depot.enregistrer_produit(produit)

    assert depot.obtenir_produit(produit.id) is produit
    assert depot.obtenir_conditionnement(conditionnement.id) is conditionnement
    assert depot.obtenir_produit(uuid4()) is None


def test_depot_stock_filtre_les_positions_par_conditionnement_et_emplacement() -> None:
    depot: StockRepository = InMemoryStockRepository()
    emplacement = Emplacement(code="RAY-C", libelle="Rayon cosmétique")
    conditionnement_id = uuid4()
    lot = Lot(
        conditionnement_id=conditionnement_id,
        numero="LOT-REP",
        date_expiration=date(2028, 1, 31),
    )
    position = StockEmplacement(
        lot_id=lot.id,
        emplacement_id=emplacement.id,
        quantite_physique=12,
    )
    depot.enregistrer_emplacement(emplacement)
    depot.enregistrer_lot(lot)
    depot.enregistrer_position(position)

    assert depot.obtenir_lot(lot.id) is lot
    assert depot.obtenir_emplacement(emplacement.id) is emplacement
    assert depot.obtenir_position(lot_id=lot.id, emplacement_id=emplacement.id) is position
    assert depot.lister_positions(
        conditionnement_id=conditionnement_id,
        emplacement_id=emplacement.id,
    ) == (position,)
    assert (
        depot.lister_positions(
            conditionnement_id=uuid4(),
            emplacement_id=emplacement.id,
        )
        == ()
    )
