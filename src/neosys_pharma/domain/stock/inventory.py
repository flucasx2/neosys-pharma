from __future__ import annotations

from datetime import date
from uuid import UUID

from neosys_pharma.domain.shared import DomainError
from neosys_pharma.domain.stock.entities import (
    AllocationFefo,
    Emplacement,
    Lot,
    MouvementStock,
    StockEmplacement,
)
from neosys_pharma.domain.stock.enums import EtatLot, TypeMouvement
from neosys_pharma.domain.stock.exceptions import StockInsuffisant


class Inventaire:
    """Agrégat en mémoire utilisé pour exprimer les règles du stock."""

    def __init__(self) -> None:
        self._lots: dict[UUID, Lot] = {}
        self._emplacements: dict[UUID, Emplacement] = {}
        self._stocks: dict[tuple[UUID, UUID], StockEmplacement] = {}
        self._mouvements: list[MouvementStock] = []

    @property
    def mouvements(self) -> tuple[MouvementStock, ...]:
        return tuple(self._mouvements)

    def ajouter_emplacement(self, emplacement: Emplacement) -> None:
        self._emplacements[emplacement.id] = emplacement

    def ajouter_lot(self, lot: Lot) -> None:
        if any(
            existant.conditionnement_id == lot.conditionnement_id and existant.numero == lot.numero
            for existant in self._lots.values()
        ):
            raise DomainError("Ce numéro de lot existe déjà pour ce conditionnement.")
        self._lots[lot.id] = lot

    def charger_position(self, position: StockEmplacement) -> None:
        if position.lot_id not in self._lots:
            raise DomainError("Impossible de charger une position dont le lot est inconnu.")
        if position.emplacement_id not in self._emplacements:
            raise DomainError("Impossible de charger une position dont l'emplacement est inconnu.")
        self._stocks[(position.lot_id, position.emplacement_id)] = position

    def stock(self, lot_id: UUID, emplacement_id: UUID) -> StockEmplacement:
        return self._stocks.setdefault(
            (lot_id, emplacement_id),
            StockEmplacement(lot_id=lot_id, emplacement_id=emplacement_id),
        )

    def receptionner(
        self, *, lot_id: UUID, emplacement_id: UUID, quantite: int, motif: str
    ) -> MouvementStock:
        self._verifier_references(lot_id, emplacement_id)
        self._verifier_quantite(quantite)
        self.stock(lot_id, emplacement_id).quantite_physique += quantite
        return self._enregistrer(
            MouvementStock(
                type=TypeMouvement.RECEPTION,
                lot_id=lot_id,
                quantite=quantite,
                emplacement_destination_id=emplacement_id,
                motif=motif,
            )
        )

    def transferer(
        self,
        *,
        lot_id: UUID,
        source_id: UUID,
        destination_id: UUID,
        quantite: int,
        motif: str,
    ) -> tuple[MouvementStock, MouvementStock]:
        self._verifier_references(lot_id, source_id)
        self._verifier_references(lot_id, destination_id)
        self._verifier_quantite(quantite)
        if source_id == destination_id:
            raise DomainError("La source et la destination doivent être différentes.")

        source = self.stock(lot_id, source_id)
        if source.quantite_disponible < quantite:
            raise StockInsuffisant("Le stock disponible de l'emplacement source est insuffisant.")

        destination = self.stock(lot_id, destination_id)
        source.quantite_physique -= quantite
        destination.quantite_physique += quantite

        sortie = self._enregistrer(
            MouvementStock(
                type=TypeMouvement.TRANSFERT_SORTANT,
                lot_id=lot_id,
                quantite=quantite,
                emplacement_source_id=source_id,
                emplacement_destination_id=destination_id,
                motif=motif,
            )
        )
        entree = self._enregistrer(
            MouvementStock(
                type=TypeMouvement.TRANSFERT_ENTRANT,
                lot_id=lot_id,
                quantite=quantite,
                emplacement_source_id=source_id,
                emplacement_destination_id=destination_id,
                motif=motif,
            )
        )
        return sortie, entree

    def proposer_fefo(
        self,
        *,
        conditionnement_id: UUID,
        emplacement_id: UUID,
        quantite: int,
        au: date,
    ) -> tuple[AllocationFefo, ...]:
        self._verifier_quantite(quantite)
        emplacement = self._emplacements.get(emplacement_id)
        if emplacement is None:
            raise DomainError("L'emplacement est inconnu.")
        candidats: list[tuple[Lot, StockEmplacement]] = []
        for lot in self._lots.values():
            if lot.conditionnement_id != conditionnement_id or not lot.est_vendable(au):
                continue
            stock = self._stocks.get((lot.id, emplacement_id))
            if stock is not None and stock.quantite_disponible > 0:
                candidats.append((lot, stock))

        candidats.sort(key=lambda element: (element[0].date_expiration, element[0].numero))
        restant = quantite
        allocations: list[AllocationFefo] = []
        for lot, stock in candidats:
            a_prendre = min(stock.quantite_disponible, restant)
            allocations.append(
                AllocationFefo(
                    lot_id=lot.id,
                    quantite=a_prendre,
                    date_expiration=lot.date_expiration,
                )
            )
            restant -= a_prendre
            if restant == 0:
                return tuple(allocations)

        raise StockInsuffisant("Le stock disponible est insuffisant dans l'emplacement demandé.")

    def reserver_fefo(
        self,
        *,
        conditionnement_id: UUID,
        emplacement_id: UUID,
        quantite: int,
        au: date,
        motif: str,
    ) -> tuple[AllocationFefo, ...]:
        allocations = self.proposer_fefo(
            conditionnement_id=conditionnement_id,
            emplacement_id=emplacement_id,
            quantite=quantite,
            au=au,
        )
        for allocation in allocations:
            self.stock(allocation.lot_id, emplacement_id).quantite_reservee += allocation.quantite
            self._enregistrer(
                MouvementStock(
                    type=TypeMouvement.RESERVATION,
                    lot_id=allocation.lot_id,
                    quantite=allocation.quantite,
                    emplacement_source_id=emplacement_id,
                    motif=motif,
                )
            )
        return allocations

    def liberer_reservations(
        self,
        *,
        allocations: tuple[AllocationFefo, ...],
        emplacement_id: UUID,
        motif: str,
    ) -> tuple[MouvementStock, ...]:
        self._verifier_allocations_reservees(allocations, emplacement_id)
        mouvements: list[MouvementStock] = []
        for allocation in allocations:
            stock = self.stock(allocation.lot_id, emplacement_id)
            stock.quantite_reservee -= allocation.quantite
            mouvements.append(
                self._enregistrer(
                    MouvementStock(
                        type=TypeMouvement.LIBERATION,
                        lot_id=allocation.lot_id,
                        quantite=allocation.quantite,
                        emplacement_destination_id=emplacement_id,
                        motif=motif,
                    )
                )
            )
        return tuple(mouvements)

    def confirmer_sortie(
        self,
        *,
        allocations: tuple[AllocationFefo, ...],
        emplacement_id: UUID,
        motif: str,
    ) -> tuple[MouvementStock, ...]:
        self._verifier_allocations_reservees(allocations, emplacement_id)
        mouvements: list[MouvementStock] = []
        for allocation in allocations:
            stock = self.stock(allocation.lot_id, emplacement_id)
            stock.quantite_reservee -= allocation.quantite
            stock.quantite_physique -= allocation.quantite
            mouvements.append(
                self._enregistrer(
                    MouvementStock(
                        type=TypeMouvement.SORTIE_VENTE,
                        lot_id=allocation.lot_id,
                        quantite=allocation.quantite,
                        emplacement_source_id=emplacement_id,
                        motif=motif,
                    )
                )
            )
            if self._quantite_physique_totale(allocation.lot_id) == 0:
                self._lots[allocation.lot_id].etat = EtatLot.EPUISE
        return tuple(mouvements)

    def ajuster_inventaire(
        self,
        *,
        lot_id: UUID,
        emplacement_id: UUID,
        nouvelle_quantite: int,
        motif: str,
    ) -> MouvementStock | None:
        self._verifier_references(lot_id, emplacement_id)
        if nouvelle_quantite < 0:
            raise DomainError("La quantité inventoriée ne peut pas être négative.")
        stock = self.stock(lot_id, emplacement_id)
        if nouvelle_quantite < stock.quantite_reservee:
            raise DomainError("L'ajustement ne peut pas supprimer du stock déjà réservé.")

        ecart = nouvelle_quantite - stock.quantite_physique
        if ecart == 0:
            return None

        stock.quantite_physique = nouvelle_quantite
        type_mouvement = (
            TypeMouvement.AJUSTEMENT_POSITIF if ecart > 0 else TypeMouvement.AJUSTEMENT_NEGATIF
        )
        return self._enregistrer(
            MouvementStock(
                type=type_mouvement,
                lot_id=lot_id,
                quantite=abs(ecart),
                emplacement_source_id=emplacement_id if ecart < 0 else None,
                emplacement_destination_id=emplacement_id if ecart > 0 else None,
                motif=motif,
            )
        )

    def changer_etat_lot(self, lot_id: UUID, nouvel_etat: EtatLot) -> None:
        try:
            self._lots[lot_id].etat = nouvel_etat
        except KeyError as error:
            raise DomainError("Le lot est inconnu.") from error

    def _verifier_references(self, lot_id: UUID, emplacement_id: UUID) -> None:
        if lot_id not in self._lots:
            raise DomainError("Le lot est inconnu.")
        if emplacement_id not in self._emplacements:
            raise DomainError("L'emplacement est inconnu.")

    def _verifier_allocations_reservees(
        self,
        allocations: tuple[AllocationFefo, ...],
        emplacement_id: UUID,
    ) -> None:
        if not allocations:
            raise DomainError("Au moins une allocation est obligatoire.")
        if emplacement_id not in self._emplacements:
            raise DomainError("L'emplacement est inconnu.")
        for allocation in allocations:
            if allocation.quantite <= 0:
                raise DomainError("La quantité allouée doit être strictement positive.")
            stock = self._stocks.get((allocation.lot_id, emplacement_id))
            if stock is None or stock.quantite_reservee < allocation.quantite:
                raise DomainError("La quantité à traiter dépasse la quantité réservée.")

    def _quantite_physique_totale(self, lot_id: UUID) -> int:
        return sum(
            stock.quantite_physique
            for (stock_lot_id, _), stock in self._stocks.items()
            if stock_lot_id == lot_id
        )

    @staticmethod
    def _verifier_quantite(quantite: int) -> None:
        if quantite <= 0:
            raise DomainError("La quantité doit être strictement positive.")

    def _enregistrer(self, mouvement: MouvementStock) -> MouvementStock:
        self._mouvements.append(mouvement)
        return mouvement
