from __future__ import annotations

from uuid import UUID

from neosys_pharma.domain.administration import Caisse, CompteOperation
from neosys_pharma.domain.catalogue import (
    CarteFidelite,
    ClientFidelite,
    CommandeAchat,
    Fournisseur,
    Marque,
    MouvementFidelite,
    OrganismePriseEnCharge,
    PrincipeActif,
    Produit,
    ProduitConditionnement,
    TarifFournisseur,
)
from neosys_pharma.domain.stock import Emplacement, Lot, MouvementStock, StockEmplacement
from neosys_pharma.domain.vente import PosteVente, Vente


class InMemoryAdministrationRepository:
    def __init__(self) -> None:
        self.items: dict[UUID, CompteOperation] = {}
        self.caisses: dict[UUID, Caisse] = {}

    def enregistrer_caisse(self, item: Caisse) -> None:
        self.caisses[item.id] = item

    def lister_caisses(self) -> tuple[Caisse, ...]:
        return tuple(self.caisses.values())

    def enregistrer_compte(self, item: CompteOperation) -> None:
        self.items[item.id] = item

    def obtenir_compte(self, item_id: UUID) -> CompteOperation | None:
        return self.items.get(item_id)

    def lister_comptes(self) -> tuple[CompteOperation, ...]:
        return tuple(self.items.values())


class InMemoryFideliteRepository:
    def __init__(self) -> None:
        self.clients: dict[UUID, ClientFidelite] = {}
        self.cartes: dict[UUID, CarteFidelite] = {}
        self.mouvements: list[MouvementFidelite] = []

    def enregistrer_client_fidelite(self, item: ClientFidelite) -> None:
        self.clients[item.id] = item

    def obtenir_client_fidelite(self, item_id: UUID) -> ClientFidelite | None:
        return self.clients.get(item_id)

    def lister_clients_fidelite(self) -> tuple[ClientFidelite, ...]:
        return tuple(self.clients.values())

    def enregistrer_carte_fidelite(self, item: CarteFidelite) -> None:
        self.cartes[item.id] = item

    def obtenir_carte_fidelite(self, item_id: UUID) -> CarteFidelite | None:
        return self.cartes.get(item_id)

    def lister_cartes_fidelite(self) -> tuple[CarteFidelite, ...]:
        return tuple(self.cartes.values())

    def enregistrer_mouvement_fidelite(self, item: MouvementFidelite) -> None:
        self.mouvements.append(item)

    def lister_mouvements_fidelite(self, carte_id: UUID) -> tuple[MouvementFidelite, ...]:
        return tuple(i for i in reversed(self.mouvements) if i.carte_id == carte_id)


class InMemoryCatalogueRepository:
    def __init__(self) -> None:
        self._produits: dict[UUID, Produit] = {}
        self._principes_actifs: dict[UUID, PrincipeActif] = {}
        self._marques: dict[UUID, Marque] = {}
        self._fournisseurs: dict[UUID, Fournisseur] = {}
        self._tarifs: dict[tuple[UUID, UUID], TarifFournisseur] = {}
        self._commandes_achat: dict[UUID, CommandeAchat] = {}
        self._organismes: dict[UUID, OrganismePriseEnCharge] = {}

    def enregistrer_produit(self, produit: Produit) -> None:
        self._produits[produit.id] = produit

    def obtenir_produit(self, produit_id: UUID) -> Produit | None:
        return self._produits.get(produit_id)

    def obtenir_produit_par_reference(self, reference: str) -> Produit | None:
        reference_normalisee = reference.strip()
        return next(
            (
                produit
                for produit in self._produits.values()
                if produit.reference == reference_normalisee
            ),
            None,
        )

    def obtenir_produit_par_cip7(self, cip7: str) -> Produit | None:
        valeur = cip7.strip()
        return next(
            (produit for produit in self._produits.values() if produit.cip7 == valeur),
            None,
        )

    def obtenir_conditionnement(self, conditionnement_id: UUID) -> ProduitConditionnement | None:
        return next(
            (
                conditionnement
                for produit in self._produits.values()
                for conditionnement in produit.conditionnements
                if conditionnement.id == conditionnement_id
            ),
            None,
        )

    def lister_produits(self) -> tuple[Produit, ...]:
        return tuple(self._produits.values())

    def reinitialiser_catalogue(self) -> int:
        nombre = len(self._produits)
        self._produits.clear()
        self._tarifs.clear()
        self._commandes_achat.clear()
        return nombre

    def enregistrer_principe_actif(self, principe: PrincipeActif) -> None:
        self._principes_actifs[principe.id] = principe

    def obtenir_principe_actif(self, principe_id: UUID) -> PrincipeActif | None:
        return self._principes_actifs.get(principe_id)

    def obtenir_principe_actif_par_libelle(self, libelle: str) -> PrincipeActif | None:
        libelle_normalise = libelle.strip().casefold()
        return next(
            (
                principe
                for principe in self._principes_actifs.values()
                if principe.libelle.casefold() == libelle_normalise
            ),
            None,
        )

    def lister_principes_actifs(self) -> tuple[PrincipeActif, ...]:
        return tuple(sorted(self._principes_actifs.values(), key=lambda item: item.libelle))

    def enregistrer_marque(self, marque: Marque) -> None:
        self._marques[marque.id] = marque

    def obtenir_marque(self, marque_id: UUID) -> Marque | None:
        return self._marques.get(marque_id)

    def obtenir_marque_par_libelle(self, libelle: str) -> Marque | None:
        valeur = libelle.strip().casefold()
        return next(
            (marque for marque in self._marques.values() if marque.libelle.casefold() == valeur),
            None,
        )

    def lister_marques(self) -> tuple[Marque, ...]:
        return tuple(sorted(self._marques.values(), key=lambda item: item.libelle))

    def enregistrer_fournisseur(self, fournisseur: Fournisseur) -> None:
        self._fournisseurs[fournisseur.id] = fournisseur

    def obtenir_fournisseur(self, fournisseur_id: UUID) -> Fournisseur | None:
        return self._fournisseurs.get(fournisseur_id)

    def obtenir_fournisseur_par_code(self, code: str) -> Fournisseur | None:
        code_normalise = code.strip().casefold()
        return next(
            (
                fournisseur
                for fournisseur in self._fournisseurs.values()
                if fournisseur.code.casefold() == code_normalise
            ),
            None,
        )

    def lister_fournisseurs(self) -> tuple[Fournisseur, ...]:
        return tuple(self._fournisseurs.values())

    def enregistrer_tarif_fournisseur(self, tarif: TarifFournisseur) -> None:
        self._tarifs[(tarif.fournisseur_id, tarif.conditionnement_id)] = tarif

    def obtenir_tarif_fournisseur(
        self, *, fournisseur_id: UUID, conditionnement_id: UUID
    ) -> TarifFournisseur | None:
        return self._tarifs.get((fournisseur_id, conditionnement_id))

    def lister_tarifs_fournisseurs(self) -> tuple[TarifFournisseur, ...]:
        return tuple(self._tarifs.values())

    def enregistrer_commande_achat(self, commande: CommandeAchat) -> None:
        self._commandes_achat[commande.id] = commande

    def lister_commandes_achat(self) -> tuple[CommandeAchat, ...]:
        return tuple(self._commandes_achat.values())

    def enregistrer_organisme(self, organisme: OrganismePriseEnCharge) -> None:
        self._organismes[organisme.id] = organisme

    def obtenir_organisme_par_code(self, code: str) -> OrganismePriseEnCharge | None:
        valeur = code.strip().casefold()
        return next(
            (item for item in self._organismes.values() if item.code.casefold() == valeur), None
        )

    def obtenir_organisme(self, organisme_id: UUID) -> OrganismePriseEnCharge | None:
        return self._organismes.get(organisme_id)

    def lister_organismes(self) -> tuple[OrganismePriseEnCharge, ...]:
        return tuple(sorted(self._organismes.values(), key=lambda item: item.nom))


class InMemoryStockRepository:
    def __init__(self) -> None:
        self._lots: dict[UUID, Lot] = {}
        self._emplacements: dict[UUID, Emplacement] = {}
        self._positions: dict[tuple[UUID, UUID], StockEmplacement] = {}
        self._mouvements: list[MouvementStock] = []

    def enregistrer_lot(self, lot: Lot) -> None:
        self._lots[lot.id] = lot

    def obtenir_lot(self, lot_id: UUID) -> Lot | None:
        return self._lots.get(lot_id)

    def enregistrer_emplacement(self, emplacement: Emplacement) -> None:
        self._emplacements[emplacement.id] = emplacement

    def obtenir_emplacement(self, emplacement_id: UUID) -> Emplacement | None:
        return self._emplacements.get(emplacement_id)

    def enregistrer_position(self, position: StockEmplacement) -> None:
        self._positions[(position.lot_id, position.emplacement_id)] = position

    def obtenir_position(self, *, lot_id: UUID, emplacement_id: UUID) -> StockEmplacement | None:
        return self._positions.get((lot_id, emplacement_id))

    def enregistrer_mouvement(self, mouvement: MouvementStock) -> None:
        self._mouvements.append(mouvement)

    def lister_mouvements(self) -> tuple[MouvementStock, ...]:
        return tuple(self._mouvements)

    def lister_lots(self) -> tuple[Lot, ...]:
        return tuple(self._lots.values())

    def lister_emplacements(self) -> tuple[Emplacement, ...]:
        return tuple(self._emplacements.values())

    def lister_toutes_positions(self) -> tuple[StockEmplacement, ...]:
        return tuple(self._positions.values())

    def lister_positions(
        self, *, conditionnement_id: UUID, emplacement_id: UUID
    ) -> tuple[StockEmplacement, ...]:
        lot_ids = {
            lot.id for lot in self._lots.values() if lot.conditionnement_id == conditionnement_id
        }
        return tuple(
            position
            for (lot_id, position_emplacement_id), position in self._positions.items()
            if lot_id in lot_ids and position_emplacement_id == emplacement_id
        )


class InMemoryVenteRepository:
    def __init__(self) -> None:
        self._postes: dict[UUID, PosteVente] = {}
        self._ventes: dict[UUID, Vente] = {}

    def enregistrer_poste(self, poste: PosteVente) -> None:
        self._postes[poste.id] = poste

    def obtenir_poste(self, poste_id: UUID) -> PosteVente | None:
        return self._postes.get(poste_id)

    def lister_postes(self) -> tuple[PosteVente, ...]:
        return tuple(self._postes.values())

    def enregistrer_vente(self, vente: Vente) -> None:
        self._ventes[vente.id] = vente

    def obtenir_vente(self, vente_id: UUID) -> Vente | None:
        return self._ventes.get(vente_id)

    def lister_ventes(self) -> tuple[Vente, ...]:
        return tuple(self._ventes.values())
