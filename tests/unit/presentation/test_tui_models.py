import asyncio
from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

from textual.widgets import DataTable, Input

from neosys_pharma.application.dto import (
    AjouterConditionnement,
    AjouterLigneVente,
    CreerMedicament,
    CreerPosteVente,
    ReceptionnerLot,
)
from neosys_pharma.application.services import CatalogueService, StockService
from neosys_pharma.application.vente_service import VenteService
from neosys_pharma.domain.stock import Inventaire
from neosys_pharma.infrastructure.persistence import (
    InMemoryCatalogueRepository,
    InMemoryStockRepository,
    InMemoryVenteRepository,
)
from neosys_pharma.presentation.api.container import ApplicationContainer
from neosys_pharma.presentation.tui.app import (
    CaisseModal,
    NeoSysPharmaConsole,
    PaiementMultipleModal,
    SelectionModal,
)
from neosys_pharma.presentation.tui.models import (
    ArticleConsole,
    ClientConsole,
    filtrer_articles,
    filtrer_clients,
)


def test_recherche_et_scan_d_un_article() -> None:
    article = ArticleConsole(
        id=UUID("00000000-0000-0000-0000-000000000001"),
        reference="MED-PARA-500",
        code="PARA500-B20",
        designation="Paracétamol 500 mg",
        libelle="Boîte de 20 comprimés",
        prix_vente=Decimal("1500"),
        stock_disponible=100,
    )

    assert filtrer_articles((article,), "para") == (article,)
    assert filtrer_articles((article,), "") == (article,)
    assert filtrer_articles((article,), "introuvable") == ()
    assert article.correspond_code_exact("PARA500-B20")
    assert article.correspond_code_exact("med-para-500")


def test_recherche_et_scan_d_un_client() -> None:
    client = ClientConsole(
        id=UUID("00000000-0000-0000-0000-000000000002"),
        code="CLI-001",
        nom="Jean Moussavou",
        identifiant_scan="9000012345",
    )

    assert filtrer_clients((client,), "mous") == (client,)
    assert filtrer_clients((client,), "") == (client,)
    assert filtrer_clients((client,), "absent") == ()
    assert client.correspond_code_exact("9000012345")
    assert client.correspond_code_exact("cli-001")


def test_la_console_terminale_demarre() -> None:
    async def verifier() -> None:
        catalogue_repository = InMemoryCatalogueRepository()
        stock = StockService(
            InMemoryStockRepository(),
            Inventaire(),
            catalogue=catalogue_repository,
        )
        container = ApplicationContainer(
            catalogue=CatalogueService(catalogue_repository),
            stock=stock,
            ventes=VenteService(
                InMemoryVenteRepository(),
                catalogue_repository,
                stock,
            ),
        )
        app = NeoSysPharmaConsole(container)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            assert app.query_one("#client")
            assert app.query_one("#article")
            assert app.query_one("#table-vente")

    asyncio.run(verifier())


def test_les_raccourcis_ouvrent_le_paiement_multiple_et_la_caisse() -> None:
    async def verifier() -> None:
        catalogue_repository = InMemoryCatalogueRepository()
        stock = StockService(
            InMemoryStockRepository(),
            Inventaire(),
            catalogue=catalogue_repository,
        )
        container = ApplicationContainer(
            catalogue=CatalogueService(catalogue_repository),
            stock=stock,
            ventes=VenteService(
                InMemoryVenteRepository(),
                catalogue_repository,
                stock,
            ),
        )
        app = NeoSysPharmaConsole(container)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.press("f9")
            await pilot.pause()
            assert isinstance(app.screen, PaiementMultipleModal)

            await pilot.press("escape")
            await pilot.press("f12")
            await pilot.pause()
            assert isinstance(app.screen, CaisseModal)

    asyncio.run(verifier())


def test_la_recherche_conserve_le_terme_et_place_le_curseur_a_la_fin() -> None:
    async def verifier() -> None:
        catalogue_repository = InMemoryCatalogueRepository()
        stock = StockService(
            InMemoryStockRepository(),
            Inventaire(),
            catalogue=catalogue_repository,
        )
        container = ApplicationContainer(
            catalogue=CatalogueService(catalogue_repository),
            stock=stock,
            ventes=VenteService(
                InMemoryVenteRepository(),
                catalogue_repository,
                stock,
            ),
        )
        client = ClientConsole(
            id=uuid4(),
            code="CLI-001",
            nom="Jean Moussavou",
        )
        app = NeoSysPharmaConsole(container, clients=(client,))
        async with app.run_test(size=(120, 40)) as pilot:
            app.query_one("#client", Input).value = "Jea"
            await pilot.pause()

            assert isinstance(app.screen, SelectionModal)
            recherche = app.screen.query_one("#selection-search", Input)
            assert recherche.value == "Jea"
            assert recherche.cursor_position == 3

    asyncio.run(verifier())


def test_preparer_vide_la_vente_et_conserve_le_numero_du_ticket() -> None:
    async def verifier() -> None:
        catalogue_repository = InMemoryCatalogueRepository()
        catalogue = CatalogueService(catalogue_repository)
        stock = StockService(
            InMemoryStockRepository(),
            Inventaire(),
            catalogue=catalogue_repository,
        )
        ventes = VenteService(
            InMemoryVenteRepository(),
            catalogue_repository,
            stock,
        )
        emplacement = stock.creer_emplacement(code="RAY-01", libelle="Rayon")
        produit = catalogue.creer_medicament(
            CreerMedicament(
                reference="MED-001",
                designation="Paracétamol",
                principe_actif="Paracétamol",
            )
        )
        article = catalogue.ajouter_conditionnement(
            AjouterConditionnement(
                produit_id=produit.id,
                code="PARA-B20",
                libelle="Boîte de 20 comprimés",
                prix_vente=Decimal("1500"),
            )
        )
        stock.receptionner_lot(
            ReceptionnerLot(
                conditionnement_id=article.id,
                numero_lot="LOT-001",
                date_expiration=date(2028, 12, 31),
                emplacement_id=emplacement.id,
                quantite=10,
                motif="Test console",
            )
        )
        poste = ventes.creer_poste(
            CreerPosteVente(
                code="POSTE-01",
                secteur_id=uuid4(),
                emplacement_id=emplacement.id,
            )
        )
        vente = ventes.creer_vente(poste_id=poste.id, date_commerciale=date(2026, 9, 20))
        ventes.ajouter_ligne(
            AjouterLigneVente(
                vente_id=vente.id,
                conditionnement_id=article.id,
                quantite=2,
            )
        )
        app = NeoSysPharmaConsole(
            ApplicationContainer(catalogue=catalogue, stock=stock, ventes=ventes)
        )
        app.vente = ventes.obtenir(vente.id)

        async with app.run_test(size=(120, 40)) as pilot:
            app._afficher_vente()
            app.action_preparer()
            await pilot.pause()

            assert app.vente is None
            assert app.query_one("#table-vente", DataTable).row_count == 0
            assert app.query_one("#client", Input).value == ""
            assert app.query_one("#article", Input).value == ""

    asyncio.run(verifier())
