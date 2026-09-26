from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from neosys_pharma.domain.shared import DomainError
from neosys_pharma.domain.vente.enums import EtatVente


@dataclass(frozen=True, slots=True, kw_only=True)
class PosteVente:
    code: str
    secteur_id: UUID
    emplacement_id: UUID
    caisse_id: UUID | None = None
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise DomainError("Le code du poste de vente est obligatoire.")


@dataclass(slots=True, kw_only=True)
class LigneVente:
    conditionnement_id: UUID
    designation: str
    quantite: int
    prix_unitaire: Decimal
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        self.designation = self.designation.strip()
        if not self.designation:
            raise DomainError("La désignation de la ligne est obligatoire.")
        if self.quantite <= 0:
            raise DomainError("La quantité vendue doit être strictement positive.")
        if self.prix_unitaire <= 0:
            raise DomainError("Le prix unitaire doit être strictement positif.")

    @property
    def montant(self) -> Decimal:
        return self.prix_unitaire * self.quantite


@dataclass(frozen=True, slots=True, kw_only=True)
class AllocationLot:
    ligne_vente_id: UUID
    lot_id: UUID
    quantite: int
    date_expiration: date
    emplacement_id: UUID | None = None
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if self.quantite <= 0:
            raise DomainError("La quantité allouée doit être strictement positive.")


@dataclass(slots=True, kw_only=True)
class Vente:
    poste_id: UUID
    secteur_id: UUID
    emplacement_id: UUID
    date_commerciale: date
    organisme_id: UUID | None = None
    patient_nom: str = ""
    patient_prenom: str = ""
    informations_prise_en_charge: dict[str, str] = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)
    etat: EtatVente = field(default=EtatVente.EN_PREPARATION, init=False)
    lignes: list[LigneVente] = field(default_factory=list, init=False)
    allocations: list[AllocationLot] = field(default_factory=list, init=False)
    encaissement_id: UUID | None = field(default=None, init=False)
    reglements: list[dict[str, str]] = field(default_factory=list, init=False)
    carte_fidelite_id: UUID | None = field(default=None, init=False)
    points_utilises: int = field(default=0, init=False)
    encaissee_le: datetime | None = field(default=None, init=False)

    @property
    def montant_total(self) -> Decimal:
        return sum((ligne.montant for ligne in self.lignes), start=Decimal("0"))

    @property
    def montant_a_payer(self) -> Decimal:
        valeur = self.informations_prise_en_charge.get("montant_client")
        if valeur in {None, ""}:
            return self.montant_total
        montant = Decimal(str(valeur))
        return max(Decimal("0"), min(self.montant_total, montant))

    @property
    def numero_ticket(self) -> str:
        """Numéro stable et lisible utilisé à l'écran et sur le ticket imprimé."""
        date_ticket = self.date_commerciale.strftime("%Y%m%d")
        suffixe = str(self.id).split("-", maxsplit=1)[0].upper()
        return f"T-{date_ticket}-{suffixe}"

    def ajouter_ligne(
        self,
        *,
        conditionnement_id: UUID,
        designation: str,
        quantite: int,
        prix_unitaire: Decimal,
    ) -> LigneVente:
        self._verifier_modifiable()
        ligne = LigneVente(
            conditionnement_id=conditionnement_id,
            designation=designation,
            quantite=quantite,
            prix_unitaire=prix_unitaire,
        )
        self.lignes.append(ligne)
        return ligne

    def placer_en_attente(self, allocations: list[AllocationLot]) -> None:
        self._verifier_modifiable()
        if not self.lignes:
            raise DomainError("Une vente vide ne peut pas être préparée.")
        quantites_par_ligne: dict[UUID, int] = {}
        for allocation in allocations:
            quantites_par_ligne[allocation.ligne_vente_id] = (
                quantites_par_ligne.get(allocation.ligne_vente_id, 0) + allocation.quantite
            )
        if any(quantites_par_ligne.get(ligne.id, 0) != ligne.quantite for ligne in self.lignes):
            raise DomainError("Toutes les lignes doivent être entièrement réservées.")
        self.allocations.extend(allocations)
        self.etat = EtatVente.EN_ATTENTE_PAIEMENT

    def annuler(self) -> None:
        if self.etat not in {
            EtatVente.EN_PREPARATION,
            EtatVente.EN_ATTENTE_PAIEMENT,
        }:
            raise DomainError("Cette vente ne peut plus être annulée.")
        self.etat = EtatVente.ANNULEE

    def finaliser(
        self,
        *,
        encaissement_id: UUID,
        reglements: list[dict[str, str]],
        carte_fidelite_id: UUID | None = None,
        points_utilises: int = 0,
    ) -> None:
        if self.etat is not EtatVente.EN_ATTENTE_PAIEMENT:
            raise DomainError("Seule une vente préparée peut être encaissée.")
        self.encaissement_id = encaissement_id
        self.reglements = reglements
        self.carte_fidelite_id = carte_fidelite_id
        self.points_utilises = points_utilises
        self.encaissee_le = datetime.now(UTC).replace(tzinfo=None)
        self.etat = EtatVente.FINALISEE

    def _verifier_modifiable(self) -> None:
        if self.etat is not EtatVente.EN_PREPARATION:
            raise DomainError("La vente n'est plus modifiable.")
