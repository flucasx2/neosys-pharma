from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from neosys_pharma.domain.vente import (
    AllocationLot,
    EtatVente,
    LigneVente,
    PosteVente,
    Vente,
)
from neosys_pharma.infrastructure.persistence.database import session_scope
from neosys_pharma.infrastructure.persistence.models import (
    AllocationLotModel,
    LigneVenteModel,
    PosteVenteModel,
    VenteModel,
)


class SqlAlchemyVenteRepository:
    def __init__(self, factory: sessionmaker[Session]) -> None:
        self._factory = factory

    def enregistrer_poste(self, poste: PosteVente) -> None:
        with session_scope(self._factory) as session:
            session.merge(
                PosteVenteModel(
                    id=str(poste.id),
                    code=poste.code,
                    secteur_id=str(poste.secteur_id),
                    emplacement_id=str(poste.emplacement_id),
                    caisse_id=str(poste.caisse_id) if poste.caisse_id else None,
                )
            )

    def obtenir_poste(self, poste_id: UUID) -> PosteVente | None:
        with session_scope(self._factory) as session:
            model = session.get(PosteVenteModel, str(poste_id))
            if model is None:
                return None
            return PosteVente(
                id=UUID(model.id),
                code=model.code,
                secteur_id=UUID(model.secteur_id),
                emplacement_id=UUID(model.emplacement_id),
                caisse_id=UUID(model.caisse_id) if model.caisse_id else None,
            )

    def lister_postes(self) -> tuple[PosteVente, ...]:
        with session_scope(self._factory) as session:
            models = session.scalars(select(PosteVenteModel).order_by(PosteVenteModel.code))
            return tuple(
                PosteVente(
                    id=UUID(model.id),
                    code=model.code,
                    secteur_id=UUID(model.secteur_id),
                    emplacement_id=UUID(model.emplacement_id),
                    caisse_id=UUID(model.caisse_id) if model.caisse_id else None,
                )
                for model in models
            )

    def enregistrer_vente(self, vente: Vente) -> None:
        with session_scope(self._factory) as session:
            session.merge(
                VenteModel(
                    id=str(vente.id),
                    poste_id=str(vente.poste_id),
                    secteur_id=str(vente.secteur_id),
                    emplacement_id=str(vente.emplacement_id),
                    date_commerciale=vente.date_commerciale,
                    etat=vente.etat.value,
                    organisme_id=str(vente.organisme_id) if vente.organisme_id else None,
                    patient_nom=vente.patient_nom,
                    patient_prenom=vente.patient_prenom,
                    informations_prise_en_charge=vente.informations_prise_en_charge,
                    encaissement_id=str(vente.encaissement_id) if vente.encaissement_id else None,
                    reglements=vente.reglements,
                    carte_fidelite_id=(
                        str(vente.carte_fidelite_id) if vente.carte_fidelite_id else None
                    ),
                    points_utilises=vente.points_utilises,
                    encaissee_le=vente.encaissee_le,
                )
            )
            for ligne in vente.lignes:
                session.merge(
                    LigneVenteModel(
                        id=str(ligne.id),
                        vente_id=str(vente.id),
                        conditionnement_id=str(ligne.conditionnement_id),
                        designation=ligne.designation,
                        quantite=ligne.quantite,
                        prix_unitaire=ligne.prix_unitaire,
                    )
                )
            for allocation in vente.allocations:
                session.merge(
                    AllocationLotModel(
                        id=str(allocation.id),
                        vente_id=str(vente.id),
                        ligne_vente_id=str(allocation.ligne_vente_id),
                        lot_id=str(allocation.lot_id),
                        quantite=allocation.quantite,
                        date_expiration=allocation.date_expiration,
                        emplacement_id=(
                            str(allocation.emplacement_id) if allocation.emplacement_id else None
                        ),
                    )
                )

    def obtenir_vente(self, vente_id: UUID) -> Vente | None:
        with session_scope(self._factory) as session:
            model = session.get(VenteModel, str(vente_id))
            if model is None:
                return None
            vente = Vente(
                id=UUID(model.id),
                poste_id=UUID(model.poste_id),
                secteur_id=UUID(model.secteur_id),
                emplacement_id=UUID(model.emplacement_id),
                date_commerciale=model.date_commerciale,
                organisme_id=UUID(model.organisme_id) if model.organisme_id else None,
                patient_nom=model.patient_nom,
                patient_prenom=model.patient_prenom,
                informations_prise_en_charge=model.informations_prise_en_charge or {},
            )
            vente.etat = EtatVente(model.etat)
            vente.encaissement_id = UUID(model.encaissement_id) if model.encaissement_id else None
            vente.reglements = model.reglements or []
            vente.carte_fidelite_id = (
                UUID(model.carte_fidelite_id) if model.carte_fidelite_id else None
            )
            vente.points_utilises = model.points_utilises or 0
            vente.encaissee_le = model.encaissee_le
            lignes = session.scalars(
                select(LigneVenteModel).where(LigneVenteModel.vente_id == model.id)
            )
            vente.lignes.extend(
                LigneVente(
                    id=UUID(ligne.id),
                    conditionnement_id=UUID(ligne.conditionnement_id),
                    designation=ligne.designation,
                    quantite=ligne.quantite,
                    prix_unitaire=ligne.prix_unitaire,
                )
                for ligne in lignes
            )
            allocations = session.scalars(
                select(AllocationLotModel).where(AllocationLotModel.vente_id == model.id)
            )
            vente.allocations.extend(
                AllocationLot(
                    id=UUID(allocation.id),
                    ligne_vente_id=UUID(allocation.ligne_vente_id),
                    lot_id=UUID(allocation.lot_id),
                    quantite=allocation.quantite,
                    date_expiration=allocation.date_expiration,
                    emplacement_id=(
                        UUID(allocation.emplacement_id)
                        if allocation.emplacement_id
                        else vente.emplacement_id
                    ),
                )
                for allocation in allocations
            )
            return vente

    def lister_ventes(self) -> tuple[Vente, ...]:
        with session_scope(self._factory) as session:
            ids = tuple(
                session.scalars(select(VenteModel.id).order_by(VenteModel.date_commerciale))
            )
        return tuple(filter(None, (self.obtenir_vente(UUID(item_id)) for item_id in ids)))
