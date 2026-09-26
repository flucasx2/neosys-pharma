from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class MedicamentCreate(StrictSchema):
    reference: str = Field(default="", max_length=50)
    designation: str = Field(min_length=1, max_length=200)
    cip7: str = Field(default="", max_length=7, pattern=r"^(?:\d{7})?$")
    principe_actif: str = Field(default="", max_length=200)
    principe_actif_id: UUID | None = None
    pris_en_charge_cnamgs: bool = False
    taux_prise_en_charge_cnamgs: Decimal = Field(default=Decimal("0"), ge=0, le=100)

    @model_validator(mode="after")
    def principe_obligatoire(self) -> "MedicamentCreate":
        if self.principe_actif_id is None and not self.principe_actif:
            raise ValueError("Un principe actif est obligatoire.")
        return self


class CosmetiqueCreate(StrictSchema):
    reference: str = Field(default="", max_length=50)
    designation: str = Field(min_length=1, max_length=200)
    cip7: str = Field(default="", max_length=7, pattern=r"^(?:\d{7})?$")
    marque: str = Field(default="", max_length=120)
    marque_id: UUID | None = None
    pris_en_charge_cnamgs: bool = False
    taux_prise_en_charge_cnamgs: Decimal = Field(default=Decimal("0"), ge=0, le=100)

    @model_validator(mode="after")
    def marque_obligatoire(self) -> "CosmetiqueCreate":
        if self.marque_id is None and not self.marque:
            raise ValueError("Une marque est obligatoire.")
        return self


class ProduitResponse(StrictSchema):
    id: UUID
    type: str
    reference: str
    designation: str


class ConditionnementCreate(StrictSchema):
    code: str = Field(default="", max_length=50)
    libelle: str = Field(min_length=1, max_length=200)
    prix_vente: Decimal = Field(gt=0, decimal_places=2)


class ConditionnementResponse(StrictSchema):
    id: UUID
    produit_id: UUID
    code: str
    libelle: str
    prix_vente: Decimal


class ProduitDetailResponse(ProduitResponse):
    cip7: str
    information: str
    principe_actif_id: UUID | None = None
    marque_id: UUID | None = None
    pris_en_charge_cnamgs: bool
    taux_prise_en_charge_cnamgs: Decimal
    conditionnements: list[ConditionnementResponse]


class ProduitUpdate(StrictSchema):
    reference: str = Field(min_length=1, max_length=50)
    designation: str = Field(min_length=1, max_length=200)
    cip7: str = Field(default="", max_length=7, pattern=r"^(?:\d{7})?$")
    information: str = Field(default="", max_length=200)
    principe_actif_id: UUID | None = None
    marque_id: UUID | None = None
    pris_en_charge_cnamgs: bool = False
    taux_prise_en_charge_cnamgs: Decimal = Field(default=Decimal("0"), ge=0, le=100)


class ConditionnementUpdate(ConditionnementCreate):
    pass


class PrincipeActifCreate(StrictSchema):
    libelle: str = Field(min_length=1, max_length=200)


class PrincipeActifResponse(StrictSchema):
    id: UUID
    libelle: str


class MarqueCreate(StrictSchema):
    libelle: str = Field(min_length=1, max_length=120)


class MarqueResponse(MarqueCreate):
    id: UUID


class FournisseurCreate(StrictSchema):
    code: str = Field(default="", max_length=50)
    raison_sociale: str = Field(min_length=1, max_length=200)
    telephone: str = Field(default="", max_length=50)
    email: str = Field(default="", max_length=200)


class FournisseurUpdate(FournisseurCreate):
    actif: bool = True


class FournisseurResponse(FournisseurUpdate):
    id: UUID


class TarifFournisseurCreate(StrictSchema):
    fournisseur_id: UUID
    conditionnement_id: UUID
    prix_achat: Decimal = Field(gt=0, decimal_places=2)
    reference_fournisseur: str = Field(default="", max_length=100)


class TarifFournisseurResponse(TarifFournisseurCreate):
    id: UUID


class CatalogueFournisseurImport(StrictSchema):
    fournisseur_id: UUID
    mode: str = Field(pattern=r"^(MISE_EN_PLACE|MISE_A_JOUR_TARIFS)$")
    contenu_csv: str = Field(min_length=1)
    confirmer_mise_en_place: bool = False


class CatalogueFournisseurImportResponse(StrictSchema):
    lignes_lues: int
    produits_supprimes: int
    produits_crees: int
    produits_mis_a_jour: int
    tarifs_enregistres: int
    lignes_ignorees: int
    erreurs: list[str]


class OrganismePriseEnChargeCreate(StrictSchema):
    code: str = Field(default="", max_length=50)
    nom: str = Field(min_length=1, max_length=200)
    type_organisme: str = Field(pattern=r"^(CNAMGS|MUTUELLE|ASSURANCE_PRIVEE)$")
    documents_requis: list[str] = Field(default_factory=list, max_length=30)
    taux_prise_en_charge: Decimal = Field(default=Decimal("0"), ge=0, le=100)


class OrganismePriseEnChargeResponse(OrganismePriseEnChargeCreate):
    id: UUID
    actif: bool


class OrganismePriseEnChargeUpdate(OrganismePriseEnChargeCreate):
    actif: bool = True


class ArticleCatalogueResponse(StrictSchema):
    id: UUID
    produit_id: UUID
    type_produit: str
    reference: str
    designation: str
    cip7: str
    code: str
    libelle: str
    prix_vente: Decimal
    pris_en_charge_cnamgs: bool = False
    taux_prise_en_charge_cnamgs: Decimal = Field(default=Decimal("0"), ge=0, le=100)


class EmplacementCreate(StrictSchema):
    code: str = Field(min_length=1, max_length=50)
    libelle: str = Field(min_length=1, max_length=120)
    autorise_vente: bool = True


class EmplacementResponse(StrictSchema):
    id: UUID
    code: str
    libelle: str
    autorise_vente: bool


class ReceptionLotCreate(StrictSchema):
    conditionnement_id: UUID
    numero_lot: str = Field(min_length=1, max_length=100)
    date_expiration: date
    emplacement_id: UUID
    quantite: int = Field(gt=0)
    motif: str = Field(min_length=1, max_length=300)


class LotResponse(StrictSchema):
    id: UUID
    conditionnement_id: UUID
    numero: str
    date_expiration: date
    etat: str


class TransfertCreate(StrictSchema):
    lot_id: UUID
    source_id: UUID
    destination_id: UUID
    quantite: int = Field(gt=0)
    motif: str = Field(min_length=1, max_length=300)


class AjustementCreate(StrictSchema):
    lot_id: UUID
    emplacement_id: UUID
    nouvelle_quantite: int = Field(ge=0)
    motif: str = Field(min_length=1, max_length=300)


class MouvementResponse(StrictSchema):
    id: UUID
    type: str
    lot_id: UUID
    quantite: int


class LigneStockResponse(StrictSchema):
    lot_id: UUID
    numero_lot: str
    date_expiration: date
    emplacement_id: UUID
    quantite_physique: int
    quantite_reservee: int
    quantite_disponible: int
    etat_lot: str


class LigneStockGlobalResponse(LigneStockResponse):
    conditionnement_id: UUID


class LigneCommandeReceptionCreate(StrictSchema):
    conditionnement_id: UUID
    quantite_commandee: int = Field(gt=0)
    quantite_recue: int = Field(ge=0)
    numero_lot: str = Field(min_length=1, max_length=100)
    date_expiration: date
    prix_unitaire: Decimal = Field(gt=0, decimal_places=2)


class CommandeReceptionCreate(StrictSchema):
    fournisseur_id: UUID
    emplacement_id: UUID
    date_commande: date
    date_arrivee: date
    numero_fournisseur: str = Field(default="", max_length=100)
    lignes: list[LigneCommandeReceptionCreate] = Field(min_length=1)


class LigneCommandeReceptionResponse(LigneCommandeReceptionCreate):
    id: UUID
    designation: str
    cip7: str
    total: Decimal


class CommandeReceptionResponse(StrictSchema):
    id: UUID
    numero_interne: str
    fournisseur_id: UUID
    emplacement_id: UUID
    date_commande: date
    date_arrivee: date
    numero_fournisseur: str
    total_general: Decimal
    lignes: list[LigneCommandeReceptionResponse]


class HealthResponse(StrictSchema):
    status: str
    service: str


class ErrorResponse(StrictSchema):
    detail: str


class PosteVenteCreate(StrictSchema):
    code: str = Field(min_length=1, max_length=50)
    secteur_id: UUID
    emplacement_id: UUID
    caisse_id: UUID | None = None


class PosteVenteResponse(StrictSchema):
    id: UUID
    code: str
    secteur_id: UUID
    emplacement_id: UUID
    caisse_id: UUID | None = None


class VenteCreate(StrictSchema):
    poste_id: UUID
    date_commerciale: date
    organisme_id: UUID | None = None
    patient_nom: str = Field(default="", max_length=150)
    patient_prenom: str = Field(default="", max_length=150)
    informations_prise_en_charge: dict[str, str] = Field(default_factory=dict)


class LigneVenteCreate(StrictSchema):
    conditionnement_id: UUID
    quantite: int = Field(gt=0)


class LigneVenteResponse(StrictSchema):
    id: UUID
    conditionnement_id: UUID
    designation: str
    quantite: int
    prix_unitaire: Decimal
    montant: Decimal


class AllocationLotResponse(StrictSchema):
    id: UUID
    ligne_vente_id: UUID
    lot_id: UUID
    quantite: int
    date_expiration: date
    emplacement_id: UUID | None = None


class ReglementCreate(StrictSchema):
    mode: str = Field(
        pattern=r"^(ESPECES|CHEQUE|CARTE_BANCAIRE|AIRTEL_MONEY|BGFI_MOBILE|MOBICASH|FLOOZ)$"
    )
    montant: Decimal = Field(gt=0)


class EncaissementCreate(StrictSchema):
    vente_ids: list[UUID] = Field(min_length=1)
    reglements: list[ReglementCreate] = Field(min_length=1)
    carte_fidelite_id: UUID | None = None
    points_utilises: int = Field(default=0, ge=0)


class VenteResponse(StrictSchema):
    id: UUID
    numero_ticket: str
    poste_id: UUID
    secteur_id: UUID
    emplacement_id: UUID
    date_commerciale: date
    etat: str
    montant_total: Decimal
    montant_a_payer: Decimal
    lignes: list[LigneVenteResponse]
    allocations: list[AllocationLotResponse]
    organisme_id: UUID | None = None
    patient_nom: str = ""
    patient_prenom: str = ""
    informations_prise_en_charge: dict[str, str] = Field(default_factory=dict)
    encaissement_id: UUID | None = None
    reglements: list[dict[str, str]] = Field(default_factory=list)
    carte_fidelite_id: UUID | None = None
    points_utilises: int = 0
    encaissee_le: datetime | None = None


class ClientFideliteCreate(StrictSchema):
    nom: str = Field(min_length=1, max_length=150)
    prenom: str = Field(default="", max_length=150)
    telephone: str = Field(default="", max_length=50)
    email: str = Field(default="", max_length=200)


class ClientFideliteUpdate(ClientFideliteCreate):
    actif: bool


class ClientFideliteResponse(ClientFideliteUpdate):
    id: UUID
    code: str


class CarteFideliteCreate(StrictSchema):
    client_id: UUID
    type_carte: str = Field(pattern=r"^(PHYSIQUE|VIRTUELLE)$")


class CarteFideliteUpdate(StrictSchema):
    type_carte: str = Field(pattern=r"^(PHYSIQUE|VIRTUELLE)$")
    actif: bool


class CarteFideliteResponse(CarteFideliteUpdate):
    id: UUID
    numero: str
    client_id: UUID
    points: int
    cree_le: datetime


class CarteFideliteLookupResponse(StrictSchema):
    carte: CarteFideliteResponse
    client: ClientFideliteResponse


class MouvementFideliteCreate(StrictSchema):
    points: int
    motif: str = Field(min_length=1, max_length=300)


class MouvementFideliteResponse(MouvementFideliteCreate):
    id: UUID
    carte_id: UUID
    solde_apres: int
    cree_le: datetime


class CompteOperationCreate(StrictSchema):
    code: str = Field(min_length=1, max_length=50)
    nom: str = Field(min_length=1, max_length=150)
    role: str = Field(pattern=r"^(VENTE|PREPARATION)$")
    poste_id: UUID | None = None
    caisse: str = Field(min_length=1, max_length=50)


class CompteOperationUpdate(CompteOperationCreate):
    actif: bool


class CompteOperationResponse(CompteOperationUpdate):
    id: UUID


class CaisseCreate(StrictSchema):
    code: str = Field(min_length=1, max_length=50)
    libelle: str = Field(min_length=1, max_length=150)


class CaisseResponse(CaisseCreate):
    id: UUID
    actif: bool
