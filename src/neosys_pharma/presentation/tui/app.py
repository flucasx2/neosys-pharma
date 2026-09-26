from __future__ import annotations

from collections.abc import Callable
from datetime import date
from decimal import Decimal
from typing import Generic, TypeVar
from uuid import UUID

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Input, Label, Select, Static

from neosys_pharma.application.dto import AjouterLigneVente
from neosys_pharma.domain.shared import DomainError
from neosys_pharma.domain.vente import Vente
from neosys_pharma.presentation.api.container import ApplicationContainer, create_container
from neosys_pharma.presentation.tui.models import (
    ArticleConsole,
    ClientConsole,
    filtrer_articles,
    filtrer_clients,
)

T = TypeVar("T", ArticleConsole, ClientConsole)


class SelectionModal(ModalScreen[T | None], Generic[T]):
    BINDINGS = [Binding("escape", "fermer", "Fermer")]

    def __init__(
        self,
        *,
        titre: str,
        terme: str,
        elements: tuple[T, ...],
        filtrer: Callable[[tuple[T, ...], str], tuple[T, ...]],
        colonnes: tuple[str, ...],
        cellules: Callable[[T], tuple[str, ...]],
    ) -> None:
        super().__init__()
        self._titre = titre
        self._terme = terme
        self._elements: tuple[T, ...] = elements
        self._filtrer: Callable[[tuple[T, ...], str], tuple[T, ...]] = filtrer
        self._colonnes = colonnes
        self._cellules: Callable[[T], tuple[str, ...]] = cellules
        self._resultats: tuple[T, ...] = ()

    def compose(self) -> ComposeResult:
        with Vertical(id="selection-dialog"):
            yield Label(self._titre, id="selection-title")
            yield Input(value=self._terme, id="selection-search")
            yield DataTable(id="selection-table", cursor_type="row")
            yield Static("HAUT/BAS : naviguer | ENTREE : selectionner | ECHAP : fermer")

    def on_mount(self) -> None:
        table = self.query_one("#selection-table", DataTable)
        table.add_columns(*self._colonnes)
        self._actualiser(self._terme)
        recherche = self.query_one("#selection-search", Input)
        recherche.cursor_position = len(recherche.value)
        recherche.focus()

    def _actualiser(self, terme: str) -> None:
        self._resultats = self._filtrer(self._elements, terme)
        table = self.query_one("#selection-table", DataTable)
        table.clear()
        for element in self._resultats:
            table.add_row(*self._cellules(element))

    @on(Input.Changed, "#selection-search")
    def recherche_modifiee(self, event: Input.Changed) -> None:
        self._actualiser(event.value)

    @on(Input.Submitted, "#selection-search")
    def recherche_validee(self, event: Input.Submitted) -> None:
        exact = next(
            (element for element in self._elements if element.correspond_code_exact(event.value)),
            None,
        )
        if exact is not None:
            self.dismiss(exact)
        elif len(self._resultats) == 1:
            self.dismiss(self._resultats[0])

    @on(DataTable.RowSelected, "#selection-table")
    def ligne_selectionnee(self, event: DataTable.RowSelected) -> None:
        index = event.cursor_row
        if 0 <= index < len(self._resultats):
            self.dismiss(self._resultats[index])

    def action_fermer(self) -> None:
        self.dismiss(None)


class PaiementMultipleModal(ModalScreen[None]):
    """Point d'entrée clavier de l'encaissement de plusieurs tickets."""

    BINDINGS = [
        Binding("f1", "valider", "Valider"),
        Binding("f2", "fermer", "Annuler"),
        Binding("escape", "fermer", "Annuler"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(classes="operation-dialog"):
            yield Static("PAIEMENT MULTIPLE", classes="operation-title")
            yield Static("Scanner ou saisir successivement les tickets à encaisser.")
            yield Input(placeholder="Code-barres ou numéro du ticket", id="ticket-multiple")
            yield DataTable(id="tickets-multiples", cursor_type="row")
            yield Static("TOTAL A PAYER : 0 FCFA", classes="operation-total")
            yield Static("F1 Valider  |  F2 Annuler  |  ECHAP Retour", classes="function-line")

    def on_mount(self) -> None:
        self.query_one("#tickets-multiples", DataTable).add_columns("Ticket", "Vendeur", "Montant")
        self.query_one("#ticket-multiple", Input).focus()

    def action_valider(self) -> None:
        self.notify("L'encaissement sera activé avec le lot métier Caisse.")

    def action_fermer(self) -> None:
        self.dismiss(None)


class CaisseModal(ModalScreen[None]):
    """Accès monochrome aux opérations de clôture et fermeture de caisse."""

    BINDINGS = [
        Binding("f12", "valider", "Valider"),
        Binding("escape", "fermer", "Retour"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(classes="operation-dialog"):
            yield Static("CAISSE", classes="operation-title")
            yield Static("POSTE : -                         ETAT : OUVERTE")
            yield Static("TOTAL ESPECES : 0 FCFA")
            yield Static("TOTAL AUTRES MODES : 0 FCFA")
            yield Static("ECART : 0 FCFA")
            yield Static(
                "Clôture / fermeture : les montants seront calculés par le lot métier Caisse.",
                id="caisse-information",
            )
            yield Static("F12 Valider  |  ECHAP Retour", classes="function-line")

    def action_valider(self) -> None:
        self.notify("La clôture sera activée avec le lot métier Caisse.")

    def action_fermer(self) -> None:
        self.dismiss(None)


class NeoSysPharmaConsole(App[None]):
    TITLE = "NeoSys Pharma - Console de vente"
    CSS = """
    Screen { background: black; color: white; overflow-y: hidden; }
    #titre { height: 1; background: black; color: white;
             text-style: bold; text-align: center; }
    #raccourcis-haut { height: 1; color: white; }
    #formulaire { height: 6; padding: 0 1; border: ascii white; }
    .champ { width: 1fr; margin-right: 1; }
    Input, Select { border: ascii white; background: black; color: white; }
    Input:focus, Select:focus { border: ascii white; background: white; color: black; }
    SelectCurrent { background: black; color: white; }
    SelectCurrent:focus { background: white; color: black; }
    #saisie-article { height: 4; border: ascii white; padding: 0 1; }
    #article { width: 1fr; }
    #quantite { width: 12; }
    #ajouter { width: 16; }
    #table-vente { height: 1fr; border: ascii white; background: black; color: white; }
    DataTable > .datatable--header { background: white; color: black; text-style: bold; }
    DataTable > .datatable--cursor { background: white; color: black; }
    DataTable > .datatable--even-row { background: black; color: white; }
    #resume { height: 4; padding: 0 2; border: ascii white; }
    #total { text-align: right; text-style: bold; color: white; }
    #message { height: 2; padding: 0 2; color: white; }
    #fonctions { height: 2; padding: 0 1; border-top: ascii white; color: white; }
    Button { margin-left: 1; background: black; color: white; border: ascii white; }
    Button:focus { background: white; color: black; text-style: bold; }
    #selection-dialog { width: 86%; height: 76%; padding: 1 2; border: ascii white;
                        background: black; color: white; }
    #selection-title { text-style: bold; color: white; margin-bottom: 1; }
    #selection-table { height: 1fr; margin: 1 0; }
    .operation-dialog { width: 82%; height: 72%; padding: 1 2; border: ascii white;
                        background: black; color: white; }
    .operation-title { text-align: center; text-style: bold; margin-bottom: 1;
                       background: white; color: black; }
    .operation-total { text-align: right; text-style: bold; margin-top: 1; }
    .function-line { dock: bottom; height: 1; color: white; }
    #tickets-multiples { height: 1fr; margin: 1 0; }
    #caisse-information { margin-top: 2; }
    """
    BINDINGS = [
        Binding("f2", "nouvelle_vente", "Nouvelle vente"),
        Binding("f5", "controler", "Contrôle"),
        Binding("f8", "preparer", "Préparer"),
        Binding("f9", "paiement_multiple", "Paiement multiple"),
        Binding("f12", "caisse", "Caisse"),
        Binding("escape", "annuler", "Annuler"),
        Binding("ctrl+q", "quit", "Quitter"),
    ]

    def __init__(
        self,
        container: ApplicationContainer | None = None,
        clients: tuple[ClientConsole, ...] = (),
    ) -> None:
        super().__init__()
        self.container = container or create_container()
        self.clients = clients
        self.articles: tuple[ArticleConsole, ...] = ()
        self.client_selectionne: ClientConsole | None = None
        self.article_selectionne: ArticleConsole | None = None
        self.vente: Vente | None = None
        self._popup_client_ouvert = False
        self._popup_article_ouvert = False
        self._suspendre_recherche_automatique = False

    def compose(self) -> ComposeResult:
        yield Static("NEOSYS PHARMA - CONSOLE DE VENTE", id="titre")
        yield Static(
            "F2 Nouvelle vente | F5 Contrôle | F8 Préparer | F9 Paiement multiple | F12 Caisse",
            id="raccourcis-haut",
        )
        with Horizontal(id="formulaire"):
            with Vertical(classes="champ"):
                yield Label("CLIENT / CARTE")
                yield Input(placeholder="Nom, code ou scan", id="client")
            with Vertical(classes="champ"):
                yield Label("POSTE DE VENTE")
                yield Select([], id="poste", prompt="Choisir un poste")
            with Vertical(classes="champ"):
                yield Label("TYPE DE VENTE")
                yield Select(
                    [("Espèces", "especes"), ("Compte", "compte")],
                    value="especes",
                    id="type-vente",
                )
        with Horizontal(id="saisie-article"):
            yield Input(placeholder="Produit : saisir 3 caractères ou scanner", id="article")
            yield Input(value="1", type="integer", id="quantite")
            yield Button("AJOUTER", id="ajouter")
        yield DataTable(id="table-vente", cursor_type="row", zebra_stripes=True)
        with Vertical(id="resume"):
            yield Static("Aucune vente ouverte", id="etat-vente")
            yield Static("TOTAL : 0 FCFA", id="total")
        yield Static("Prêt. Saisir trois caractères ou scanner un code.", id="message")
        yield Static(
            "ECHAP Annuler/Retour | TAB Champ suivant | CTRL+Q Quitter",
            id="fonctions",
        )

    def on_mount(self) -> None:
        table = self.query_one("#table-vente", DataTable)
        table.add_columns("Désignation", "Qté", "Prix", "Total")
        postes = self.container.ventes.lister_postes()
        select = self.query_one("#poste", Select)
        select.set_options([(poste.code, str(poste.id)) for poste in postes])
        if postes:
            select.value = str(postes[0].id)
        self._charger_articles()
        self.query_one("#client", Input).focus()

    def _charger_articles(self) -> None:
        poste_id = self.query_one("#poste", Select).value
        postes = {str(poste.id): poste for poste in self.container.ventes.lister_postes()}
        poste = postes.get(str(poste_id))
        articles: list[ArticleConsole] = []
        for produit in self.container.catalogue.lister_produits():
            for item in produit.conditionnements:
                stock = 0
                if poste is not None:
                    stock = sum(
                        ligne.quantite_disponible
                        for ligne in self.container.stock.consulter_stock(
                            conditionnement_id=item.id,
                            emplacement_id=poste.emplacement_id,
                        )
                    )
                articles.append(
                    ArticleConsole(
                        id=item.id,
                        reference=produit.reference,
                        code=item.code,
                        designation=produit.designation,
                        libelle=item.libelle,
                        prix_vente=item.prix_vente,
                        stock_disponible=stock,
                    )
                )
        self.articles = tuple(articles)

    @on(Select.Changed, "#poste")
    def poste_modifie(self, _event: Select.Changed) -> None:
        self._charger_articles()

    @on(Input.Changed, "#client")
    def client_modifie(self, event: Input.Changed) -> None:
        if (
            len(event.value.strip()) >= 3
            and not self._popup_client_ouvert
            and not self._suspendre_recherche_automatique
        ):
            self._ouvrir_clients(event.value)

    @on(Input.Submitted, "#client")
    def client_valide(self, event: Input.Submitted) -> None:
        exact = next(
            (client for client in self.clients if client.correspond_code_exact(event.value)),
            None,
        )
        if exact is not None:
            self._client_choisi(exact)
        elif event.value.strip():
            self.query_one("#article", Input).focus()

    def _ouvrir_clients(self, terme: str) -> None:
        self._popup_client_ouvert = True
        self.push_screen(
            SelectionModal(
                titre="Sélection du client",
                terme=terme,
                elements=self.clients,
                filtrer=filtrer_clients,
                colonnes=("Code", "Client"),
                cellules=lambda client: (client.code, client.nom),
            ),
            self._client_choisi,
        )

    def _client_choisi(self, client: ClientConsole | None) -> None:
        self._popup_client_ouvert = False
        if client is not None:
            self.client_selectionne = client
            self._suspendre_recherche_automatique = True
            self.query_one("#client", Input).value = f"{client.code} — {client.nom}"
            self.call_after_refresh(self._reactiver_recherche_automatique)
        self.query_one("#article", Input).focus()

    @on(Input.Changed, "#article")
    def article_modifie(self, event: Input.Changed) -> None:
        if (
            len(event.value.strip()) >= 3
            and not self._popup_article_ouvert
            and not self._suspendre_recherche_automatique
        ):
            self._ouvrir_articles(event.value)

    @on(Input.Submitted, "#article")
    def article_valide(self, event: Input.Submitted) -> None:
        exact = next(
            (article for article in self.articles if article.correspond_code_exact(event.value)),
            None,
        )
        if exact is not None:
            self._article_choisi(exact)
        else:
            self._ouvrir_articles(event.value)

    def _ouvrir_articles(self, terme: str) -> None:
        if self._popup_article_ouvert:
            return
        self._popup_article_ouvert = True
        self.push_screen(
            SelectionModal(
                titre="Sélection du produit",
                terme=terme,
                elements=self.articles,
                filtrer=filtrer_articles,
                colonnes=("Référence", "Désignation", "Conditionnement", "Prix", "Stock"),
                cellules=lambda article: (
                    article.reference,
                    article.designation,
                    article.libelle,
                    self._monnaie(article.prix_vente),
                    str(article.stock_disponible),
                ),
            ),
            self._article_choisi,
        )

    def _article_choisi(self, article: ArticleConsole | None) -> None:
        self._popup_article_ouvert = False
        if article is not None:
            self.article_selectionne = article
            self._suspendre_recherche_automatique = True
            self.query_one(
                "#article", Input
            ).value = f"{article.code} — {article.designation} / {article.libelle}"
            self.call_after_refresh(self._reactiver_recherche_automatique)
            self.query_one("#quantite", Input).focus()

    def _reactiver_recherche_automatique(self) -> None:
        self._suspendre_recherche_automatique = False

    @on(Button.Pressed, "#nouvelle")
    def bouton_nouvelle_vente(self) -> None:
        self.action_nouvelle_vente()

    def action_nouvelle_vente(self) -> None:
        poste_id = self.query_one("#poste", Select).value
        if poste_id is Select.BLANK:
            self._message("Aucun poste de vente sélectionné.")
            return
        try:
            self.vente = self.container.ventes.creer_vente(
                poste_id=UUID(str(poste_id)), date_commerciale=date.today()
            )
            self._afficher_vente()
            self.query_one("#client", Input).focus()
            self._message("Nouvelle vente créée.")
        except (DomainError, ValueError) as exception:
            self._message(str(exception))

    @on(Button.Pressed, "#ajouter")
    def ajouter_article(self) -> None:
        if self.vente is None:
            self.action_nouvelle_vente()
        if self.vente is None or self.article_selectionne is None:
            self._message("Sélectionnez un produit avant de l'ajouter.")
            return
        try:
            quantite = int(self.query_one("#quantite", Input).value)
            self.container.ventes.ajouter_ligne(
                AjouterLigneVente(
                    vente_id=self.vente.id,
                    conditionnement_id=self.article_selectionne.id,
                    quantite=quantite,
                )
            )
            self.vente = self.container.ventes.obtenir(self.vente.id)
            self._afficher_vente()
            self.article_selectionne = None
            self.query_one("#article", Input).value = ""
            self.query_one("#quantite", Input).value = "1"
            self.query_one("#article", Input).focus()
        except (DomainError, ValueError) as exception:
            self._message(str(exception))

    @on(Button.Pressed, "#preparer")
    def bouton_preparer(self) -> None:
        self.action_preparer()

    def action_preparer(self) -> None:
        if self.vente is None:
            self._message("Aucune vente à préparer.")
            return
        try:
            vente_preparee = self.container.ventes.preparer(self.vente.id)
            numero_ticket = vente_preparee.numero_ticket
            self._charger_articles()
            self._vider_vente_preparee(numero_ticket)
        except DomainError as exception:
            self._message(str(exception))

    def _vider_vente_preparee(self, numero_ticket: str) -> None:
        self.vente = None
        self.client_selectionne = None
        self.article_selectionne = None
        self.query_one("#table-vente", DataTable).clear()
        self._suspendre_recherche_automatique = True
        self.query_one("#client", Input).value = ""
        self.query_one("#article", Input).value = ""
        self.query_one("#quantite", Input).value = "1"
        self.call_after_refresh(self._reactiver_recherche_automatique)
        self.query_one("#etat-vente", Static).update(
            f"Ticket {numero_ticket} préparé — en attente de paiement"
        )
        self.query_one("#total", Static).update("TOTAL : 0 FCFA")
        self._message(
            f"Préparation validée. Ticket {numero_ticket}. Écran prêt pour la vente suivante."
        )
        self.query_one("#client", Input).focus()

    def action_controler(self) -> None:
        self._message("Contrôle : fonctionnalité prévue dans le prochain lot métier.")

    def action_paiement_multiple(self) -> None:
        self.push_screen(PaiementMultipleModal())

    def action_caisse(self) -> None:
        self.push_screen(CaisseModal())

    @on(Button.Pressed, "#annuler")
    def bouton_annuler(self) -> None:
        self.action_annuler()

    def action_annuler(self) -> None:
        if self.vente is None:
            self._message("Aucune vente à annuler.")
            return
        try:
            self.vente = self.container.ventes.annuler(self.vente.id)
            self._afficher_vente()
            self._charger_articles()
            self._message("Vente annulée et réservations libérées.")
        except DomainError as exception:
            self._message(str(exception))

    def _afficher_vente(self) -> None:
        if self.vente is None:
            return
        table = self.query_one("#table-vente", DataTable)
        table.clear()
        for ligne in self.vente.lignes:
            table.add_row(
                ligne.designation,
                str(ligne.quantite),
                self._monnaie(ligne.prix_unitaire),
                self._monnaie(ligne.montant),
            )
        self.query_one("#etat-vente", Static).update(
            f"Vente {str(self.vente.id)[:8].upper()}  •  {self.vente.etat.value}"
        )
        self.query_one("#total", Static).update(
            f"TOTAL : {self._monnaie(self.vente.montant_total)}"
        )

    def _message(self, contenu: str) -> None:
        self.query_one("#message", Static).update(contenu)

    @staticmethod
    def _monnaie(montant: Decimal) -> str:
        return f"{montant:,.0f} FCFA".replace(",", " ")


def main() -> None:
    NeoSysPharmaConsole().run()


if __name__ == "__main__":
    main()
