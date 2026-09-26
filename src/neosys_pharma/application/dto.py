from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True, slots=True, kw_only=True)
class CreerMedicament:
    reference: str = ""
    designation: str
    cip7: str = ""
    principe_actif: str = ""
    principe_actif_id: UUID | None = None
    pris_en_charge_cnamgs: bool = False
    taux_prise_en_charge_cnamgs: Decimal = Decimal("0")


@dataclass(frozen=True, slots=True, kw_only=True)
class CreerProduitCosmetique:
    reference: str = ""
    designation: str
    cip7: str = ""
    marque: str = ""
    marque_id: UUID | None = None
    pris_en_charge_cnamgs: bool = False
    taux_prise_en_charge_cnamgs: Decimal = Decimal("0")


@dataclass(frozen=True, slots=True, kw_only=True)
class AjouterConditionnement:
    produit_id: UUID
    code: str = ""
    libelle: str
    prix_vente: Decimal


@dataclass(frozen=True, slots=True, kw_only=True)
class ModifierProduit:
    produit_id: UUID
    reference: str
    designation: str
    cip7: str = ""
    information: str = ""
    principe_actif_id: UUID | None = None
    marque_id: UUID | None = None
    pris_en_charge_cnamgs: bool = False
    taux_prise_en_charge_cnamgs: Decimal = Decimal("0")


@dataclass(frozen=True, slots=True, kw_only=True)
class CreerOrganismePriseEnCharge:
    code: str = ""
    nom: str
    type_organisme: str
    documents_requis: tuple[str, ...] = ()
    taux_prise_en_charge: Decimal = Decimal("0")


@dataclass(frozen=True, slots=True, kw_only=True)
class ModifierOrganismePriseEnCharge:
    organisme_id: UUID
    code: str
    nom: str
    type_organisme: str
    documents_requis: tuple[str, ...] = ()
    taux_prise_en_charge: Decimal = Decimal("0")
    actif: bool = True


@dataclass(frozen=True, slots=True, kw_only=True)
class ModifierConditionnement:
    conditionnement_id: UUID
    code: str
    libelle: str
    prix_vente: Decimal


@dataclass(frozen=True, slots=True, kw_only=True)
class CreerFournisseur:
    code: str = ""
    raison_sociale: str
    telephone: str = ""
    email: str = ""


@dataclass(frozen=True, slots=True, kw_only=True)
class ModifierFournisseur:
    fournisseur_id: UUID
    code: str
    raison_sociale: str
    telephone: str = ""
    email: str = ""
    actif: bool = True


@dataclass(frozen=True, slots=True, kw_only=True)
class DefinirTarifFournisseur:
    fournisseur_id: UUID
    conditionnement_id: UUID
    prix_achat: Decimal
    reference_fournisseur: str = ""


@dataclass(frozen=True, slots=True, kw_only=True)
class LigneCommandeReception:
    conditionnement_id: UUID
    quantite_commandee: int
    quantite_recue: int
    numero_lot: str
    date_expiration: date
    prix_unitaire: Decimal


@dataclass(frozen=True, slots=True, kw_only=True)
class CreerCommandeReception:
    fournisseur_id: UUID
    emplacement_id: UUID
    date_commande: date
    date_arrivee: date
    numero_fournisseur: str = ""
    lignes: tuple[LigneCommandeReception, ...] = ()


@dataclass(frozen=True, slots=True, kw_only=True)
class ReceptionnerLot:
    conditionnement_id: UUID
    numero_lot: str
    date_expiration: date
    emplacement_id: UUID
    quantite: int
    motif: str


@dataclass(frozen=True, slots=True, kw_only=True)
class TransfererStock:
    lot_id: UUID
    source_id: UUID
    destination_id: UUID
    quantite: int
    motif: str


@dataclass(frozen=True, slots=True, kw_only=True)
class AjusterStock:
    lot_id: UUID
    emplacement_id: UUID
    nouvelle_quantite: int
    motif: str


@dataclass(frozen=True, slots=True, kw_only=True)
class LigneEtatStock:
    lot_id: UUID
    numero_lot: str
    date_expiration: date
    emplacement_id: UUID
    quantite_physique: int
    quantite_reservee: int
    quantite_disponible: int
    etat_lot: str


@dataclass(frozen=True, slots=True, kw_only=True)
class LigneEtatStockGlobal:
    lot_id: UUID
    conditionnement_id: UUID
    numero_lot: str
    date_expiration: date
    emplacement_id: UUID
    quantite_physique: int
    quantite_reservee: int
    quantite_disponible: int
    etat_lot: str


@dataclass(frozen=True, slots=True, kw_only=True)
class CreerPosteVente:
    code: str
    secteur_id: UUID
    emplacement_id: UUID
    caisse_id: UUID | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class AjouterLigneVente:
    vente_id: UUID
    conditionnement_id: UUID
    quantite: int
