from datetime import date
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from neosys_pharma.domain.vente import AllocationLot, EtatVente, PosteVente, Vente
from neosys_pharma.infrastructure.persistence import SqlAlchemyVenteRepository
from neosys_pharma.infrastructure.persistence.database import create_session_factory
from neosys_pharma.infrastructure.persistence.models import Base


def test_une_vente_complete_est_rechargee_depuis_la_base() -> None:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    depot = SqlAlchemyVenteRepository(create_session_factory(engine))
    emplacement_id = uuid4()
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "INSERT INTO emplacements (id, code, libelle, autorise_vente) VALUES (?, ?, ?, ?)",
            (str(emplacement_id), "RAY-VSQL", "Rayon vente SQL", 1),
        )
    poste = PosteVente(
        code="POSTE-SQL",
        secteur_id=uuid4(),
        emplacement_id=emplacement_id,
    )
    depot.enregistrer_poste(poste)
    vente = Vente(
        poste_id=poste.id,
        secteur_id=poste.secteur_id,
        emplacement_id=poste.emplacement_id,
        date_commerciale=date(2026, 9, 19),
    )
    conditionnement_id = uuid4()
    lot_id = uuid4()
    with engine.begin() as connection:
        produit_id = uuid4()
        connection.exec_driver_sql(
            "INSERT INTO produits (id, type_produit, reference, designation) VALUES (?, ?, ?, ?)",
            (str(produit_id), "medicament", "MED-VSQL", "Produit"),
        )
        connection.exec_driver_sql(
            "INSERT INTO conditionnements "
            "(id, produit_id, code, libelle, prix_vente) VALUES (?, ?, ?, ?, ?)",
            (str(conditionnement_id), str(produit_id), "BTE", "Boîte", 2500),
        )
        connection.exec_driver_sql(
            "INSERT INTO lots "
            "(id, conditionnement_id, numero, date_expiration, etat) "
            "VALUES (?, ?, ?, ?, ?)",
            (str(lot_id), str(conditionnement_id), "LOT-VSQL", "2027-12-31", "actif"),
        )
    ligne = vente.ajouter_ligne(
        conditionnement_id=conditionnement_id,
        designation="Boîte",
        quantite=2,
        prix_unitaire=Decimal("2500"),
    )
    vente.placer_en_attente(
        [
            AllocationLot(
                ligne_vente_id=ligne.id,
                lot_id=lot_id,
                quantite=2,
                date_expiration=date(2027, 12, 31),
            )
        ]
    )

    depot.enregistrer_vente(vente)
    recharge = depot.obtenir_vente(vente.id)

    assert depot.obtenir_poste(poste.id) == poste
    assert recharge is not None
    assert recharge.etat is EtatVente.EN_ATTENTE_PAIEMENT
    assert recharge.montant_total == Decimal("5000")
    assert len(recharge.lignes) == 1
    assert len(recharge.allocations) == 1
