from dataclasses import dataclass

from sqlalchemy import Engine, inspect, text

from neosys_pharma.application.administration_service import AdministrationService
from neosys_pharma.application.fidelite_service import FideliteService
from neosys_pharma.application.services import AchatService, CatalogueService, StockService
from neosys_pharma.application.vente_service import VenteService
from neosys_pharma.domain.stock import Inventaire
from neosys_pharma.infrastructure.persistence import (
    SqlAlchemyAdministrationRepository,
    SqlAlchemyCatalogueRepository,
    SqlAlchemyFideliteRepository,
    SqlAlchemyStockRepository,
    SqlAlchemyVenteRepository,
)
from neosys_pharma.infrastructure.persistence.database import (
    create_database_engine,
    create_session_factory,
)
from neosys_pharma.infrastructure.persistence.models import Base


@dataclass(slots=True)
class ApplicationContainer:
    catalogue: CatalogueService
    stock: StockService
    ventes: VenteService
    achats: AchatService | None = None
    fidelite: FideliteService | None = None
    administration: AdministrationService | None = None


def _mettre_a_niveau_schema_legacy(engine: Engine) -> None:
    """Rend les bases SQLite du prototype précédent lisibles sans perte."""
    inspector = inspect(engine)
    if "produits" not in inspector.get_table_names():
        return
    colonnes = {colonne["name"] for colonne in inspector.get_columns("produits")}
    if "principe_actif_id" not in colonnes:
        with engine.begin() as connexion:
            connexion.execute(text("ALTER TABLE produits ADD COLUMN principe_actif_id VARCHAR(36)"))
    if "cip7" not in colonnes:
        with engine.begin() as connexion:
            connexion.execute(text("ALTER TABLE produits ADD COLUMN cip7 VARCHAR(7)"))
    if "marque_id" not in colonnes:
        with engine.begin() as connexion:
            connexion.execute(text("ALTER TABLE produits ADD COLUMN marque_id VARCHAR(36)"))
    if "pris_en_charge_cnamgs" not in colonnes:
        with engine.begin() as connexion:
            connexion.execute(
                text(
                    "ALTER TABLE produits ADD COLUMN pris_en_charge_cnamgs BOOLEAN "
                    "NOT NULL DEFAULT 0"
                )
            )
    if "taux_prise_en_charge_cnamgs" not in colonnes:
        with engine.begin() as connexion:
            connexion.execute(
                text(
                    "ALTER TABLE produits ADD COLUMN taux_prise_en_charge_cnamgs "
                    "NUMERIC(5, 2) NOT NULL DEFAULT 0"
                )
            )
    tables = inspector.get_table_names()
    if "organismes_prise_en_charge" in tables:
        colonnes_organismes = {
            c["name"] for c in inspect(engine).get_columns("organismes_prise_en_charge")
        }
        if "taux_prise_en_charge" not in colonnes_organismes:
            with engine.begin() as connexion:
                connexion.execute(
                    text(
                        "ALTER TABLE organismes_prise_en_charge ADD COLUMN "
                        "taux_prise_en_charge NUMERIC(5, 2) NOT NULL DEFAULT 0"
                    )
                )
    inspector = inspect(engine)
    if "postes_vente" in inspector.get_table_names():
        cols = {c["name"] for c in inspector.get_columns("postes_vente")}
        if "caisse_id" not in cols:
            with engine.begin() as connexion:
                connexion.execute(text("ALTER TABLE postes_vente ADD COLUMN caisse_id VARCHAR(36)"))
    if "ventes" in inspector.get_table_names():
        cols = {c["name"] for c in inspector.get_columns("ventes")}
        additions = {
            "organisme_id": "VARCHAR(36)",
            "patient_nom": "VARCHAR(150) NOT NULL DEFAULT ''",
            "patient_prenom": "VARCHAR(150) NOT NULL DEFAULT ''",
            "informations_prise_en_charge": "JSON NOT NULL DEFAULT '{}'",
            "encaissement_id": "VARCHAR(36)",
            "reglements": "JSON NOT NULL DEFAULT '[]'",
            "carte_fidelite_id": "VARCHAR(36)",
            "points_utilises": "INTEGER NOT NULL DEFAULT 0",
            "encaissee_le": "DATETIME",
        }
        with engine.begin() as connexion:
            for name, sqltype in additions.items():
                if name not in cols:
                    connexion.execute(text(f"ALTER TABLE ventes ADD COLUMN {name} {sqltype}"))
    inspector = inspect(engine)
    if "allocations_lots" in inspector.get_table_names():
        cols = {c["name"] for c in inspector.get_columns("allocations_lots")}
        if "emplacement_id" not in cols:
            with engine.begin() as connexion:
                connexion.execute(
                    text("ALTER TABLE allocations_lots ADD COLUMN emplacement_id VARCHAR(36)")
                )


def create_container() -> ApplicationContainer:
    engine = create_database_engine()
    Base.metadata.create_all(engine)
    _mettre_a_niveau_schema_legacy(engine)
    factory = create_session_factory(engine)
    catalogue_repository = SqlAlchemyCatalogueRepository(factory)
    stock_repository = SqlAlchemyStockRepository(factory)
    vente_repository = SqlAlchemyVenteRepository(factory)
    fidelite_repository = SqlAlchemyFideliteRepository(factory)
    administration_repository = SqlAlchemyAdministrationRepository(factory)
    inventaire = Inventaire()
    for emplacement in stock_repository.lister_emplacements():
        inventaire.ajouter_emplacement(emplacement)
    for lot in stock_repository.lister_lots():
        inventaire.ajouter_lot(lot)
    for position in stock_repository.lister_toutes_positions():
        inventaire.charger_position(position)
    catalogue_service = CatalogueService(catalogue_repository)
    catalogue_service.initialiser_principes_actifs()
    catalogue_service.initialiser_marques()
    stock_service = StockService(
        stock_repository,
        inventaire,
        catalogue=catalogue_repository,
    )
    achats_service = AchatService(catalogue_repository, catalogue_service, stock_service)
    fidelite_service = FideliteService(fidelite_repository)
    return ApplicationContainer(
        catalogue=catalogue_service,
        stock=stock_service,
        ventes=VenteService(
            vente_repository,
            catalogue_repository,
            stock_service,
            fidelite_service,
        ),
        achats=achats_service,
        fidelite=fidelite_service,
        administration=AdministrationService(administration_repository),
    )
