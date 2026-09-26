from typing import Protocol
from uuid import UUID

from neosys_pharma.domain.catalogue import CarteFidelite, ClientFidelite, MouvementFidelite
from neosys_pharma.domain.shared import DomainError


class FideliteRepository(Protocol):
    def enregistrer_client_fidelite(self, item: ClientFidelite) -> None: ...
    def obtenir_client_fidelite(self, item_id: UUID) -> ClientFidelite | None: ...
    def lister_clients_fidelite(self) -> tuple[ClientFidelite, ...]: ...
    def enregistrer_carte_fidelite(self, item: CarteFidelite) -> None: ...
    def obtenir_carte_fidelite(self, item_id: UUID) -> CarteFidelite | None: ...
    def lister_cartes_fidelite(self) -> tuple[CarteFidelite, ...]: ...
    def enregistrer_mouvement_fidelite(self, item: MouvementFidelite) -> None: ...
    def lister_mouvements_fidelite(self, carte_id: UUID) -> tuple[MouvementFidelite, ...]: ...


class FideliteService:
    def __init__(self, depot: FideliteRepository) -> None:
        self._depot = depot

    def lister_clients(self) -> tuple[ClientFidelite, ...]:
        return self._depot.lister_clients_fidelite()

    def lister_cartes(self) -> tuple[CarteFidelite, ...]:
        return self._depot.lister_cartes_fidelite()

    def lister_mouvements(self, carte_id: UUID) -> tuple[MouvementFidelite, ...]:
        return self._depot.lister_mouvements_fidelite(carte_id)

    def rechercher_carte(self, numero: str) -> tuple[CarteFidelite, ClientFidelite]:
        numero_normalise = numero.strip().upper()
        carte = next(
            (item for item in self.lister_cartes() if item.numero == numero_normalise),
            None,
        )
        if carte is None:
            raise DomainError("La carte de fidélité est inconnue.")
        if not carte.actif:
            raise DomainError("La carte de fidélité est inactive.")
        client = self._depot.obtenir_client_fidelite(carte.client_id)
        if client is None or not client.actif:
            raise DomainError("Le client associé à cette carte est inactif.")
        return carte, client

    def creer_client(self, *, nom: str, prenom: str, telephone: str, email: str) -> ClientFidelite:
        index = len(self.lister_clients()) + 1
        codes = {item.code for item in self.lister_clients()}
        while f"CLI-{index:05d}" in codes:
            index += 1
        client = ClientFidelite(
            code=f"CLI-{index:05d}", nom=nom, prenom=prenom, telephone=telephone, email=email
        )
        self._depot.enregistrer_client_fidelite(client)
        return client

    def modifier_client(
        self, client_id: UUID, *, nom: str, prenom: str, telephone: str, email: str, actif: bool
    ) -> ClientFidelite:
        client = self._depot.obtenir_client_fidelite(client_id)
        if client is None:
            raise DomainError("Le client est inconnu.")
        client.modifier(nom=nom, prenom=prenom, telephone=telephone, email=email, actif=actif)
        self._depot.enregistrer_client_fidelite(client)
        return client

    def creer_carte(self, *, client_id: UUID, type_carte: str) -> CarteFidelite:
        if self._depot.obtenir_client_fidelite(client_id) is None:
            raise DomainError("Le client est inconnu.")
        if any(item.client_id == client_id for item in self.lister_cartes()):
            raise DomainError("Ce client possède déjà une carte de fidélité.")
        index = len(self.lister_cartes()) + 1
        numeros = {item.numero for item in self.lister_cartes()}
        while f"FID-{index:06d}" in numeros:
            index += 1
        carte = CarteFidelite(numero=f"FID-{index:06d}", client_id=client_id, type_carte=type_carte)
        self._depot.enregistrer_carte_fidelite(carte)
        return carte

    def modifier_carte(self, carte_id: UUID, *, type_carte: str, actif: bool) -> CarteFidelite:
        carte = self._depot.obtenir_carte_fidelite(carte_id)
        if carte is None:
            raise DomainError("La carte est inconnue.")
        carte.modifier(type_carte=type_carte, actif=actif)
        self._depot.enregistrer_carte_fidelite(carte)
        return carte

    def ajuster_points(self, carte_id: UUID, *, points: int, motif: str) -> MouvementFidelite:
        carte = self._depot.obtenir_carte_fidelite(carte_id)
        if carte is None:
            raise DomainError("La carte est inconnue.")
        if not carte.actif:
            raise DomainError("La carte est inactive.")
        mouvement = MouvementFidelite(
            carte_id=carte.id, points=points, motif=motif, solde_apres=carte.ajuster_points(points)
        )
        self._depot.enregistrer_carte_fidelite(carte)
        self._depot.enregistrer_mouvement_fidelite(mouvement)
        return mouvement
