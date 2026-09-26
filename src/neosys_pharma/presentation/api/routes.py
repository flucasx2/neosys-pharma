import csv
import io
from dataclasses import asdict
from decimal import Decimal, InvalidOperation
from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status

from neosys_pharma.application.administration_service import AdministrationService
from neosys_pharma.application.dto import (
    AjouterConditionnement,
    AjouterLigneVente,
    AjusterStock,
    CreerCommandeReception,
    CreerFournisseur,
    CreerMedicament,
    CreerOrganismePriseEnCharge,
    CreerPosteVente,
    CreerProduitCosmetique,
    DefinirTarifFournisseur,
    LigneCommandeReception,
    ModifierConditionnement,
    ModifierFournisseur,
    ModifierOrganismePriseEnCharge,
    ModifierProduit,
    ReceptionnerLot,
    TransfererStock,
)
from neosys_pharma.application.fidelite_service import FideliteService
from neosys_pharma.application.services import AchatService, CatalogueService, StockService
from neosys_pharma.application.vente_service import VenteService
from neosys_pharma.domain.administration import CompteOperation
from neosys_pharma.domain.catalogue import (
    CarteFidelite,
    ClientFidelite,
    CommandeAchat,
    Medicament,
    ProduitCosmetique,
)
from neosys_pharma.domain.shared import DomainError
from neosys_pharma.domain.vente import Vente
from neosys_pharma.presentation.api.container import ApplicationContainer
from neosys_pharma.presentation.api.schemas import (
    AjustementCreate,
    AllocationLotResponse,
    ArticleCatalogueResponse,
    CaisseCreate,
    CaisseResponse,
    CarteFideliteCreate,
    CarteFideliteLookupResponse,
    CarteFideliteResponse,
    CarteFideliteUpdate,
    CatalogueFournisseurImport,
    CatalogueFournisseurImportResponse,
    ClientFideliteCreate,
    ClientFideliteResponse,
    ClientFideliteUpdate,
    CommandeReceptionCreate,
    CommandeReceptionResponse,
    CompteOperationCreate,
    CompteOperationResponse,
    CompteOperationUpdate,
    ConditionnementCreate,
    ConditionnementResponse,
    ConditionnementUpdate,
    CosmetiqueCreate,
    EmplacementCreate,
    EmplacementResponse,
    EncaissementCreate,
    FournisseurCreate,
    FournisseurResponse,
    FournisseurUpdate,
    HealthResponse,
    LigneCommandeReceptionResponse,
    LigneStockGlobalResponse,
    LigneStockResponse,
    LigneVenteCreate,
    LigneVenteResponse,
    LotResponse,
    MarqueCreate,
    MarqueResponse,
    MedicamentCreate,
    MouvementFideliteCreate,
    MouvementFideliteResponse,
    MouvementResponse,
    OrganismePriseEnChargeCreate,
    OrganismePriseEnChargeResponse,
    OrganismePriseEnChargeUpdate,
    PosteVenteCreate,
    PosteVenteResponse,
    PrincipeActifCreate,
    PrincipeActifResponse,
    ProduitDetailResponse,
    ProduitResponse,
    ProduitUpdate,
    ReceptionLotCreate,
    TarifFournisseurCreate,
    TarifFournisseurResponse,
    TransfertCreate,
    VenteCreate,
    VenteResponse,
)

router = APIRouter(prefix="/api/v1")


def get_container(request: Request) -> ApplicationContainer:
    return cast(ApplicationContainer, request.app.state.container)


def get_catalogue(
    container: Annotated[ApplicationContainer, Depends(get_container)],
) -> CatalogueService:
    return container.catalogue


def get_stock(
    container: Annotated[ApplicationContainer, Depends(get_container)],
) -> StockService:
    return container.stock


def get_ventes(
    container: Annotated[ApplicationContainer, Depends(get_container)],
) -> VenteService:
    return container.ventes


def get_achats(
    container: Annotated[ApplicationContainer, Depends(get_container)],
) -> AchatService:
    if container.achats is None:
        raise RuntimeError("Le service des achats n'est pas configuré.")
    return container.achats


def get_fidelite(
    container: Annotated[ApplicationContainer, Depends(get_container)],
) -> FideliteService:
    if container.fidelite is None:
        raise RuntimeError("Le service fidélité n'est pas configuré.")
    return container.fidelite


def get_administration(
    container: Annotated[ApplicationContainer, Depends(get_container)],
) -> AdministrationService:
    if container.administration is None:
        raise RuntimeError("Le service administration n'est pas configuré.")
    return container.administration


def vente_response(vente: Vente) -> VenteResponse:
    return VenteResponse(
        id=vente.id,
        numero_ticket=vente.numero_ticket,
        poste_id=vente.poste_id,
        secteur_id=vente.secteur_id,
        emplacement_id=vente.emplacement_id,
        date_commerciale=vente.date_commerciale,
        etat=vente.etat.value,
        montant_total=vente.montant_total,
        montant_a_payer=vente.montant_a_payer,
        organisme_id=vente.organisme_id,
        patient_nom=vente.patient_nom,
        patient_prenom=vente.patient_prenom,
        informations_prise_en_charge=vente.informations_prise_en_charge,
        encaissement_id=vente.encaissement_id,
        reglements=vente.reglements,
        carte_fidelite_id=vente.carte_fidelite_id,
        points_utilises=vente.points_utilises,
        encaissee_le=vente.encaissee_le,
        lignes=[
            LigneVenteResponse(
                id=ligne.id,
                conditionnement_id=ligne.conditionnement_id,
                designation=ligne.designation,
                quantite=ligne.quantite,
                prix_unitaire=ligne.prix_unitaire,
                montant=ligne.montant,
            )
            for ligne in vente.lignes
        ],
        allocations=[
            AllocationLotResponse(
                id=allocation.id,
                ligne_vente_id=allocation.ligne_vente_id,
                lot_id=allocation.lot_id,
                quantite=allocation.quantite,
                date_expiration=allocation.date_expiration,
                emplacement_id=allocation.emplacement_id,
            )
            for allocation in vente.allocations
        ],
    )


@router.get("/health", response_model=HealthResponse, tags=["Système"])
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="NeoSys Pharma API")


@router.post(
    "/catalogue/medicaments",
    response_model=ProduitResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Catalogue"],
)
def creer_medicament(
    payload: MedicamentCreate,
    service: Annotated[CatalogueService, Depends(get_catalogue)],
) -> ProduitResponse:
    produit = service.creer_medicament(CreerMedicament(**payload.model_dump()))
    return ProduitResponse(
        id=produit.id,
        type="medicament",
        reference=produit.reference,
        designation=produit.designation,
    )


@router.post(
    "/catalogue/cosmetiques",
    response_model=ProduitResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Catalogue"],
)
def creer_cosmetique(
    payload: CosmetiqueCreate,
    service: Annotated[CatalogueService, Depends(get_catalogue)],
) -> ProduitResponse:
    produit = service.creer_produit_cosmetique(CreerProduitCosmetique(**payload.model_dump()))
    return ProduitResponse(
        id=produit.id,
        type="cosmetique",
        reference=produit.reference,
        designation=produit.designation,
    )


@router.get(
    "/catalogue/produits",
    response_model=list[ProduitDetailResponse],
    tags=["Catalogue"],
)
def lister_produits(
    service: Annotated[CatalogueService, Depends(get_catalogue)],
) -> list[ProduitDetailResponse]:
    return [
        ProduitDetailResponse(
            id=produit.id,
            type="medicament" if isinstance(produit, Medicament) else "cosmetique",
            reference=produit.reference,
            designation=produit.designation,
            cip7=produit.cip7,
            information=(
                produit.principe_actif
                if isinstance(produit, Medicament)
                else cast(ProduitCosmetique, produit).marque
            ),
            principe_actif_id=(
                produit.principe_actif_id if isinstance(produit, Medicament) else None
            ),
            marque_id=(produit.marque_id if isinstance(produit, ProduitCosmetique) else None),
            pris_en_charge_cnamgs=produit.pris_en_charge_cnamgs,
            taux_prise_en_charge_cnamgs=produit.taux_prise_en_charge_cnamgs,
            conditionnements=[
                ConditionnementResponse(
                    id=item.id,
                    produit_id=item.produit_id,
                    code=item.code,
                    libelle=item.libelle,
                    prix_vente=item.prix_vente,
                )
                for item in produit.conditionnements
            ],
        )
        for produit in service.lister_produits()
    ]


@router.put(
    "/catalogue/produits/{produit_id}",
    response_model=ProduitDetailResponse,
    tags=["Catalogue"],
)
def modifier_produit(
    produit_id: UUID,
    payload: ProduitUpdate,
    service: Annotated[CatalogueService, Depends(get_catalogue)],
) -> ProduitDetailResponse:
    produit = service.modifier_produit(
        ModifierProduit(produit_id=produit_id, **payload.model_dump())
    )
    return ProduitDetailResponse(
        id=produit.id,
        type="medicament" if isinstance(produit, Medicament) else "cosmetique",
        reference=produit.reference,
        designation=produit.designation,
        cip7=produit.cip7,
        information=(
            produit.principe_actif
            if isinstance(produit, Medicament)
            else cast(ProduitCosmetique, produit).marque
        ),
        principe_actif_id=(produit.principe_actif_id if isinstance(produit, Medicament) else None),
        marque_id=(produit.marque_id if isinstance(produit, ProduitCosmetique) else None),
        pris_en_charge_cnamgs=produit.pris_en_charge_cnamgs,
        taux_prise_en_charge_cnamgs=produit.taux_prise_en_charge_cnamgs,
        conditionnements=[
            ConditionnementResponse(
                id=item.id,
                produit_id=item.produit_id,
                code=item.code,
                libelle=item.libelle,
                prix_vente=item.prix_vente,
            )
            for item in produit.conditionnements
        ],
    )


@router.post(
    "/catalogue/produits/{produit_id}/conditionnements",
    response_model=ConditionnementResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Catalogue"],
)
def ajouter_conditionnement(
    produit_id: UUID,
    payload: ConditionnementCreate,
    service: Annotated[CatalogueService, Depends(get_catalogue)],
) -> ConditionnementResponse:
    conditionnement = service.ajouter_conditionnement(
        AjouterConditionnement(produit_id=produit_id, **payload.model_dump())
    )
    return ConditionnementResponse(
        id=conditionnement.id,
        produit_id=conditionnement.produit_id,
        code=conditionnement.code,
        libelle=conditionnement.libelle,
        prix_vente=conditionnement.prix_vente,
    )


@router.put(
    "/catalogue/conditionnements/{conditionnement_id}",
    response_model=ConditionnementResponse,
    tags=["Catalogue"],
)
def modifier_conditionnement(
    conditionnement_id: UUID,
    payload: ConditionnementUpdate,
    service: Annotated[CatalogueService, Depends(get_catalogue)],
) -> ConditionnementResponse:
    conditionnement = service.modifier_conditionnement(
        ModifierConditionnement(
            conditionnement_id=conditionnement_id,
            **payload.model_dump(),
        )
    )
    return ConditionnementResponse(
        id=conditionnement.id,
        produit_id=conditionnement.produit_id,
        code=conditionnement.code,
        libelle=conditionnement.libelle,
        prix_vente=conditionnement.prix_vente,
    )


@router.get(
    "/catalogue/principes-actifs",
    response_model=list[PrincipeActifResponse],
    tags=["Catalogue"],
)
def lister_principes_actifs(
    service: Annotated[CatalogueService, Depends(get_catalogue)],
) -> list[PrincipeActifResponse]:
    return [
        PrincipeActifResponse(id=principe.id, libelle=principe.libelle)
        for principe in service.lister_principes_actifs()
    ]


@router.post(
    "/catalogue/principes-actifs",
    response_model=PrincipeActifResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Catalogue"],
)
def creer_principe_actif(
    payload: PrincipeActifCreate,
    service: Annotated[CatalogueService, Depends(get_catalogue)],
) -> PrincipeActifResponse:
    principe = service.creer_principe_actif(payload.libelle)
    return PrincipeActifResponse(id=principe.id, libelle=principe.libelle)


@router.get(
    "/catalogue/marques",
    response_model=list[MarqueResponse],
    tags=["Catalogue"],
)
def lister_marques(
    service: Annotated[CatalogueService, Depends(get_catalogue)],
) -> list[MarqueResponse]:
    return [MarqueResponse(id=item.id, libelle=item.libelle) for item in service.lister_marques()]


@router.post(
    "/catalogue/marques",
    response_model=MarqueResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Catalogue"],
)
def creer_marque(
    payload: MarqueCreate,
    service: Annotated[CatalogueService, Depends(get_catalogue)],
) -> MarqueResponse:
    item = service.creer_marque(payload.libelle)
    return MarqueResponse(id=item.id, libelle=item.libelle)


@router.get(
    "/prises-en-charge/organismes",
    response_model=list[OrganismePriseEnChargeResponse],
    tags=["Prises en charge"],
)
def lister_organismes(
    service: Annotated[CatalogueService, Depends(get_catalogue)],
) -> list[OrganismePriseEnChargeResponse]:
    return [
        OrganismePriseEnChargeResponse(
            id=item.id,
            code=item.code,
            nom=item.nom,
            type_organisme=item.type_organisme,
            documents_requis=list(item.documents_requis),
            actif=item.actif,
            taux_prise_en_charge=item.taux_prise_en_charge,
        )
        for item in service.lister_organismes()
    ]


@router.post(
    "/prises-en-charge/organismes",
    response_model=OrganismePriseEnChargeResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Prises en charge"],
)
def creer_organisme(
    payload: OrganismePriseEnChargeCreate,
    service: Annotated[CatalogueService, Depends(get_catalogue)],
) -> OrganismePriseEnChargeResponse:
    item = service.creer_organisme(
        CreerOrganismePriseEnCharge(
            code=payload.code,
            nom=payload.nom,
            type_organisme=payload.type_organisme,
            documents_requis=tuple(payload.documents_requis),
            taux_prise_en_charge=payload.taux_prise_en_charge,
        )
    )
    return OrganismePriseEnChargeResponse(
        id=item.id,
        code=item.code,
        nom=item.nom,
        type_organisme=item.type_organisme,
        documents_requis=list(item.documents_requis),
        actif=item.actif,
        taux_prise_en_charge=item.taux_prise_en_charge,
    )


@router.put(
    "/prises-en-charge/organismes/{organisme_id}",
    response_model=OrganismePriseEnChargeResponse,
    tags=["Prises en charge"],
)
def modifier_organisme(
    organisme_id: UUID,
    payload: OrganismePriseEnChargeUpdate,
    service: Annotated[CatalogueService, Depends(get_catalogue)],
) -> OrganismePriseEnChargeResponse:
    item = service.modifier_organisme(
        ModifierOrganismePriseEnCharge(
            organisme_id=organisme_id,
            code=payload.code,
            nom=payload.nom,
            type_organisme=payload.type_organisme,
            documents_requis=tuple(payload.documents_requis),
            actif=payload.actif,
            taux_prise_en_charge=payload.taux_prise_en_charge,
        )
    )
    return OrganismePriseEnChargeResponse(
        id=item.id,
        code=item.code,
        nom=item.nom,
        type_organisme=item.type_organisme,
        documents_requis=list(item.documents_requis),
        actif=item.actif,
        taux_prise_en_charge=item.taux_prise_en_charge,
    )


@router.get(
    "/achats/fournisseurs",
    response_model=list[FournisseurResponse],
    tags=["Achats"],
)
def lister_fournisseurs(
    service: Annotated[CatalogueService, Depends(get_catalogue)],
) -> list[FournisseurResponse]:
    return [
        FournisseurResponse(
            id=item.id,
            code=item.code,
            raison_sociale=item.raison_sociale,
            telephone=item.telephone,
            email=item.email,
            actif=item.actif,
        )
        for item in service.lister_fournisseurs()
    ]


@router.post(
    "/achats/fournisseurs",
    response_model=FournisseurResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Achats"],
)
def creer_fournisseur(
    payload: FournisseurCreate,
    service: Annotated[CatalogueService, Depends(get_catalogue)],
) -> FournisseurResponse:
    item = service.creer_fournisseur(CreerFournisseur(**payload.model_dump()))
    return FournisseurResponse(
        id=item.id,
        code=item.code,
        raison_sociale=item.raison_sociale,
        telephone=item.telephone,
        email=item.email,
        actif=item.actif,
    )


@router.put(
    "/achats/fournisseurs/{fournisseur_id}",
    response_model=FournisseurResponse,
    tags=["Achats"],
)
def modifier_fournisseur(
    fournisseur_id: UUID,
    payload: FournisseurUpdate,
    service: Annotated[CatalogueService, Depends(get_catalogue)],
) -> FournisseurResponse:
    item = service.modifier_fournisseur(
        ModifierFournisseur(fournisseur_id=fournisseur_id, **payload.model_dump())
    )
    return FournisseurResponse(
        id=item.id,
        code=item.code,
        raison_sociale=item.raison_sociale,
        telephone=item.telephone,
        email=item.email,
        actif=item.actif,
    )


@router.post(
    "/achats/catalogues/import",
    response_model=CatalogueFournisseurImportResponse,
    tags=["Achats"],
)
def importer_catalogue_fournisseur(
    payload: CatalogueFournisseurImport,
    catalogue: Annotated[CatalogueService, Depends(get_catalogue)],
) -> CatalogueFournisseurImportResponse:
    fournisseur = next(
        (item for item in catalogue.lister_fournisseurs() if item.id == payload.fournisseur_id),
        None,
    )
    if fournisseur is None:
        raise DomainError("Le fournisseur doit exister avant l'import du catalogue.")

    reader = csv.DictReader(io.StringIO(payload.contenu_csv.lstrip("\ufeff")), delimiter=";")
    colonnes = set(reader.fieldnames or [])
    attendues = {"CIP", "Description", "DCI", "PrixAchat", "PrixVente"}
    if not attendues.issubset(colonnes):
        manquantes = ", ".join(sorted(attendues - colonnes))
        raise DomainError(f"Colonnes manquantes dans le fichier : {manquantes}.")

    lignes: list[tuple[int, str, str, str, Decimal, Decimal]] = []
    erreurs: list[str] = []
    lignes_lues = lignes_ignorees = 0
    for numero, row in enumerate(reader, start=2):
        lignes_lues += 1
        cip7 = (row.get("CIP") or "").strip()
        designation = (row.get("Description") or "").strip()
        dci = (row.get("DCI") or "").strip()
        try:
            prix_achat = Decimal((row.get("PrixAchat") or "").strip().replace(",", "."))
            prix_vente = Decimal((row.get("PrixVente") or "").strip().replace(",", "."))
        except InvalidOperation:
            prix_achat = prix_vente = Decimal("0")
        if (
            len(cip7) != 7
            or not cip7.isdigit()
            or not designation
            or prix_achat <= 0
            or prix_vente <= 0
        ):
            lignes_ignorees += 1
            if len(erreurs) < 20:
                erreurs.append(f"Ligne {numero}: CIP7, désignation ou prix invalide.")
            continue
        lignes.append((numero, cip7, designation, dci, prix_achat, prix_vente))
    if not lignes:
        raise DomainError("Le fichier ne contient aucune ligne de catalogue valide.")
    if payload.mode == "MISE_EN_PLACE" and not payload.confirmer_mise_en_place:
        raise DomainError("La confirmation de mise en place est obligatoire.")

    produits_supprimes = (
        catalogue.reinitialiser_catalogue() if payload.mode == "MISE_EN_PLACE" else 0
    )
    produits_crees = produits_mis_a_jour = tarifs_enregistres = 0
    produits_par_cip = {item.cip7: item for item in catalogue.lister_produits() if item.cip7}
    for numero, cip7, designation, dci, prix_achat, prix_vente in lignes:
        produit = produits_par_cip.get(cip7)
        try:
            if produit is None:
                if payload.mode == "MISE_A_JOUR_TARIFS":
                    lignes_ignorees += 1
                    continue
                if dci:
                    produit = catalogue.creer_medicament(
                        CreerMedicament(designation=designation, cip7=cip7, principe_actif=dci)
                    )
                else:
                    produit = catalogue.creer_produit_cosmetique(
                        CreerProduitCosmetique(
                            designation=designation, cip7=cip7, marque=fournisseur.raison_sociale
                        )
                    )
                conditionnement = catalogue.ajouter_conditionnement(
                    AjouterConditionnement(
                        produit_id=produit.id,
                        libelle="UNITÉ / CONDITIONNEMENT FOURNISSEUR",
                        prix_vente=prix_vente,
                    )
                )
                produits_crees += 1
                produits_par_cip[cip7] = produit
            else:
                conditionnement = (
                    produit.conditionnements[0]
                    if produit.conditionnements
                    else catalogue.ajouter_conditionnement(
                        AjouterConditionnement(
                            produit_id=produit.id,
                            libelle="UNITÉ / CONDITIONNEMENT FOURNISSEUR",
                            prix_vente=prix_vente,
                        )
                    )
                )
                catalogue.modifier_conditionnement(
                    ModifierConditionnement(
                        conditionnement_id=conditionnement.id,
                        code=conditionnement.code,
                        libelle=conditionnement.libelle,
                        prix_vente=prix_vente,
                    )
                )
                if payload.mode == "MISE_A_JOUR_TARIFS":
                    information = (
                        produit.principe_actif
                        if isinstance(produit, Medicament)
                        else cast(ProduitCosmetique, produit).marque
                    )
                    catalogue.modifier_produit(
                        ModifierProduit(
                            produit_id=produit.id,
                            reference=produit.reference,
                            designation=designation,
                            cip7=cip7,
                            information=information,
                            principe_actif_id=(
                                produit.principe_actif_id
                                if isinstance(produit, Medicament)
                                else None
                            ),
                            marque_id=(
                                produit.marque_id
                                if isinstance(produit, ProduitCosmetique)
                                else None
                            ),
                            pris_en_charge_cnamgs=produit.pris_en_charge_cnamgs,
                            taux_prise_en_charge_cnamgs=produit.taux_prise_en_charge_cnamgs,
                        )
                    )
                    produits_mis_a_jour += 1
            catalogue.definir_tarif_fournisseur(
                DefinirTarifFournisseur(
                    fournisseur_id=fournisseur.id,
                    conditionnement_id=conditionnement.id,
                    prix_achat=prix_achat,
                    reference_fournisseur=cip7,
                )
            )
            tarifs_enregistres += 1
        except Exception as exc:
            lignes_ignorees += 1
            if len(erreurs) < 20:
                erreurs.append(f"Ligne {numero}: {exc}")
    return CatalogueFournisseurImportResponse(
        lignes_lues=lignes_lues,
        produits_supprimes=produits_supprimes,
        produits_crees=produits_crees,
        produits_mis_a_jour=produits_mis_a_jour,
        tarifs_enregistres=tarifs_enregistres,
        lignes_ignorees=lignes_ignorees,
        erreurs=erreurs,
    )


@router.get(
    "/achats/tarifs",
    response_model=list[TarifFournisseurResponse],
    tags=["Achats"],
)
def lister_tarifs_fournisseurs(
    service: Annotated[CatalogueService, Depends(get_catalogue)],
) -> list[TarifFournisseurResponse]:
    return [
        TarifFournisseurResponse(
            id=item.id,
            fournisseur_id=item.fournisseur_id,
            conditionnement_id=item.conditionnement_id,
            prix_achat=item.prix_achat,
            reference_fournisseur=item.reference_fournisseur,
        )
        for item in service.lister_tarifs_fournisseurs()
    ]


@router.put(
    "/achats/tarifs",
    response_model=TarifFournisseurResponse,
    tags=["Achats"],
)
def definir_tarif_fournisseur(
    payload: TarifFournisseurCreate,
    service: Annotated[CatalogueService, Depends(get_catalogue)],
) -> TarifFournisseurResponse:
    item = service.definir_tarif_fournisseur(DefinirTarifFournisseur(**payload.model_dump()))
    return TarifFournisseurResponse(
        id=item.id,
        fournisseur_id=item.fournisseur_id,
        conditionnement_id=item.conditionnement_id,
        prix_achat=item.prix_achat,
        reference_fournisseur=item.reference_fournisseur,
    )


def commande_response(commande: CommandeAchat) -> CommandeReceptionResponse:
    return CommandeReceptionResponse(
        id=commande.id,
        numero_interne=commande.numero_interne,
        fournisseur_id=commande.fournisseur_id,
        emplacement_id=commande.emplacement_id,
        date_commande=commande.date_commande,
        date_arrivee=commande.date_arrivee,
        numero_fournisseur=commande.numero_fournisseur,
        total_general=commande.total_general,
        lignes=[
            LigneCommandeReceptionResponse(
                id=ligne.id,
                conditionnement_id=ligne.conditionnement_id,
                designation=ligne.designation,
                cip7=ligne.cip7,
                quantite_commandee=ligne.quantite_commandee,
                quantite_recue=ligne.quantite_recue,
                numero_lot=ligne.numero_lot,
                date_expiration=ligne.date_expiration,
                prix_unitaire=ligne.prix_unitaire,
                total=ligne.total,
            )
            for ligne in commande.lignes
        ],
    )


@router.post(
    "/achats/commandes-receptions",
    response_model=CommandeReceptionResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Achats"],
)
def creer_commande_reception(
    payload: CommandeReceptionCreate,
    service: Annotated[AchatService, Depends(get_achats)],
) -> CommandeReceptionResponse:
    commande = service.creer_commande_reception(
        CreerCommandeReception(
            fournisseur_id=payload.fournisseur_id,
            emplacement_id=payload.emplacement_id,
            date_commande=payload.date_commande,
            date_arrivee=payload.date_arrivee,
            numero_fournisseur=payload.numero_fournisseur,
            lignes=tuple(LigneCommandeReception(**ligne.model_dump()) for ligne in payload.lignes),
        )
    )
    return commande_response(commande)


@router.get(
    "/achats/commandes-receptions",
    response_model=list[CommandeReceptionResponse],
    tags=["Achats"],
)
def lister_commandes_receptions(
    service: Annotated[AchatService, Depends(get_achats)],
) -> list[CommandeReceptionResponse]:
    return [commande_response(item) for item in service.lister_commandes()]


@router.get(
    "/catalogue/articles",
    response_model=list[ArticleCatalogueResponse],
    tags=["Catalogue"],
)
def lister_articles(
    service: Annotated[CatalogueService, Depends(get_catalogue)],
) -> list[ArticleCatalogueResponse]:
    return [
        ArticleCatalogueResponse(
            id=conditionnement.id,
            produit_id=produit.id,
            type_produit=("medicament" if isinstance(produit, Medicament) else "cosmetique"),
            reference=produit.reference,
            designation=produit.designation,
            cip7=produit.cip7,
            code=conditionnement.code,
            libelle=conditionnement.libelle,
            prix_vente=conditionnement.prix_vente,
            pris_en_charge_cnamgs=produit.pris_en_charge_cnamgs,
            taux_prise_en_charge_cnamgs=produit.taux_prise_en_charge_cnamgs,
        )
        for produit in service.lister_produits()
        for conditionnement in produit.conditionnements
    ]


@router.post(
    "/stock/emplacements",
    response_model=EmplacementResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Stock"],
)
def creer_emplacement(
    payload: EmplacementCreate,
    service: Annotated[StockService, Depends(get_stock)],
) -> EmplacementResponse:
    emplacement = service.creer_emplacement(**payload.model_dump())
    return EmplacementResponse(
        id=emplacement.id,
        code=emplacement.code,
        libelle=emplacement.libelle,
        autorise_vente=emplacement.autorise_vente,
    )


@router.get(
    "/stock/emplacements",
    response_model=list[EmplacementResponse],
    tags=["Stock"],
)
def lister_emplacements(
    service: Annotated[StockService, Depends(get_stock)],
) -> list[EmplacementResponse]:
    return [
        EmplacementResponse(
            id=emplacement.id,
            code=emplacement.code,
            libelle=emplacement.libelle,
            autorise_vente=emplacement.autorise_vente,
        )
        for emplacement in service.lister_emplacements()
    ]


@router.post(
    "/stock/receptions",
    response_model=LotResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Stock"],
)
def receptionner_lot(
    payload: ReceptionLotCreate,
    service: Annotated[StockService, Depends(get_stock)],
) -> LotResponse:
    lot = service.receptionner_lot(ReceptionnerLot(**payload.model_dump()))
    return LotResponse(
        id=lot.id,
        conditionnement_id=lot.conditionnement_id,
        numero=lot.numero,
        date_expiration=lot.date_expiration,
        etat=lot.etat.value,
    )


@router.post(
    "/stock/transferts",
    response_model=list[MouvementResponse],
    status_code=status.HTTP_201_CREATED,
    tags=["Stock"],
)
def transferer(
    payload: TransfertCreate,
    service: Annotated[StockService, Depends(get_stock)],
) -> list[MouvementResponse]:
    mouvements = service.transferer(TransfererStock(**payload.model_dump()))
    return [
        MouvementResponse(
            id=mouvement.id,
            type=mouvement.type.value,
            lot_id=mouvement.lot_id,
            quantite=mouvement.quantite,
        )
        for mouvement in mouvements
    ]


@router.post(
    "/stock/ajustements",
    response_model=MouvementResponse | None,
    status_code=status.HTTP_200_OK,
    tags=["Stock"],
)
def ajuster(
    payload: AjustementCreate,
    service: Annotated[StockService, Depends(get_stock)],
) -> MouvementResponse | None:
    mouvement = service.ajuster(AjusterStock(**payload.model_dump()))
    if mouvement is None:
        return None
    return MouvementResponse(
        id=mouvement.id,
        type=mouvement.type.value,
        lot_id=mouvement.lot_id,
        quantite=mouvement.quantite,
    )


@router.get(
    "/stock/conditionnements/{conditionnement_id}/emplacements/{emplacement_id}",
    response_model=list[LigneStockResponse],
    tags=["Stock"],
)
def consulter_stock(
    conditionnement_id: UUID,
    emplacement_id: UUID,
    service: Annotated[StockService, Depends(get_stock)],
) -> list[LigneStockResponse]:
    return [
        LigneStockResponse(**asdict(ligne))
        for ligne in service.consulter_stock(
            conditionnement_id=conditionnement_id,
            emplacement_id=emplacement_id,
        )
    ]


@router.get(
    "/stock/etat",
    response_model=list[LigneStockGlobalResponse],
    tags=["Stock"],
)
def lister_etat_stock(
    service: Annotated[StockService, Depends(get_stock)],
) -> list[LigneStockGlobalResponse]:
    return [LigneStockGlobalResponse(**asdict(ligne)) for ligne in service.lister_etat_stock()]


@router.post(
    "/ventes/postes",
    response_model=PosteVenteResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Ventes"],
)
def creer_poste_vente(
    payload: PosteVenteCreate,
    service: Annotated[VenteService, Depends(get_ventes)],
) -> PosteVenteResponse:
    poste = service.creer_poste(CreerPosteVente(**payload.model_dump()))
    return PosteVenteResponse(
        id=poste.id,
        code=poste.code,
        secteur_id=poste.secteur_id,
        emplacement_id=poste.emplacement_id,
        caisse_id=poste.caisse_id,
    )


@router.get(
    "/ventes/postes",
    response_model=list[PosteVenteResponse],
    tags=["Ventes"],
)
def lister_postes_vente(
    service: Annotated[VenteService, Depends(get_ventes)],
) -> list[PosteVenteResponse]:
    return [
        PosteVenteResponse(
            id=poste.id,
            code=poste.code,
            secteur_id=poste.secteur_id,
            emplacement_id=poste.emplacement_id,
            caisse_id=poste.caisse_id,
        )
        for poste in service.lister_postes()
    ]


@router.post(
    "/ventes",
    response_model=VenteResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Ventes"],
)
def creer_vente(
    payload: VenteCreate,
    service: Annotated[VenteService, Depends(get_ventes)],
) -> VenteResponse:
    return vente_response(service.creer_vente(**payload.model_dump()))


@router.get("/ventes", response_model=list[VenteResponse], tags=["Ventes"])
def lister_ventes(
    service: Annotated[VenteService, Depends(get_ventes)],
    etat: str | None = None,
) -> list[VenteResponse]:
    return [vente_response(item) for item in service.lister(etat)]


@router.post("/ventes/encaissements", response_model=list[VenteResponse], tags=["Ventes"])
def encaisser_ventes(
    payload: EncaissementCreate,
    service: Annotated[VenteService, Depends(get_ventes)],
) -> list[VenteResponse]:
    ventes = service.encaisser(
        vente_ids=payload.vente_ids,
        reglements=[
            {"mode": item.mode, "montant": str(item.montant)} for item in payload.reglements
        ],
        carte_fidelite_id=payload.carte_fidelite_id,
        points_utilises=payload.points_utilises,
    )
    return [vente_response(item) for item in ventes]


@router.post(
    "/ventes/{vente_id}/lignes",
    response_model=LigneVenteResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Ventes"],
)
def ajouter_ligne_vente(
    vente_id: UUID,
    payload: LigneVenteCreate,
    service: Annotated[VenteService, Depends(get_ventes)],
) -> LigneVenteResponse:
    ligne = service.ajouter_ligne(AjouterLigneVente(vente_id=vente_id, **payload.model_dump()))
    return LigneVenteResponse(
        id=ligne.id,
        conditionnement_id=ligne.conditionnement_id,
        designation=ligne.designation,
        quantite=ligne.quantite,
        prix_unitaire=ligne.prix_unitaire,
        montant=ligne.montant,
    )


@router.post(
    "/ventes/{vente_id}/preparation",
    response_model=VenteResponse,
    tags=["Ventes"],
)
def preparer_vente(
    vente_id: UUID,
    service: Annotated[VenteService, Depends(get_ventes)],
) -> VenteResponse:
    return vente_response(service.preparer(vente_id))


@router.post(
    "/ventes/{vente_id}/annulation",
    response_model=VenteResponse,
    tags=["Ventes"],
)
def annuler_vente(
    vente_id: UUID,
    service: Annotated[VenteService, Depends(get_ventes)],
) -> VenteResponse:
    return vente_response(service.annuler(vente_id))


@router.get(
    "/ventes/{vente_id}",
    response_model=VenteResponse,
    tags=["Ventes"],
)
def obtenir_vente(
    vente_id: UUID,
    service: Annotated[VenteService, Depends(get_ventes)],
) -> VenteResponse:
    return vente_response(service.obtenir(vente_id))


def client_fidelite_response(item: ClientFidelite) -> ClientFideliteResponse:
    return ClientFideliteResponse(
        id=item.id,
        code=item.code,
        nom=item.nom,
        prenom=item.prenom,
        telephone=item.telephone,
        email=item.email,
        actif=item.actif,
    )


def carte_fidelite_response(item: CarteFidelite) -> CarteFideliteResponse:
    return CarteFideliteResponse(
        id=item.id,
        numero=item.numero,
        client_id=item.client_id,
        type_carte=item.type_carte,
        points=item.points,
        actif=item.actif,
        cree_le=item.cree_le,
    )


@router.get("/fidelite/clients", response_model=list[ClientFideliteResponse], tags=["Fidélité"])
def lister_clients_fidelite(
    service: Annotated[FideliteService, Depends(get_fidelite)],
) -> list[ClientFideliteResponse]:
    return [client_fidelite_response(item) for item in service.lister_clients()]


@router.post(
    "/fidelite/clients", response_model=ClientFideliteResponse, status_code=201, tags=["Fidélité"]
)
def creer_client_fidelite(
    payload: ClientFideliteCreate, service: Annotated[FideliteService, Depends(get_fidelite)]
) -> ClientFideliteResponse:
    return client_fidelite_response(service.creer_client(**payload.model_dump()))


@router.put(
    "/fidelite/clients/{client_id}", response_model=ClientFideliteResponse, tags=["Fidélité"]
)
def modifier_client_fidelite(
    client_id: UUID,
    payload: ClientFideliteUpdate,
    service: Annotated[FideliteService, Depends(get_fidelite)],
) -> ClientFideliteResponse:
    return client_fidelite_response(service.modifier_client(client_id, **payload.model_dump()))


@router.get("/fidelite/cartes", response_model=list[CarteFideliteResponse], tags=["Fidélité"])
def lister_cartes_fidelite(
    service: Annotated[FideliteService, Depends(get_fidelite)],
) -> list[CarteFideliteResponse]:
    return [carte_fidelite_response(item) for item in service.lister_cartes()]


@router.get(
    "/fidelite/cartes/recherche/{numero}",
    response_model=CarteFideliteLookupResponse,
    tags=["Fidélité"],
)
def rechercher_carte_fidelite(
    numero: str,
    service: Annotated[FideliteService, Depends(get_fidelite)],
) -> CarteFideliteLookupResponse:
    carte, client = service.rechercher_carte(numero)
    return CarteFideliteLookupResponse(
        carte=carte_fidelite_response(carte),
        client=client_fidelite_response(client),
    )


@router.post(
    "/fidelite/cartes", response_model=CarteFideliteResponse, status_code=201, tags=["Fidélité"]
)
def creer_carte_fidelite(
    payload: CarteFideliteCreate, service: Annotated[FideliteService, Depends(get_fidelite)]
) -> CarteFideliteResponse:
    return carte_fidelite_response(service.creer_carte(**payload.model_dump()))


@router.put("/fidelite/cartes/{carte_id}", response_model=CarteFideliteResponse, tags=["Fidélité"])
def modifier_carte_fidelite(
    carte_id: UUID,
    payload: CarteFideliteUpdate,
    service: Annotated[FideliteService, Depends(get_fidelite)],
) -> CarteFideliteResponse:
    return carte_fidelite_response(service.modifier_carte(carte_id, **payload.model_dump()))


@router.get(
    "/fidelite/cartes/{carte_id}/mouvements",
    response_model=list[MouvementFideliteResponse],
    tags=["Fidélité"],
)
def lister_mouvements_fidelite(
    carte_id: UUID, service: Annotated[FideliteService, Depends(get_fidelite)]
) -> list[MouvementFideliteResponse]:
    return [
        MouvementFideliteResponse(
            id=i.id,
            carte_id=i.carte_id,
            points=i.points,
            motif=i.motif,
            solde_apres=i.solde_apres,
            cree_le=i.cree_le,
        )
        for i in service.lister_mouvements(carte_id)
    ]


@router.post(
    "/fidelite/cartes/{carte_id}/mouvements",
    response_model=MouvementFideliteResponse,
    status_code=201,
    tags=["Fidélité"],
)
def ajuster_points_fidelite(
    carte_id: UUID,
    payload: MouvementFideliteCreate,
    service: Annotated[FideliteService, Depends(get_fidelite)],
) -> MouvementFideliteResponse:
    i = service.ajuster_points(carte_id, **payload.model_dump())
    return MouvementFideliteResponse(
        id=i.id,
        carte_id=i.carte_id,
        points=i.points,
        motif=i.motif,
        solde_apres=i.solde_apres,
        cree_le=i.cree_le,
    )


def compte_response(item: CompteOperation) -> CompteOperationResponse:
    return CompteOperationResponse(
        id=item.id,
        code=item.code,
        nom=item.nom,
        role=item.role,
        poste_id=item.poste_id,
        caisse=item.caisse,
        actif=item.actif,
    )


@router.get("/administration/caisses", response_model=list[CaisseResponse], tags=["Administration"])
def lister_caisses(
    service: Annotated[AdministrationService, Depends(get_administration)],
) -> list[CaisseResponse]:
    return [
        CaisseResponse(id=i.id, code=i.code, libelle=i.libelle, actif=i.actif)
        for i in service.lister_caisses()
    ]


@router.post(
    "/administration/caisses",
    response_model=CaisseResponse,
    status_code=201,
    tags=["Administration"],
)
def creer_caisse(
    payload: CaisseCreate, service: Annotated[AdministrationService, Depends(get_administration)]
) -> CaisseResponse:
    i = service.creer_caisse(**payload.model_dump())
    return CaisseResponse(id=i.id, code=i.code, libelle=i.libelle, actif=i.actif)


@router.get(
    "/administration/comptes", response_model=list[CompteOperationResponse], tags=["Administration"]
)
def lister_comptes(
    service: Annotated[AdministrationService, Depends(get_administration)],
) -> list[CompteOperationResponse]:
    return [compte_response(i) for i in service.lister()]


@router.post(
    "/administration/comptes",
    response_model=CompteOperationResponse,
    status_code=201,
    tags=["Administration"],
)
def creer_compte(
    payload: CompteOperationCreate,
    service: Annotated[AdministrationService, Depends(get_administration)],
) -> CompteOperationResponse:
    return compte_response(service.creer(**payload.model_dump()))


@router.put(
    "/administration/comptes/{compte_id}",
    response_model=CompteOperationResponse,
    tags=["Administration"],
)
def modifier_compte(
    compte_id: UUID,
    payload: CompteOperationUpdate,
    service: Annotated[AdministrationService, Depends(get_administration)],
) -> CompteOperationResponse:
    return compte_response(service.modifier(compte_id, **payload.model_dump()))
