from typing import Protocol
from uuid import UUID

from neosys_pharma.domain.administration import Caisse, CompteOperation
from neosys_pharma.domain.shared import DomainError


class AdministrationRepository(Protocol):
    def enregistrer_caisse(self, item: Caisse) -> None: ...
    def lister_caisses(self) -> tuple[Caisse, ...]: ...
    def enregistrer_compte(self, item: CompteOperation) -> None: ...
    def obtenir_compte(self, item_id: UUID) -> CompteOperation | None: ...
    def lister_comptes(self) -> tuple[CompteOperation, ...]: ...


class AdministrationService:
    def __init__(self, depot: AdministrationRepository) -> None:
        self._depot = depot

    def lister(self) -> tuple[CompteOperation, ...]:
        return self._depot.lister_comptes()

    def lister_caisses(self) -> tuple[Caisse, ...]:
        return self._depot.lister_caisses()

    def creer_caisse(self, *, code: str, libelle: str) -> Caisse:
        if any(i.code == code.strip().upper() for i in self.lister_caisses()):
            raise DomainError("Cette caisse existe déjà.")
        item = Caisse(code=code, libelle=libelle)
        self._depot.enregistrer_caisse(item)
        return item

    def creer(
        self, *, code: str, nom: str, role: str, poste_id: UUID | None, caisse: str
    ) -> CompteOperation:
        if any(i.code == code.strip().upper() for i in self.lister()):
            raise DomainError("Ce code compte existe déjà.")
        item = CompteOperation(code=code, nom=nom, role=role, poste_id=poste_id, caisse=caisse)
        self._depot.enregistrer_compte(item)
        return item

    def modifier(
        self,
        item_id: UUID,
        *,
        code: str,
        nom: str,
        role: str,
        poste_id: UUID | None,
        caisse: str,
        actif: bool,
    ) -> CompteOperation:
        item = self._depot.obtenir_compte(item_id)
        if item is None:
            raise DomainError("Le compte est inconnu.")
        if any(i.code == code.strip().upper() and i.id != item.id for i in self.lister()):
            raise DomainError("Ce code compte existe déjà.")
        item.code = code.strip().upper()
        item.modifier(nom=nom, role=role, poste_id=poste_id, caisse=caisse, actif=actif)
        self._depot.enregistrer_compte(item)
        return item
