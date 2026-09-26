from __future__ import annotations

from datetime import date
from uuid import UUID

from neosys_pharma.application.dto import (
    AjouterConditionnement,
    AjusterStock,
    CreerCommandeReception,
    CreerFournisseur,
    CreerMedicament,
    CreerOrganismePriseEnCharge,
    CreerProduitCosmetique,
    DefinirTarifFournisseur,
    LigneEtatStock,
    LigneEtatStockGlobal,
    ModifierConditionnement,
    ModifierFournisseur,
    ModifierOrganismePriseEnCharge,
    ModifierProduit,
    ReceptionnerLot,
    TransfererStock,
)
from neosys_pharma.application.ports import CatalogueRepository, StockRepository
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
from neosys_pharma.domain.shared import DomainError
from neosys_pharma.domain.stock import (
    AllocationFefo,
    Emplacement,
    Inventaire,
    Lot,
    MouvementStock,
)

PRINCIPES_ACTIFS_INITIAUX = (
    "Acide acétylsalicylique",
    "Acide folique",
    "Acide fusidique",
    "Acide valproïque",
    "Albendazole",
    "Amoxicilline",
    "Amoxicilline + acide clavulanique",
    "Amlodipine",
    "Artemether + lumefantrine",
    "Artésunate",
    "Aténolol",
    "Azithromycine",
    "Bétaméthasone",
    "Captopril",
    "Carbamazépine",
    "Céftriaxone",
    "Céfixime",
    "Cetirizine",
    "Ciprofloxacine",
    "Clarithromycine",
    "Clotrimazole",
    "Cotrimoxazole",
    "Diclofénac",
    "Doxycycline",
    "Énalapril",
    "Érythromycine",
    "Fluconazole",
    "Furosémide",
    "Gentamicine",
    "Glibenclamide",
    "Hydrochlorothiazide",
    "Ibuprofène",
    "Insuline humaine",
    "Lévofloxacine",
    "Loratadine",
    "Losartan",
    "Mébendazole",
    "Metformine",
    "Métronidazole",
    "Nifédipine",
    "Nystatine",
    "Oméprazole",
    "Paracétamol",
    "Phénobarbital",
    "Prednisolone",
    "Quinine",
    "Salbutamol",
    "Spironolactone",
    "Tramadol",
    "Vitamine C",
)

MARQUES_INITIALES = (
    "AVÈNE",
    "BIODERMA",
    "CERAVE",
    "DUCRAY",
    "EUCERIN",
    "LA ROCHE-POSAY",
    "MUSTELA",
    "NEOCARE",
    "NUXE",
    "VICHY",
)


class CatalogueService:
    def __init__(self, depot: CatalogueRepository) -> None:
        self._depot = depot

    def creer_medicament(self, commande: CreerMedicament) -> Medicament:
        reference = commande.reference.strip() or self._generer_reference("MED")
        self._verifier_reference_unique(reference)
        self._verifier_cip7_unique(commande.cip7)
        principe = self._resoudre_principe_actif(
            principe_actif_id=commande.principe_actif_id,
            libelle=commande.principe_actif,
        )
        produit = Medicament(
            reference=reference,
            designation=commande.designation,
            cip7=commande.cip7,
            principe_actif=principe.libelle,
            principe_actif_id=principe.id,
            pris_en_charge_cnamgs=commande.pris_en_charge_cnamgs,
            taux_prise_en_charge_cnamgs=commande.taux_prise_en_charge_cnamgs,
        )
        self._depot.enregistrer_produit(produit)
        return produit

    def creer_produit_cosmetique(self, commande: CreerProduitCosmetique) -> ProduitCosmetique:
        reference = commande.reference.strip() or self._generer_reference("COS")
        self._verifier_reference_unique(reference)
        self._verifier_cip7_unique(commande.cip7)
        marque = self._resoudre_marque(
            marque_id=commande.marque_id,
            libelle=commande.marque,
        )
        produit = ProduitCosmetique(
            reference=reference,
            designation=commande.designation,
            cip7=commande.cip7,
            marque=marque.libelle,
            marque_id=marque.id,
            pris_en_charge_cnamgs=commande.pris_en_charge_cnamgs,
            taux_prise_en_charge_cnamgs=commande.taux_prise_en_charge_cnamgs,
        )
        self._depot.enregistrer_produit(produit)
        return produit

    def ajouter_conditionnement(self, commande: AjouterConditionnement) -> ProduitConditionnement:
        produit = self._produit_obligatoire(commande.produit_id)
        code = commande.code.strip() or self._generer_code_article()
        conditionnement = produit.ajouter_conditionnement(
            code=code,
            libelle=commande.libelle,
            prix_vente=commande.prix_vente,
        )
        self._depot.enregistrer_produit(produit)
        return conditionnement

    def lister_produits(self) -> tuple[Produit, ...]:
        return self._depot.lister_produits()

    def reinitialiser_catalogue(self) -> int:
        return self._depot.reinitialiser_catalogue()

    def modifier_produit(self, commande: ModifierProduit) -> Produit:
        produit = self._produit_obligatoire(commande.produit_id)
        produit_existant = self._depot.obtenir_produit_par_reference(commande.reference)
        if produit_existant is not None and produit_existant.id != produit.id:
            raise DomainError("Cette référence produit existe déjà.")
        produit_cip = (
            self._depot.obtenir_produit_par_cip7(commande.cip7) if commande.cip7.strip() else None
        )
        if produit_cip is not None and produit_cip.id != produit.id:
            raise DomainError("Ce CIP7 existe déjà.")
        produit.modifier_identite(
            reference=commande.reference,
            designation=commande.designation,
            cip7=commande.cip7,
        )
        produit.modifier_couverture_cnamgs(
            pris_en_charge=commande.pris_en_charge_cnamgs,
            taux=commande.taux_prise_en_charge_cnamgs,
        )
        if isinstance(produit, Medicament):
            principe = self._resoudre_principe_actif(
                principe_actif_id=commande.principe_actif_id,
                libelle=commande.information,
            )
            produit.modifier_principe_actif(principe)
        elif isinstance(produit, ProduitCosmetique):
            marque = self._resoudre_marque(
                marque_id=commande.marque_id,
                libelle=commande.information,
            )
            produit.modifier_marque(marque)
        self._depot.enregistrer_produit(produit)
        return produit

    def modifier_conditionnement(self, commande: ModifierConditionnement) -> ProduitConditionnement:
        for produit in self._depot.lister_produits():
            conditionnement = next(
                (
                    item
                    for item in produit.conditionnements
                    if item.id == commande.conditionnement_id
                ),
                None,
            )
            if conditionnement is None:
                continue
            if any(
                item.id != conditionnement.id and item.code == commande.code.strip()
                for item in produit.conditionnements
            ):
                raise DomainError(
                    f"Le conditionnement {commande.code!r} existe déjà pour ce produit."
                )
            conditionnement.modifier(
                code=commande.code,
                libelle=commande.libelle,
                prix_vente=commande.prix_vente,
            )
            self._depot.enregistrer_produit(produit)
            return conditionnement
        raise DomainError("Le conditionnement est inconnu.")

    def initialiser_principes_actifs(self) -> None:
        for libelle in PRINCIPES_ACTIFS_INITIAUX:
            if self._depot.obtenir_principe_actif_par_libelle(libelle) is None:
                self._depot.enregistrer_principe_actif(PrincipeActif(libelle=libelle))

    def creer_principe_actif(self, libelle: str) -> PrincipeActif:
        existant = self._depot.obtenir_principe_actif_par_libelle(libelle)
        if existant is not None:
            return existant
        principe = PrincipeActif(libelle=libelle)
        self._depot.enregistrer_principe_actif(principe)
        return principe

    def lister_principes_actifs(self) -> tuple[PrincipeActif, ...]:
        return self._depot.lister_principes_actifs()

    def initialiser_marques(self) -> None:
        for libelle in MARQUES_INITIALES:
            if self._depot.obtenir_marque_par_libelle(libelle) is None:
                self._depot.enregistrer_marque(Marque(libelle=libelle))

    def creer_marque(self, libelle: str) -> Marque:
        existante = self._depot.obtenir_marque_par_libelle(libelle)
        if existante is not None:
            return existante
        marque = Marque(libelle=libelle)
        self._depot.enregistrer_marque(marque)
        return marque

    def lister_marques(self) -> tuple[Marque, ...]:
        return self._depot.lister_marques()

    def creer_fournisseur(self, commande: CreerFournisseur) -> Fournisseur:
        code = commande.code.strip() or self._generer_code_fournisseur()
        if self._depot.obtenir_fournisseur_par_code(code) is not None:
            raise DomainError("Ce code fournisseur existe déjà.")
        fournisseur = Fournisseur(
            code=code,
            raison_sociale=commande.raison_sociale,
            telephone=commande.telephone,
            email=commande.email,
        )
        self._depot.enregistrer_fournisseur(fournisseur)
        return fournisseur

    def modifier_fournisseur(self, commande: ModifierFournisseur) -> Fournisseur:
        fournisseur = self._depot.obtenir_fournisseur(commande.fournisseur_id)
        if fournisseur is None:
            raise DomainError("Le fournisseur est inconnu.")
        existant = self._depot.obtenir_fournisseur_par_code(commande.code)
        if existant is not None and existant.id != fournisseur.id:
            raise DomainError("Ce code fournisseur existe déjà.")
        fournisseur.modifier(
            code=commande.code,
            raison_sociale=commande.raison_sociale,
            telephone=commande.telephone,
            email=commande.email,
            actif=commande.actif,
        )
        self._depot.enregistrer_fournisseur(fournisseur)
        return fournisseur

    def lister_fournisseurs(self) -> tuple[Fournisseur, ...]:
        return self._depot.lister_fournisseurs()

    def definir_tarif_fournisseur(self, commande: DefinirTarifFournisseur) -> TarifFournisseur:
        if self._depot.obtenir_fournisseur(commande.fournisseur_id) is None:
            raise DomainError("Le fournisseur est inconnu.")
        if self._depot.obtenir_conditionnement(commande.conditionnement_id) is None:
            raise DomainError("Le conditionnement est inconnu.")
        tarif = self._depot.obtenir_tarif_fournisseur(
            fournisseur_id=commande.fournisseur_id,
            conditionnement_id=commande.conditionnement_id,
        )
        if tarif is None:
            tarif = TarifFournisseur(
                fournisseur_id=commande.fournisseur_id,
                conditionnement_id=commande.conditionnement_id,
                prix_achat=commande.prix_achat,
                reference_fournisseur=commande.reference_fournisseur,
            )
        else:
            tarif.modifier(
                prix_achat=commande.prix_achat,
                reference_fournisseur=commande.reference_fournisseur,
            )
        self._depot.enregistrer_tarif_fournisseur(tarif)
        return tarif

    def lister_tarifs_fournisseurs(self) -> tuple[TarifFournisseur, ...]:
        return self._depot.lister_tarifs_fournisseurs()

    def creer_organisme(self, commande: CreerOrganismePriseEnCharge) -> OrganismePriseEnCharge:
        code = commande.code.strip() or self._generer_code_organisme()
        if self._depot.obtenir_organisme_par_code(code) is not None:
            raise DomainError("Ce code organisme existe déjà.")
        organisme = OrganismePriseEnCharge(
            code=code,
            nom=commande.nom,
            type_organisme=commande.type_organisme,
            documents_requis=commande.documents_requis,
            taux_prise_en_charge=commande.taux_prise_en_charge,
        )
        self._depot.enregistrer_organisme(organisme)
        return organisme

    def lister_organismes(self) -> tuple[OrganismePriseEnCharge, ...]:
        return self._depot.lister_organismes()

    def modifier_organisme(
        self, commande: ModifierOrganismePriseEnCharge
    ) -> OrganismePriseEnCharge:
        organisme = self._depot.obtenir_organisme(commande.organisme_id)
        if organisme is None:
            raise DomainError("L'organisme est inconnu.")
        existant = self._depot.obtenir_organisme_par_code(commande.code)
        if existant is not None and existant.id != organisme.id:
            raise DomainError("Ce code organisme existe déjà.")
        organisme.modifier(
            code=commande.code,
            nom=commande.nom,
            type_organisme=commande.type_organisme,
            documents_requis=commande.documents_requis,
            taux_prise_en_charge=commande.taux_prise_en_charge,
            actif=commande.actif,
        )
        self._depot.enregistrer_organisme(organisme)
        return organisme

    def _produit_obligatoire(self, produit_id: UUID) -> Produit:
        produit = self._depot.obtenir_produit(produit_id)
        if produit is None:
            raise DomainError("Le produit est inconnu.")
        return produit

    def _verifier_reference_unique(self, reference: str) -> None:
        if self._depot.obtenir_produit_par_reference(reference) is not None:
            raise DomainError("Cette référence produit existe déjà.")

    def _verifier_cip7_unique(self, cip7: str) -> None:
        if cip7.strip() and self._depot.obtenir_produit_par_cip7(cip7) is not None:
            raise DomainError("Ce CIP7 existe déjà.")

    def _generer_reference(self, prefixe: str) -> str:
        index = len(self._depot.lister_produits()) + 1
        while self._depot.obtenir_produit_par_reference(f"{prefixe}-{index:05d}"):
            index += 1
        return f"{prefixe}-{index:05d}"

    def _generer_code_article(self) -> str:
        total = sum(len(item.conditionnements) for item in self._depot.lister_produits())
        return f"ART-{total + 1:06d}"

    def _generer_code_fournisseur(self) -> str:
        index = len(self._depot.lister_fournisseurs()) + 1
        while self._depot.obtenir_fournisseur_par_code(f"FOUR-{index:04d}"):
            index += 1
        return f"FOUR-{index:04d}"

    def _generer_code_organisme(self) -> str:
        index = len(self._depot.lister_organismes()) + 1
        while self._depot.obtenir_organisme_par_code(f"ORG-{index:04d}"):
            index += 1
        return f"ORG-{index:04d}"

    def _resoudre_principe_actif(
        self, *, principe_actif_id: UUID | None, libelle: str
    ) -> PrincipeActif:
        if principe_actif_id is not None:
            principe = self._depot.obtenir_principe_actif(principe_actif_id)
            if principe is None:
                raise DomainError("Le principe actif est inconnu.")
            return principe
        return self.creer_principe_actif(libelle)

    def _resoudre_marque(self, *, marque_id: UUID | None, libelle: str) -> Marque:
        if marque_id is not None:
            marque = self._depot.obtenir_marque(marque_id)
            if marque is None:
                raise DomainError("La marque est inconnue.")
            return marque
        return self.creer_marque(libelle)


class StockService:
    def __init__(
        self,
        depot: StockRepository,
        inventaire: Inventaire,
        catalogue: CatalogueRepository | None = None,
    ) -> None:
        self._depot = depot
        self._inventaire = inventaire
        self._catalogue = catalogue

    def creer_emplacement(
        self, *, code: str, libelle: str, autorise_vente: bool = True
    ) -> Emplacement:
        emplacement = Emplacement(
            code=code,
            libelle=libelle,
            autorise_vente=autorise_vente,
        )
        self._inventaire.ajouter_emplacement(emplacement)
        self._depot.enregistrer_emplacement(emplacement)
        return emplacement

    def receptionner_lot(self, commande: ReceptionnerLot) -> Lot:
        self._emplacement_obligatoire(commande.emplacement_id)
        if (
            self._catalogue is not None
            and self._catalogue.obtenir_conditionnement(commande.conditionnement_id) is None
        ):
            raise DomainError("Le conditionnement est inconnu.")
        lot = Lot(
            conditionnement_id=commande.conditionnement_id,
            numero=commande.numero_lot,
            date_expiration=commande.date_expiration,
        )
        self._inventaire.ajouter_lot(lot)
        self._depot.enregistrer_lot(lot)
        mouvement = self._inventaire.receptionner(
            lot_id=lot.id,
            emplacement_id=commande.emplacement_id,
            quantite=commande.quantite,
            motif=commande.motif,
        )
        self._persister_operation(
            lot_id=lot.id,
            emplacement_ids=(commande.emplacement_id,),
            mouvements=(mouvement,),
        )
        return lot

    def transferer(self, commande: TransfererStock) -> tuple[MouvementStock, ...]:
        mouvements = self._inventaire.transferer(
            lot_id=commande.lot_id,
            source_id=commande.source_id,
            destination_id=commande.destination_id,
            quantite=commande.quantite,
            motif=commande.motif,
        )
        self._persister_operation(
            lot_id=commande.lot_id,
            emplacement_ids=(commande.source_id, commande.destination_id),
            mouvements=mouvements,
        )
        return mouvements

    def ajuster(self, commande: AjusterStock) -> MouvementStock | None:
        mouvement = self._inventaire.ajuster_inventaire(
            lot_id=commande.lot_id,
            emplacement_id=commande.emplacement_id,
            nouvelle_quantite=commande.nouvelle_quantite,
            motif=commande.motif,
        )
        mouvements = () if mouvement is None else (mouvement,)
        self._persister_operation(
            lot_id=commande.lot_id,
            emplacement_ids=(commande.emplacement_id,),
            mouvements=mouvements,
        )
        return mouvement

    def consulter_stock(
        self, *, conditionnement_id: UUID, emplacement_id: UUID
    ) -> tuple[LigneEtatStock, ...]:
        self._emplacement_obligatoire(emplacement_id)
        lignes: list[LigneEtatStock] = []
        for position in self._depot.lister_positions(
            conditionnement_id=conditionnement_id,
            emplacement_id=emplacement_id,
        ):
            lot = self._depot.obtenir_lot(position.lot_id)
            if lot is None:
                raise DomainError("Une position de stock référence un lot inconnu.")
            lignes.append(
                LigneEtatStock(
                    lot_id=lot.id,
                    numero_lot=lot.numero,
                    date_expiration=lot.date_expiration,
                    emplacement_id=emplacement_id,
                    quantite_physique=position.quantite_physique,
                    quantite_reservee=position.quantite_reservee,
                    quantite_disponible=position.quantite_disponible,
                    etat_lot=lot.etat.value,
                )
            )
        return tuple(sorted(lignes, key=lambda ligne: (ligne.date_expiration, ligne.numero_lot)))

    def lister_emplacements(self) -> tuple[Emplacement, ...]:
        return self._depot.lister_emplacements()

    def lister_etat_stock(self) -> tuple[LigneEtatStockGlobal, ...]:
        lignes: list[LigneEtatStockGlobal] = []
        for position in self._depot.lister_toutes_positions():
            lot = self._depot.obtenir_lot(position.lot_id)
            if lot is None:
                raise DomainError("Une position de stock référence un lot inconnu.")
            lignes.append(
                LigneEtatStockGlobal(
                    lot_id=lot.id,
                    conditionnement_id=lot.conditionnement_id,
                    numero_lot=lot.numero,
                    date_expiration=lot.date_expiration,
                    emplacement_id=position.emplacement_id,
                    quantite_physique=position.quantite_physique,
                    quantite_reservee=position.quantite_reservee,
                    quantite_disponible=position.quantite_disponible,
                    etat_lot=lot.etat.value,
                )
            )
        return tuple(
            sorted(
                lignes,
                key=lambda ligne: (
                    ligne.date_expiration,
                    ligne.numero_lot,
                    str(ligne.emplacement_id),
                ),
            )
        )

    def reserver_fefo(
        self,
        *,
        conditionnement_id: UUID,
        emplacement_id: UUID,
        quantite: int,
        au: date,
        motif: str,
    ) -> tuple[AllocationFefo, ...]:
        allocations = self._inventaire.reserver_fefo(
            conditionnement_id=conditionnement_id,
            emplacement_id=emplacement_id,
            quantite=quantite,
            au=au,
            motif=motif,
        )
        for allocation in allocations:
            mouvements = tuple(
                mouvement
                for mouvement in self._inventaire.mouvements
                if mouvement.lot_id == allocation.lot_id
                and mouvement.type.value == "reservation"
                and mouvement.motif == motif
            )
            self._persister_operation(
                lot_id=allocation.lot_id,
                emplacement_ids=(emplacement_id,),
                mouvements=(mouvements[-1],),
            )
        return allocations

    def liberer_reservations(
        self,
        *,
        allocations: tuple[AllocationFefo, ...],
        emplacement_id: UUID,
        motif: str,
    ) -> None:
        mouvements = self._inventaire.liberer_reservations(
            allocations=allocations,
            emplacement_id=emplacement_id,
            motif=motif,
        )
        for allocation, mouvement in zip(allocations, mouvements, strict=True):
            self._persister_operation(
                lot_id=allocation.lot_id,
                emplacement_ids=(emplacement_id,),
                mouvements=(mouvement,),
            )

    def confirmer_sortie(
        self,
        *,
        allocations: tuple[AllocationFefo, ...],
        emplacement_id: UUID,
        motif: str,
    ) -> None:
        mouvements = self._inventaire.confirmer_sortie(
            allocations=allocations,
            emplacement_id=emplacement_id,
            motif=motif,
        )
        for allocation, mouvement in zip(allocations, mouvements, strict=True):
            self._persister_operation(
                lot_id=allocation.lot_id,
                emplacement_ids=(emplacement_id,),
                mouvements=(mouvement,),
            )

    def emplacement_existe(self, emplacement_id: UUID) -> bool:
        return self._depot.obtenir_emplacement(emplacement_id) is not None

    def _emplacement_obligatoire(self, emplacement_id: UUID) -> Emplacement:
        emplacement = self._depot.obtenir_emplacement(emplacement_id)
        if emplacement is None:
            raise DomainError("L'emplacement est inconnu.")
        return emplacement

    def _persister_operation(
        self,
        *,
        lot_id: UUID,
        emplacement_ids: tuple[UUID, ...],
        mouvements: tuple[MouvementStock, ...],
    ) -> None:
        for emplacement_id in emplacement_ids:
            self._depot.enregistrer_position(self._inventaire.stock(lot_id, emplacement_id))
        for mouvement in mouvements:
            self._depot.enregistrer_mouvement(mouvement)


class AchatService:
    def __init__(
        self,
        depot: CatalogueRepository,
        catalogue: CatalogueService,
        stock: StockService,
    ) -> None:
        self._depot = depot
        self._catalogue = catalogue
        self._stock = stock

    def creer_commande_reception(self, commande: CreerCommandeReception) -> CommandeAchat:
        if self._depot.obtenir_fournisseur(commande.fournisseur_id) is None:
            raise DomainError("Le fournisseur est inconnu.")
        if not self._stock.emplacement_existe(commande.emplacement_id):
            raise DomainError("L'emplacement est inconnu.")
        produits = self._depot.lister_produits()
        lignes: list[LigneCommandeAchat] = []
        for saisie in commande.lignes:
            article = self._depot.obtenir_conditionnement(saisie.conditionnement_id)
            if article is None:
                raise DomainError("Un conditionnement est inconnu.")
            produit = next(item for item in produits if item.id == article.produit_id)
            lignes.append(
                LigneCommandeAchat(
                    conditionnement_id=article.id,
                    designation=f"{produit.designation} — {article.libelle}",
                    cip7=produit.cip7,
                    quantite_commandee=saisie.quantite_commandee,
                    quantite_recue=saisie.quantite_recue,
                    numero_lot=saisie.numero_lot,
                    date_expiration=saisie.date_expiration,
                    prix_unitaire=saisie.prix_unitaire,
                )
            )
        numero = (
            f"CMD-{commande.date_commande:%Y}-{len(self._depot.lister_commandes_achat()) + 1:05d}"
        )
        achat = CommandeAchat(
            numero_interne=numero,
            fournisseur_id=commande.fournisseur_id,
            emplacement_id=commande.emplacement_id,
            date_commande=commande.date_commande,
            date_arrivee=commande.date_arrivee,
            numero_fournisseur=commande.numero_fournisseur,
            lignes=lignes,
        )
        for ligne in lignes:
            self._catalogue.definir_tarif_fournisseur(
                DefinirTarifFournisseur(
                    fournisseur_id=commande.fournisseur_id,
                    conditionnement_id=ligne.conditionnement_id,
                    prix_achat=ligne.prix_unitaire,
                )
            )
            if ligne.quantite_recue:
                self._stock.receptionner_lot(
                    ReceptionnerLot(
                        conditionnement_id=ligne.conditionnement_id,
                        numero_lot=ligne.numero_lot,
                        date_expiration=ligne.date_expiration,
                        emplacement_id=commande.emplacement_id,
                        quantite=ligne.quantite_recue,
                        motif=f"Réception {numero}",
                    )
                )
        self._depot.enregistrer_commande_achat(achat)
        return achat

    def lister_commandes(self) -> tuple[CommandeAchat, ...]:
        return self._depot.lister_commandes_achat()
