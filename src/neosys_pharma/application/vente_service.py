from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

from neosys_pharma.application.dto import AjouterLigneVente, CreerPosteVente
from neosys_pharma.application.fidelite_service import FideliteService
from neosys_pharma.application.ports import CatalogueRepository, VenteRepository
from neosys_pharma.application.services import StockService
from neosys_pharma.domain.shared import DomainError
from neosys_pharma.domain.stock import AllocationFefo, StockInsuffisant
from neosys_pharma.domain.vente import AllocationLot, LigneVente, PosteVente, Vente


class VenteService:
    def __init__(
        self,
        depot: VenteRepository,
        catalogue: CatalogueRepository,
        stock: StockService,
        fidelite: FideliteService | None = None,
    ) -> None:
        self._depot = depot
        self._catalogue = catalogue
        self._stock = stock
        self._fidelite = fidelite

    def creer_poste(self, commande: CreerPosteVente) -> PosteVente:
        if not self._stock.emplacement_existe(commande.emplacement_id):
            raise DomainError("L'emplacement du poste est inconnu.")
        poste = PosteVente(
            code=commande.code,
            secteur_id=commande.secteur_id,
            emplacement_id=commande.emplacement_id,
            caisse_id=commande.caisse_id,
        )
        self._depot.enregistrer_poste(poste)
        return poste

    def lister_postes(self) -> tuple[PosteVente, ...]:
        return self._depot.lister_postes()

    def creer_vente(
        self,
        *,
        poste_id: UUID,
        date_commerciale: date,
        organisme_id: UUID | None = None,
        patient_nom: str = "",
        patient_prenom: str = "",
        informations_prise_en_charge: dict[str, str] | None = None,
    ) -> Vente:
        poste = self._poste_obligatoire(poste_id)
        vente = Vente(
            poste_id=poste.id,
            secteur_id=poste.secteur_id,
            emplacement_id=poste.emplacement_id,
            date_commerciale=date_commerciale,
            organisme_id=organisme_id,
            patient_nom=patient_nom.strip().upper(),
            patient_prenom=patient_prenom.strip().upper(),
            informations_prise_en_charge=informations_prise_en_charge or {},
        )
        self._depot.enregistrer_vente(vente)
        return vente

    def ajouter_ligne(self, commande: AjouterLigneVente) -> LigneVente:
        vente = self._vente_obligatoire(commande.vente_id)
        conditionnement = self._catalogue.obtenir_conditionnement(commande.conditionnement_id)
        if conditionnement is None:
            raise DomainError("Le conditionnement est inconnu.")
        ligne = vente.ajouter_ligne(
            conditionnement_id=conditionnement.id,
            designation=conditionnement.libelle,
            quantite=commande.quantite,
            prix_unitaire=conditionnement.prix_vente,
        )
        self._depot.enregistrer_vente(vente)
        return ligne

    def preparer(self, vente_id: UUID) -> Vente:
        vente = self._vente_obligatoire(vente_id)
        reservations_effectuees: list[tuple[UUID, AllocationFefo]] = []
        allocations_vente: list[AllocationLot] = []
        try:
            for ligne in vente.lignes:
                restant = ligne.quantite
                emplacements = list(self._stock.lister_emplacements())
                # Le stock du poste est utilisé en priorité, puis les rayons de vente,
                # puis les réserves. Aucun emplacement contenant du stock vendable
                # ne doit toutefois bloquer une préparation.
                emplacements.sort(
                    key=lambda item: (
                        item.id != vente.emplacement_id,
                        not item.autorise_vente,
                        item.code,
                    )
                )
                vendable_global = sum(
                    item.quantite_disponible
                    for emplacement in emplacements
                    for item in self._stock.consulter_stock(
                        conditionnement_id=ligne.conditionnement_id,
                        emplacement_id=emplacement.id,
                    )
                    if item.etat_lot == "actif"
                    and item.date_expiration >= vente.date_commerciale
                )
                if vendable_global < ligne.quantite:
                    raise StockInsuffisant(
                        self._message_stock_insuffisant(
                            conditionnement_id=ligne.conditionnement_id,
                            quantite_demandee=ligne.quantite,
                            au=vente.date_commerciale,
                        )
                    )
                for emplacement in emplacements:
                    disponible = sum(
                        item.quantite_disponible
                        for item in self._stock.consulter_stock(
                            conditionnement_id=ligne.conditionnement_id,
                            emplacement_id=emplacement.id,
                        )
                        if item.etat_lot == "actif"
                        and item.date_expiration >= vente.date_commerciale
                    )
                    a_reserver = min(restant, disponible)
                    if not a_reserver:
                        continue
                    reservations = self._stock.reserver_fefo(
                        conditionnement_id=ligne.conditionnement_id,
                        emplacement_id=emplacement.id,
                        quantite=a_reserver,
                        au=vente.date_commerciale,
                        motif=f"Préparation vente {vente.id}",
                    )
                    reservations_effectuees.extend((emplacement.id, item) for item in reservations)
                    allocations_vente.extend(
                        AllocationLot(
                            ligne_vente_id=ligne.id,
                            lot_id=reservation.lot_id,
                            quantite=reservation.quantite,
                            date_expiration=reservation.date_expiration,
                            emplacement_id=emplacement.id,
                        )
                        for reservation in reservations
                    )
                    restant -= a_reserver
                    if restant == 0:
                        break
                if restant:
                    raise StockInsuffisant(
                        self._message_stock_insuffisant(
                            conditionnement_id=ligne.conditionnement_id,
                            quantite_demandee=ligne.quantite,
                            au=vente.date_commerciale,
                        )
                    )
        except DomainError:
            for emplacement_id in {item[0] for item in reservations_effectuees}:
                self._stock.liberer_reservations(
                    allocations=tuple(
                        allocation
                        for location_id, allocation in reservations_effectuees
                        if location_id == emplacement_id
                    ),
                    emplacement_id=emplacement_id,
                    motif=f"Compensation préparation vente {vente.id}",
                )
            raise
        vente.placer_en_attente(allocations_vente)
        self._depot.enregistrer_vente(vente)
        return vente

    def _message_stock_insuffisant(
        self, *, conditionnement_id: UUID, quantite_demandee: int, au: date
    ) -> str:
        lignes = [
            ligne
            for emplacement in self._stock.lister_emplacements()
            for ligne in self._stock.consulter_stock(
                conditionnement_id=conditionnement_id,
                emplacement_id=emplacement.id,
            )
        ]
        physique = sum(ligne.quantite_physique for ligne in lignes)
        reserve = sum(ligne.quantite_reservee for ligne in lignes)
        perime = sum(
            ligne.quantite_disponible
            for ligne in lignes
            if ligne.date_expiration < au
        )
        bloque = sum(
            ligne.quantite_disponible
            for ligne in lignes
            if ligne.date_expiration >= au and ligne.etat_lot != "actif"
        )
        vendable = sum(
            ligne.quantite_disponible
            for ligne in lignes
            if ligne.date_expiration >= au and ligne.etat_lot == "actif"
        )
        raisons: list[str] = []
        if reserve:
            raisons.append(f"{reserve} unité(s) déjà réservée(s)")
        if perime:
            raisons.append(f"{perime} unité(s) périmée(s)")
        if bloque:
            raisons.append(f"{bloque} unité(s) dans un lot bloqué")
        if not raisons:
            raisons.append(
                f"seulement {vendable} unité(s) vendable(s) pour {quantite_demandee} demandée(s)"
                if physique
                else "aucune quantité physique enregistrée"
            )
        detail = "; ".join(raisons)
        return (
            f"Stock insuffisant : {quantite_demandee} unité(s) demandée(s), "
            f"{physique} physique(s), {reserve} réservée(s) et {vendable} vendable(s). "
            f"Cause : {detail}."
        )

    def annuler(self, vente_id: UUID) -> Vente:
        vente = self._vente_obligatoire(vente_id)
        if vente.allocations:
            emplacements = {
                allocation.emplacement_id or vente.emplacement_id
                for allocation in vente.allocations
            }
            for emplacement_id in emplacements:
                self._stock.liberer_reservations(
                    allocations=tuple(
                        AllocationFefo(
                            lot_id=a.lot_id, quantite=a.quantite, date_expiration=a.date_expiration
                        )
                        for a in vente.allocations
                        if (a.emplacement_id or vente.emplacement_id) == emplacement_id
                    ),
                    emplacement_id=emplacement_id,
                    motif=f"Annulation vente {vente.id}",
                )
        vente.annuler()
        self._depot.enregistrer_vente(vente)
        return vente

    def obtenir(self, vente_id: UUID) -> Vente:
        return self._vente_obligatoire(vente_id)

    def lister(self, etat: str | None = None) -> tuple[Vente, ...]:
        ventes = self._depot.lister_ventes()
        if etat:
            ventes = tuple(item for item in ventes if item.etat.value == etat)
        return ventes

    def encaisser(
        self,
        *,
        vente_ids: list[UUID],
        reglements: list[dict[str, str]],
        carte_fidelite_id: UUID | None = None,
        points_utilises: int = 0,
    ) -> tuple[Vente, ...]:
        if not vente_ids:
            raise DomainError("Sélectionnez au moins un ticket à encaisser.")
        ventes = tuple(self._vente_obligatoire(item_id) for item_id in vente_ids)
        total = sum((item.montant_a_payer for item in ventes), start=Decimal("0"))
        remise = Decimal(points_utilises * 10)
        if points_utilises < 0 or remise > total:
            raise DomainError("Le nombre de points utilisé est invalide.")
        total_regle = sum(
            (Decimal(str(item["montant"])) for item in reglements),
            start=Decimal("0"),
        )
        if total_regle != total - remise:
            raise DomainError("Le total des règlements doit correspondre au montant à payer.")
        if points_utilises:
            if self._fidelite is None or carte_fidelite_id is None:
                raise DomainError(
                    "Une carte de fidélité active est requise pour utiliser des points."
                )
            self._fidelite.ajuster_points(
                carte_fidelite_id,
                points=-points_utilises,
                motif="REMISE ENCAISSEMENT",
            )
        encaissement_id = uuid4()
        for vente in ventes:
            emplacements = {
                allocation.emplacement_id or vente.emplacement_id
                for allocation in vente.allocations
            }
            for emplacement_id in emplacements:
                self._stock.confirmer_sortie(
                    allocations=tuple(
                        AllocationFefo(
                            lot_id=a.lot_id, quantite=a.quantite, date_expiration=a.date_expiration
                        )
                        for a in vente.allocations
                        if (a.emplacement_id or vente.emplacement_id) == emplacement_id
                    ),
                    emplacement_id=emplacement_id,
                    motif=f"Encaissement {encaissement_id}",
                )
            vente.finaliser(
                encaissement_id=encaissement_id,
                reglements=reglements,
                carte_fidelite_id=carte_fidelite_id,
                points_utilises=points_utilises,
            )
            self._depot.enregistrer_vente(vente)
        if carte_fidelite_id and self._fidelite is not None:
            points_gagnes = int((total - remise) // Decimal("1000"))
            if points_gagnes:
                self._fidelite.ajuster_points(
                    carte_fidelite_id,
                    points=points_gagnes,
                    motif=f"ENCAISSEMENT {encaissement_id}",
                )
        return ventes

    def _poste_obligatoire(self, poste_id: UUID) -> PosteVente:
        poste = self._depot.obtenir_poste(poste_id)
        if poste is None:
            raise DomainError("Le poste de vente est inconnu.")
        return poste

    def _vente_obligatoire(self, vente_id: UUID) -> Vente:
        vente = self._depot.obtenir_vente(vente_id)
        if vente is None:
            raise DomainError("La vente est inconnue.")
        return vente
