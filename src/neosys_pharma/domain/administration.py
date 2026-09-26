from dataclasses import dataclass, field
from uuid import UUID, uuid4

from neosys_pharma.domain.shared import DomainError


@dataclass(slots=True, kw_only=True)
class Caisse:
    code: str
    libelle: str
    actif: bool = True
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        self.code = self.code.strip().upper()
        self.libelle = self.libelle.strip().upper()
        if not self.code or not self.libelle:
            raise DomainError("Le code et le libellé de la caisse sont obligatoires.")


@dataclass(slots=True, kw_only=True)
class CompteOperation:
    code: str
    nom: str
    role: str
    poste_id: UUID | None
    caisse: str
    actif: bool = True
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        self.modifier(
            nom=self.nom,
            role=self.role,
            poste_id=self.poste_id,
            caisse=self.caisse,
            actif=self.actif,
        )
        self.code = self.code.strip().upper()
        if not self.code:
            raise DomainError("Le code du compte est obligatoire.")

    def modifier(
        self, *, nom: str, role: str, poste_id: UUID | None, caisse: str, actif: bool
    ) -> None:
        self.nom = nom.strip().upper()
        if not self.nom:
            raise DomainError("Le nom du compte est obligatoire.")
        role = role.strip().upper()
        if role not in {"VENTE", "PREPARATION"}:
            raise DomainError("Le rôle du compte est invalide.")
        self.role = role
        self.poste_id = poste_id
        self.caisse = caisse.strip().upper()
        self.actif = actif
        if not self.caisse:
            raise DomainError("La caisse associée est obligatoire.")
