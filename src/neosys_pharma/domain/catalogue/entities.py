from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from neosys_pharma.domain.shared import DomainError


def _texte_obligatoire(valeur: str, nom: str) -> str:
    texte = valeur.strip()
    if not texte:
        raise DomainError(f"{nom} est obligatoire.")
    return texte


@dataclass(slots=True, kw_only=True)
class Produit:
    reference: str
    designation: str
    cip7: str = ""
    pris_en_charge_cnamgs: bool = False
    taux_prise_en_charge_cnamgs: Decimal = Decimal("0")
    id: UUID = field(default_factory=uuid4)
    conditionnements: list[ProduitConditionnement] = field(
        default_factory=list, init=False, repr=False
    )

    def __post_init__(self) -> None:
        self.reference = _texte_obligatoire(self.reference, "La référence")
        self.designation = _texte_obligatoire(self.designation, "La désignation")
        self.cip7 = self._normaliser_cip7(self.cip7)
        self.modifier_couverture_cnamgs(
            pris_en_charge=self.pris_en_charge_cnamgs,
            taux=self.taux_prise_en_charge_cnamgs,
        )

    def ajouter_conditionnement(
        self, *, code: str, libelle: str, prix_vente: Decimal
    ) -> ProduitConditionnement:
        if any(item.code == code.strip() for item in self.conditionnements):
            raise DomainError(f"Le conditionnement {code!r} existe déjà pour ce produit.")

        conditionnement = ProduitConditionnement(
            produit_id=self.id,
            code=code,
            libelle=libelle,
            prix_vente=prix_vente,
        )
        self.conditionnements.append(conditionnement)
        return conditionnement

    def modifier_identite(self, *, reference: str, designation: str, cip7: str) -> None:
        self.reference = _texte_obligatoire(reference, "La référence")
        self.designation = _texte_obligatoire(designation, "La désignation")
        self.cip7 = self._normaliser_cip7(cip7)

    def modifier_couverture_cnamgs(self, *, pris_en_charge: bool, taux: Decimal) -> None:
        if taux < Decimal("0") or taux > Decimal("100"):
            raise DomainError("Le taux de prise en charge CNAMGS doit être compris entre 0 et 100.")
        if pris_en_charge and taux <= Decimal("0"):
            raise DomainError("Un taux CNAMGS strictement positif est requis.")
        self.pris_en_charge_cnamgs = pris_en_charge
        self.taux_prise_en_charge_cnamgs = taux if pris_en_charge else Decimal("0")

    @staticmethod
    def _normaliser_cip7(cip7: str) -> str:
        valeur = cip7.strip()
        if valeur and (len(valeur) != 7 or not valeur.isdigit()):
            raise DomainError("Le CIP7 doit contenir exactement 7 chiffres.")
        return valeur


@dataclass(slots=True, kw_only=True)
class Medicament(Produit):
    principe_actif: str
    principe_actif_id: UUID | None = None

    def __post_init__(self) -> None:
        Produit.__post_init__(self)
        self.principe_actif = _texte_obligatoire(self.principe_actif, "Le principe actif")

    def modifier_principe_actif(self, principe: PrincipeActif) -> None:
        self.principe_actif_id = principe.id
        self.principe_actif = principe.libelle


@dataclass(slots=True, kw_only=True)
class ProduitCosmetique(Produit):
    marque: str
    marque_id: UUID | None = None

    def __post_init__(self) -> None:
        Produit.__post_init__(self)
        self.marque = _texte_obligatoire(self.marque, "La marque")

    def modifier_marque(self, marque: Marque) -> None:
        self.marque_id = marque.id
        self.marque = marque.libelle


@dataclass(slots=True, kw_only=True)
class ProduitConditionnement:
    produit_id: UUID
    code: str
    libelle: str
    prix_vente: Decimal
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        self.code = _texte_obligatoire(self.code, "Le code")
        self.libelle = _texte_obligatoire(self.libelle, "Le libellé")
        if self.prix_vente <= Decimal("0"):
            raise DomainError("Le prix de vente doit être strictement positif.")

    def modifier(self, *, code: str, libelle: str, prix_vente: Decimal) -> None:
        self.code = _texte_obligatoire(code, "Le code")
        self.libelle = _texte_obligatoire(libelle, "Le libellé")
        if prix_vente <= Decimal("0"):
            raise DomainError("Le prix de vente doit être strictement positif.")
        self.prix_vente = prix_vente


@dataclass(frozen=True, slots=True, kw_only=True)
class PrincipeActif:
    libelle: str
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        object.__setattr__(self, "libelle", _texte_obligatoire(self.libelle, "Le principe actif"))


@dataclass(frozen=True, slots=True, kw_only=True)
class Marque:
    libelle: str
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        object.__setattr__(self, "libelle", _texte_obligatoire(self.libelle, "La marque"))


@dataclass(slots=True, kw_only=True)
class Fournisseur:
    code: str
    raison_sociale: str
    telephone: str = ""
    email: str = ""
    actif: bool = True
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        self.modifier(
            code=self.code,
            raison_sociale=self.raison_sociale,
            telephone=self.telephone,
            email=self.email,
            actif=self.actif,
        )

    def modifier(
        self,
        *,
        code: str,
        raison_sociale: str,
        telephone: str,
        email: str,
        actif: bool,
    ) -> None:
        self.code = _texte_obligatoire(code, "Le code fournisseur")
        self.raison_sociale = _texte_obligatoire(raison_sociale, "La raison sociale")
        self.telephone = telephone.strip()
        self.email = email.strip()
        self.actif = actif


@dataclass(slots=True, kw_only=True)
class TarifFournisseur:
    fournisseur_id: UUID
    conditionnement_id: UUID
    prix_achat: Decimal
    reference_fournisseur: str = ""
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        self.modifier(
            prix_achat=self.prix_achat,
            reference_fournisseur=self.reference_fournisseur,
        )

    def modifier(self, *, prix_achat: Decimal, reference_fournisseur: str) -> None:
        if prix_achat <= Decimal("0"):
            raise DomainError("Le prix d'achat doit être strictement positif.")
        self.prix_achat = prix_achat
        self.reference_fournisseur = reference_fournisseur.strip()


@dataclass(slots=True, kw_only=True)
class OrganismePriseEnCharge:
    code: str
    nom: str
    type_organisme: str
    documents_requis: tuple[str, ...] = ()
    taux_prise_en_charge: Decimal = Decimal("0")
    actif: bool = True
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        self.modifier(
            code=self.code,
            nom=self.nom,
            type_organisme=self.type_organisme,
            documents_requis=self.documents_requis,
            taux_prise_en_charge=self.taux_prise_en_charge,
            actif=self.actif,
        )

    def modifier(
        self,
        *,
        code: str,
        nom: str,
        type_organisme: str,
        documents_requis: tuple[str, ...],
        taux_prise_en_charge: Decimal,
        actif: bool,
    ) -> None:
        type_normalise = type_organisme.strip().upper()
        if type_normalise not in {"CNAMGS", "MUTUELLE", "ASSURANCE_PRIVEE"}:
            raise DomainError("Le type d'organisme est invalide.")
        documents = tuple(dict.fromkeys(item.strip() for item in documents_requis if item.strip()))
        self.code = _texte_obligatoire(code, "Le code organisme")
        self.nom = _texte_obligatoire(nom, "Le nom de l'organisme")
        self.type_organisme = type_normalise
        self.documents_requis = documents
        if taux_prise_en_charge < Decimal("0") or taux_prise_en_charge > Decimal("100"):
            raise DomainError("Le taux de prise en charge doit être compris entre 0 et 100.")
        self.taux_prise_en_charge = taux_prise_en_charge
        self.actif = actif


@dataclass(slots=True, kw_only=True)
class ClientFidelite:
    code: str
    nom: str
    prenom: str = ""
    telephone: str = ""
    email: str = ""
    actif: bool = True
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        self.code = _texte_obligatoire(self.code, "Le code client")
        self.modifier(
            nom=self.nom,
            prenom=self.prenom,
            telephone=self.telephone,
            email=self.email,
            actif=self.actif,
        )

    def modifier(self, *, nom: str, prenom: str, telephone: str, email: str, actif: bool) -> None:
        self.nom = _texte_obligatoire(nom, "Le nom du client")
        self.prenom = prenom.strip()
        self.telephone = telephone.strip()
        self.email = email.strip()
        self.actif = actif


@dataclass(slots=True, kw_only=True)
class CarteFidelite:
    numero: str
    client_id: UUID
    type_carte: str
    points: int = 0
    actif: bool = True
    cree_le: datetime = field(default_factory=lambda: datetime.now(UTC))
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        self.numero = _texte_obligatoire(self.numero, "Le numéro de carte")
        self.modifier(type_carte=self.type_carte, actif=self.actif)
        if self.points < 0:
            raise DomainError("Le solde de points ne peut pas être négatif.")

    def modifier(self, *, type_carte: str, actif: bool) -> None:
        valeur = type_carte.strip().upper()
        if valeur not in {"PHYSIQUE", "VIRTUELLE"}:
            raise DomainError("Le type de carte est invalide.")
        self.type_carte = valeur
        self.actif = actif

    def ajuster_points(self, points: int) -> int:
        nouveau_solde = self.points + points
        if points == 0:
            raise DomainError("Le mouvement de points ne peut pas être nul.")
        if nouveau_solde < 0:
            raise DomainError("Le solde de points est insuffisant.")
        self.points = nouveau_solde
        return nouveau_solde


@dataclass(frozen=True, slots=True, kw_only=True)
class MouvementFidelite:
    carte_id: UUID
    points: int
    motif: str
    solde_apres: int
    cree_le: datetime = field(default_factory=lambda: datetime.now(UTC))
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        object.__setattr__(self, "motif", _texte_obligatoire(self.motif, "Le motif"))
        if self.points == 0:
            raise DomainError("Le mouvement de points ne peut pas être nul.")


@dataclass(frozen=True, slots=True, kw_only=True)
class LigneCommandeAchat:
    conditionnement_id: UUID
    designation: str
    cip7: str
    quantite_commandee: int
    quantite_recue: int
    numero_lot: str
    date_expiration: date
    prix_unitaire: Decimal
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "designation", _texte_obligatoire(self.designation, "La désignation")
        )
        object.__setattr__(
            self, "numero_lot", _texte_obligatoire(self.numero_lot, "Le numéro de lot")
        )
        if self.quantite_commandee <= 0:
            raise DomainError("La quantité commandée doit être strictement positive.")
        if self.quantite_recue < 0 or self.quantite_recue > self.quantite_commandee:
            raise DomainError(
                "La quantité reçue doit être comprise entre 0 et la quantité commandée."
            )
        if self.prix_unitaire <= Decimal("0"):
            raise DomainError("Le prix unitaire doit être strictement positif.")

    @property
    def total(self) -> Decimal:
        return self.prix_unitaire * self.quantite_recue


@dataclass(slots=True, kw_only=True)
class CommandeAchat:
    numero_interne: str
    fournisseur_id: UUID
    emplacement_id: UUID
    date_commande: date
    date_arrivee: date
    numero_fournisseur: str = ""
    lignes: list[LigneCommandeAchat] = field(default_factory=list)
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        self.numero_interne = _texte_obligatoire(self.numero_interne, "Le numéro interne")
        self.numero_fournisseur = self.numero_fournisseur.strip()
        if self.date_arrivee < self.date_commande:
            raise DomainError("La date d'arrivée ne peut pas précéder la date de commande.")
        if not self.lignes:
            raise DomainError("La commande doit contenir au moins une ligne.")

    @property
    def total_general(self) -> Decimal:
        return sum((ligne.total for ligne in self.lignes), start=Decimal("0"))
