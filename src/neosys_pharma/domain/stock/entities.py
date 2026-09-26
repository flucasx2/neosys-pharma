from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from uuid import UUID, uuid4

from neosys_pharma.domain.shared import DomainError
from neosys_pharma.domain.stock.enums import EtatLot, TypeMouvement


@dataclass(frozen=True, slots=True, kw_only=True)
class Emplacement:
    code: str
    libelle: str
    autorise_vente: bool = True
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not self.code.strip() or not self.libelle.strip():
            raise DomainError("Le code et le libellé de l'emplacement sont obligatoires.")


@dataclass(slots=True, kw_only=True)
class Lot:
    conditionnement_id: UUID
    numero: str
    date_expiration: date
    etat: EtatLot = EtatLot.ACTIF
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        self.numero = self.numero.strip()
        if not self.numero:
            raise DomainError("Le numéro de lot est obligatoire.")

    def est_vendable(self, au: date) -> bool:
        return self.etat is EtatLot.ACTIF and self.date_expiration >= au


@dataclass(slots=True, kw_only=True)
class StockEmplacement:
    lot_id: UUID
    emplacement_id: UUID
    quantite_physique: int = 0
    quantite_reservee: int = 0

    def __post_init__(self) -> None:
        if self.quantite_physique < 0 or self.quantite_reservee < 0:
            raise DomainError("Les quantités de stock ne peuvent pas être négatives.")
        if self.quantite_reservee > self.quantite_physique:
            raise DomainError("La quantité réservée dépasse le stock physique.")

    @property
    def quantite_disponible(self) -> int:
        return self.quantite_physique - self.quantite_reservee


@dataclass(frozen=True, slots=True, kw_only=True)
class MouvementStock:
    type: TypeMouvement
    lot_id: UUID
    quantite: int
    emplacement_source_id: UUID | None = None
    emplacement_destination_id: UUID | None = None
    motif: str
    cree_le: datetime = field(default_factory=lambda: datetime.now(UTC))
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if self.quantite <= 0:
            raise DomainError("La quantité d'un mouvement doit être strictement positive.")
        if not self.motif.strip():
            raise DomainError("Le motif du mouvement est obligatoire.")


@dataclass(frozen=True, slots=True, kw_only=True)
class AllocationFefo:
    lot_id: UUID
    quantite: int
    date_expiration: date
