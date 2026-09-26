from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

from neosys_pharma.domain.catalogue import (
    CommandeAchat,
    Fournisseur,
    LigneCommandeAchat,
    Marque,
    Medicament,
    OrganismePriseEnCharge,
    PrincipeActif,
    Produit,
    ProduitConditionnement,
    ProduitCosmetique,
    TarifFournisseur,
)
from neosys_pharma.domain.stock import (
    Emplacement,
    EtatLot,
    Lot,
    MouvementStock,
    StockEmplacement,
    TypeMouvement,
)
from neosys_pharma.infrastructure.persistence.database import session_scope
from neosys_pharma.infrastructure.persistence.models import (
    AllocationLotModel,
    CommandeAchatModel,
    ConditionnementModel,
    EmplacementModel,
    FournisseurModel,
    LigneCommandeAchatModel,
    LigneVenteModel,
    LotModel,
    MarqueModel,
    MouvementStockModel,
    OrganismePriseEnChargeModel,
    PrincipeActifModel,
    ProduitModel,
    StockEmplacementModel,
    TarifFournisseurModel,
    VenteModel,
)


class SqlAlchemyCatalogueRepository:
    def __init__(self, factory: sessionmaker[Session]) -> None:
        self._factory = factory

    def enregistrer_produit(self, produit: Produit) -> None:
        with session_scope(self._factory) as session:
            session.merge(
                ProduitModel(
                    id=str(produit.id),
                    type_produit="medicament" if isinstance(produit, Medicament) else "cosmetique",
                    reference=produit.reference,
                    designation=produit.designation,
                    cip7=produit.cip7 or None,
                    principe_actif_id=(
                        str(produit.principe_actif_id)
                        if isinstance(produit, Medicament) and produit.principe_actif_id is not None
                        else None
                    ),
                    principe_actif=(
                        produit.principe_actif if isinstance(produit, Medicament) else None
                    ),
                    marque=produit.marque if isinstance(produit, ProduitCosmetique) else None,
                    marque_id=(
                        str(produit.marque_id)
                        if isinstance(produit, ProduitCosmetique) and produit.marque_id is not None
                        else None
                    ),
                    pris_en_charge_cnamgs=produit.pris_en_charge_cnamgs,
                    taux_prise_en_charge_cnamgs=produit.taux_prise_en_charge_cnamgs,
                )
            )
            for item in produit.conditionnements:
                session.merge(self._conditionnement_model(item))

    def obtenir_produit(self, produit_id: UUID) -> Produit | None:
        with session_scope(self._factory) as session:
            model = session.get(ProduitModel, str(produit_id))
            return None if model is None else self._produit_domain(session, model)

    def obtenir_produit_par_reference(self, reference: str) -> Produit | None:
        with session_scope(self._factory) as session:
            model = session.scalar(
                select(ProduitModel).where(ProduitModel.reference == reference.strip())
            )
            return None if model is None else self._produit_domain(session, model)

    def obtenir_produit_par_cip7(self, cip7: str) -> Produit | None:
        with session_scope(self._factory) as session:
            model = session.scalar(select(ProduitModel).where(ProduitModel.cip7 == cip7.strip()))
            return None if model is None else self._produit_domain(session, model)

    def obtenir_conditionnement(self, conditionnement_id: UUID) -> ProduitConditionnement | None:
        with session_scope(self._factory) as session:
            model = session.get(ConditionnementModel, str(conditionnement_id))
            return None if model is None else self._conditionnement_domain(model)

    def lister_produits(self) -> tuple[Produit, ...]:
        with session_scope(self._factory) as session:
            models = session.scalars(select(ProduitModel).order_by(ProduitModel.designation))
            return tuple(self._produit_domain(session, model) for model in models)

    def reinitialiser_catalogue(self) -> int:
        with session_scope(self._factory) as session:
            nombre = len(tuple(session.scalars(select(ProduitModel.id))))
            for model in (
                AllocationLotModel,
                LigneVenteModel,
                VenteModel,
                MouvementStockModel,
                StockEmplacementModel,
                LotModel,
                LigneCommandeAchatModel,
                CommandeAchatModel,
                TarifFournisseurModel,
                ConditionnementModel,
                ProduitModel,
            ):
                session.execute(delete(model))
            return nombre

    def enregistrer_principe_actif(self, principe: PrincipeActif) -> None:
        with session_scope(self._factory) as session:
            session.merge(PrincipeActifModel(id=str(principe.id), libelle=principe.libelle))

    def obtenir_principe_actif(self, principe_id: UUID) -> PrincipeActif | None:
        with session_scope(self._factory) as session:
            model = session.get(PrincipeActifModel, str(principe_id))
            return None if model is None else self._principe_actif_domain(model)

    def obtenir_principe_actif_par_libelle(self, libelle: str) -> PrincipeActif | None:
        with session_scope(self._factory) as session:
            model = session.scalar(
                select(PrincipeActifModel).where(PrincipeActifModel.libelle == libelle.strip())
            )
            return None if model is None else self._principe_actif_domain(model)

    def lister_principes_actifs(self) -> tuple[PrincipeActif, ...]:
        with session_scope(self._factory) as session:
            models = session.scalars(
                select(PrincipeActifModel).order_by(PrincipeActifModel.libelle)
            )
            return tuple(self._principe_actif_domain(model) for model in models)

    def enregistrer_marque(self, marque: Marque) -> None:
        with session_scope(self._factory) as session:
            session.merge(MarqueModel(id=str(marque.id), libelle=marque.libelle))

    def obtenir_marque(self, marque_id: UUID) -> Marque | None:
        with session_scope(self._factory) as session:
            model = session.get(MarqueModel, str(marque_id))
            return None if model is None else self._marque_domain(model)

    def obtenir_marque_par_libelle(self, libelle: str) -> Marque | None:
        with session_scope(self._factory) as session:
            model = session.scalar(
                select(MarqueModel).where(MarqueModel.libelle == libelle.strip())
            )
            return None if model is None else self._marque_domain(model)

    def lister_marques(self) -> tuple[Marque, ...]:
        with session_scope(self._factory) as session:
            models = session.scalars(select(MarqueModel).order_by(MarqueModel.libelle))
            return tuple(self._marque_domain(model) for model in models)

    def enregistrer_fournisseur(self, fournisseur: Fournisseur) -> None:
        with session_scope(self._factory) as session:
            session.merge(
                FournisseurModel(
                    id=str(fournisseur.id),
                    code=fournisseur.code,
                    raison_sociale=fournisseur.raison_sociale,
                    telephone=fournisseur.telephone,
                    email=fournisseur.email,
                    actif=fournisseur.actif,
                )
            )

    def obtenir_fournisseur(self, fournisseur_id: UUID) -> Fournisseur | None:
        with session_scope(self._factory) as session:
            model = session.get(FournisseurModel, str(fournisseur_id))
            return None if model is None else self._fournisseur_domain(model)

    def obtenir_fournisseur_par_code(self, code: str) -> Fournisseur | None:
        with session_scope(self._factory) as session:
            model = session.scalar(
                select(FournisseurModel).where(FournisseurModel.code == code.strip())
            )
            return None if model is None else self._fournisseur_domain(model)

    def lister_fournisseurs(self) -> tuple[Fournisseur, ...]:
        with session_scope(self._factory) as session:
            models = session.scalars(
                select(FournisseurModel).order_by(FournisseurModel.raison_sociale)
            )
            return tuple(self._fournisseur_domain(model) for model in models)

    def enregistrer_tarif_fournisseur(self, tarif: TarifFournisseur) -> None:
        with session_scope(self._factory) as session:
            session.merge(
                TarifFournisseurModel(
                    id=str(tarif.id),
                    fournisseur_id=str(tarif.fournisseur_id),
                    conditionnement_id=str(tarif.conditionnement_id),
                    prix_achat=tarif.prix_achat,
                    reference_fournisseur=tarif.reference_fournisseur,
                )
            )

    def obtenir_tarif_fournisseur(
        self, *, fournisseur_id: UUID, conditionnement_id: UUID
    ) -> TarifFournisseur | None:
        with session_scope(self._factory) as session:
            model = session.scalar(
                select(TarifFournisseurModel).where(
                    TarifFournisseurModel.fournisseur_id == str(fournisseur_id),
                    TarifFournisseurModel.conditionnement_id == str(conditionnement_id),
                )
            )
            return None if model is None else self._tarif_fournisseur_domain(model)

    def lister_tarifs_fournisseurs(self) -> tuple[TarifFournisseur, ...]:
        with session_scope(self._factory) as session:
            models = session.scalars(select(TarifFournisseurModel))
            return tuple(self._tarif_fournisseur_domain(model) for model in models)

    def enregistrer_commande_achat(self, commande: CommandeAchat) -> None:
        with session_scope(self._factory) as session:
            session.merge(
                CommandeAchatModel(
                    id=str(commande.id),
                    numero_interne=commande.numero_interne,
                    fournisseur_id=str(commande.fournisseur_id),
                    emplacement_id=str(commande.emplacement_id),
                    date_commande=commande.date_commande,
                    date_arrivee=commande.date_arrivee,
                    numero_fournisseur=commande.numero_fournisseur,
                )
            )
            for ligne in commande.lignes:
                session.merge(
                    LigneCommandeAchatModel(
                        id=str(ligne.id),
                        commande_id=str(commande.id),
                        conditionnement_id=str(ligne.conditionnement_id),
                        designation=ligne.designation,
                        cip7=ligne.cip7,
                        quantite_commandee=ligne.quantite_commandee,
                        quantite_recue=ligne.quantite_recue,
                        numero_lot=ligne.numero_lot,
                        date_expiration=ligne.date_expiration,
                        prix_unitaire=ligne.prix_unitaire,
                    )
                )

    def lister_commandes_achat(self) -> tuple[CommandeAchat, ...]:
        with session_scope(self._factory) as session:
            models = session.scalars(
                select(CommandeAchatModel).order_by(CommandeAchatModel.numero_interne)
            )
            return tuple(self._commande_domain(session, model) for model in models)

    def enregistrer_organisme(self, organisme: OrganismePriseEnCharge) -> None:
        with session_scope(self._factory) as session:
            session.merge(
                OrganismePriseEnChargeModel(
                    id=str(organisme.id),
                    code=organisme.code,
                    nom=organisme.nom,
                    type_organisme=organisme.type_organisme,
                    documents_requis=list(organisme.documents_requis),
                    actif=organisme.actif,
                    taux_prise_en_charge=organisme.taux_prise_en_charge,
                )
            )

    def obtenir_organisme_par_code(self, code: str) -> OrganismePriseEnCharge | None:
        with session_scope(self._factory) as session:
            model = session.scalar(
                select(OrganismePriseEnChargeModel).where(
                    OrganismePriseEnChargeModel.code == code.strip()
                )
            )
            return None if model is None else self._organisme_domain(model)

    def obtenir_organisme(self, organisme_id: UUID) -> OrganismePriseEnCharge | None:
        with session_scope(self._factory) as session:
            model = session.get(OrganismePriseEnChargeModel, str(organisme_id))
            return None if model is None else self._organisme_domain(model)

    def lister_organismes(self) -> tuple[OrganismePriseEnCharge, ...]:
        with session_scope(self._factory) as session:
            models = session.scalars(
                select(OrganismePriseEnChargeModel).order_by(OrganismePriseEnChargeModel.nom)
            )
            return tuple(self._organisme_domain(model) for model in models)

    @staticmethod
    def _conditionnement_model(item: ProduitConditionnement) -> ConditionnementModel:
        return ConditionnementModel(
            id=str(item.id),
            produit_id=str(item.produit_id),
            code=item.code,
            libelle=item.libelle,
            prix_vente=item.prix_vente,
        )

    @staticmethod
    def _conditionnement_domain(model: ConditionnementModel) -> ProduitConditionnement:
        return ProduitConditionnement(
            id=UUID(model.id),
            produit_id=UUID(model.produit_id),
            code=model.code,
            libelle=model.libelle,
            prix_vente=model.prix_vente,
        )

    def _produit_domain(self, session: Session, model: ProduitModel) -> Produit:
        if model.type_produit == "medicament":
            produit: Produit = Medicament(
                id=UUID(model.id),
                reference=model.reference,
                designation=model.designation,
                cip7=model.cip7 or "",
                principe_actif=model.principe_actif or "",
                principe_actif_id=(
                    UUID(model.principe_actif_id) if model.principe_actif_id else None
                ),
                pris_en_charge_cnamgs=model.pris_en_charge_cnamgs,
                taux_prise_en_charge_cnamgs=model.taux_prise_en_charge_cnamgs,
            )
        else:
            produit = ProduitCosmetique(
                id=UUID(model.id),
                reference=model.reference,
                designation=model.designation,
                cip7=model.cip7 or "",
                marque=model.marque or "",
                marque_id=UUID(model.marque_id) if model.marque_id else None,
                pris_en_charge_cnamgs=model.pris_en_charge_cnamgs,
                taux_prise_en_charge_cnamgs=model.taux_prise_en_charge_cnamgs,
            )
        conditionnements = session.scalars(
            select(ConditionnementModel).where(ConditionnementModel.produit_id == model.id)
        )
        produit.conditionnements.extend(
            self._conditionnement_domain(item) for item in conditionnements
        )
        return produit

    @staticmethod
    def _principe_actif_domain(model: PrincipeActifModel) -> PrincipeActif:
        return PrincipeActif(id=UUID(model.id), libelle=model.libelle)

    @staticmethod
    def _marque_domain(model: MarqueModel) -> Marque:
        return Marque(id=UUID(model.id), libelle=model.libelle)

    @staticmethod
    def _fournisseur_domain(model: FournisseurModel) -> Fournisseur:
        return Fournisseur(
            id=UUID(model.id),
            code=model.code,
            raison_sociale=model.raison_sociale,
            telephone=model.telephone,
            email=model.email,
            actif=model.actif,
        )

    @staticmethod
    def _tarif_fournisseur_domain(
        model: TarifFournisseurModel,
    ) -> TarifFournisseur:
        return TarifFournisseur(
            id=UUID(model.id),
            fournisseur_id=UUID(model.fournisseur_id),
            conditionnement_id=UUID(model.conditionnement_id),
            prix_achat=model.prix_achat,
            reference_fournisseur=model.reference_fournisseur,
        )

    @staticmethod
    def _organisme_domain(model: OrganismePriseEnChargeModel) -> OrganismePriseEnCharge:
        return OrganismePriseEnCharge(
            id=UUID(model.id),
            code=model.code,
            nom=model.nom,
            type_organisme=model.type_organisme,
            documents_requis=tuple(model.documents_requis or []),
            actif=model.actif,
            taux_prise_en_charge=model.taux_prise_en_charge,
        )

    @staticmethod
    def _commande_domain(session: Session, model: CommandeAchatModel) -> CommandeAchat:
        lignes = session.scalars(
            select(LigneCommandeAchatModel).where(LigneCommandeAchatModel.commande_id == model.id)
        )
        return CommandeAchat(
            id=UUID(model.id),
            numero_interne=model.numero_interne,
            fournisseur_id=UUID(model.fournisseur_id),
            emplacement_id=UUID(model.emplacement_id),
            date_commande=model.date_commande,
            date_arrivee=model.date_arrivee,
            numero_fournisseur=model.numero_fournisseur,
            lignes=[
                LigneCommandeAchat(
                    id=UUID(ligne.id),
                    conditionnement_id=UUID(ligne.conditionnement_id),
                    designation=ligne.designation,
                    cip7=ligne.cip7,
                    quantite_commandee=ligne.quantite_commandee,
                    quantite_recue=ligne.quantite_recue,
                    numero_lot=ligne.numero_lot,
                    date_expiration=ligne.date_expiration,
                    prix_unitaire=ligne.prix_unitaire,
                )
                for ligne in lignes
            ],
        )


class SqlAlchemyStockRepository:
    def __init__(self, factory: sessionmaker[Session]) -> None:
        self._factory = factory

    def enregistrer_lot(self, lot: Lot) -> None:
        with session_scope(self._factory) as session:
            session.merge(
                LotModel(
                    id=str(lot.id),
                    conditionnement_id=str(lot.conditionnement_id),
                    numero=lot.numero,
                    date_expiration=lot.date_expiration,
                    etat=lot.etat.value,
                )
            )

    def obtenir_lot(self, lot_id: UUID) -> Lot | None:
        with session_scope(self._factory) as session:
            model = session.get(LotModel, str(lot_id))
            return None if model is None else self._lot_domain(model)

    def enregistrer_emplacement(self, emplacement: Emplacement) -> None:
        with session_scope(self._factory) as session:
            session.merge(
                EmplacementModel(
                    id=str(emplacement.id),
                    code=emplacement.code,
                    libelle=emplacement.libelle,
                    autorise_vente=emplacement.autorise_vente,
                )
            )

    def obtenir_emplacement(self, emplacement_id: UUID) -> Emplacement | None:
        with session_scope(self._factory) as session:
            model = session.get(EmplacementModel, str(emplacement_id))
            return None if model is None else self._emplacement_domain(model)

    def enregistrer_position(self, position: StockEmplacement) -> None:
        with session_scope(self._factory) as session:
            session.merge(
                StockEmplacementModel(
                    lot_id=str(position.lot_id),
                    emplacement_id=str(position.emplacement_id),
                    quantite_physique=position.quantite_physique,
                    quantite_reservee=position.quantite_reservee,
                )
            )

    def obtenir_position(self, *, lot_id: UUID, emplacement_id: UUID) -> StockEmplacement | None:
        with session_scope(self._factory) as session:
            model = session.get(StockEmplacementModel, (str(lot_id), str(emplacement_id)))
            return None if model is None else self._position_domain(model)

    def enregistrer_mouvement(self, mouvement: MouvementStock) -> None:
        with session_scope(self._factory) as session:
            session.merge(
                MouvementStockModel(
                    id=str(mouvement.id),
                    type_mouvement=mouvement.type.value,
                    lot_id=str(mouvement.lot_id),
                    quantite=mouvement.quantite,
                    emplacement_source_id=(
                        str(mouvement.emplacement_source_id)
                        if mouvement.emplacement_source_id
                        else None
                    ),
                    emplacement_destination_id=(
                        str(mouvement.emplacement_destination_id)
                        if mouvement.emplacement_destination_id
                        else None
                    ),
                    motif=mouvement.motif,
                    cree_le=mouvement.cree_le,
                )
            )

    def lister_mouvements(self) -> tuple[MouvementStock, ...]:
        with session_scope(self._factory) as session:
            models = session.scalars(
                select(MouvementStockModel).order_by(MouvementStockModel.cree_le)
            )
            return tuple(self._mouvement_domain(model) for model in models)

    def lister_lots(self) -> tuple[Lot, ...]:
        with session_scope(self._factory) as session:
            return tuple(self._lot_domain(model) for model in session.scalars(select(LotModel)))

    def lister_emplacements(self) -> tuple[Emplacement, ...]:
        with session_scope(self._factory) as session:
            return tuple(
                self._emplacement_domain(model)
                for model in session.scalars(select(EmplacementModel))
            )

    def lister_toutes_positions(self) -> tuple[StockEmplacement, ...]:
        with session_scope(self._factory) as session:
            return tuple(
                self._position_domain(model)
                for model in session.scalars(select(StockEmplacementModel))
            )

    def lister_positions(
        self, *, conditionnement_id: UUID, emplacement_id: UUID
    ) -> tuple[StockEmplacement, ...]:
        with session_scope(self._factory) as session:
            models = session.scalars(
                select(StockEmplacementModel)
                .join(LotModel, StockEmplacementModel.lot_id == LotModel.id)
                .where(
                    LotModel.conditionnement_id == str(conditionnement_id),
                    StockEmplacementModel.emplacement_id == str(emplacement_id),
                )
            )
            return tuple(self._position_domain(model) for model in models)

    @staticmethod
    def _lot_domain(model: LotModel) -> Lot:
        return Lot(
            id=UUID(model.id),
            conditionnement_id=UUID(model.conditionnement_id),
            numero=model.numero,
            date_expiration=model.date_expiration,
            etat=EtatLot(model.etat),
        )

    @staticmethod
    def _emplacement_domain(model: EmplacementModel) -> Emplacement:
        return Emplacement(
            id=UUID(model.id),
            code=model.code,
            libelle=model.libelle,
            autorise_vente=model.autorise_vente,
        )

    @staticmethod
    def _position_domain(model: StockEmplacementModel) -> StockEmplacement:
        return StockEmplacement(
            lot_id=UUID(model.lot_id),
            emplacement_id=UUID(model.emplacement_id),
            quantite_physique=model.quantite_physique,
            quantite_reservee=model.quantite_reservee,
        )

    @staticmethod
    def _mouvement_domain(model: MouvementStockModel) -> MouvementStock:
        return MouvementStock(
            id=UUID(model.id),
            type=TypeMouvement(model.type_mouvement),
            lot_id=UUID(model.lot_id),
            quantite=model.quantite,
            emplacement_source_id=(
                UUID(model.emplacement_source_id) if model.emplacement_source_id else None
            ),
            emplacement_destination_id=(
                UUID(model.emplacement_destination_id) if model.emplacement_destination_id else None
            ),
            motif=model.motif,
            cree_le=model.cree_le,
        )
