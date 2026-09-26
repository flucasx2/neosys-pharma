from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from neosys_pharma.domain.catalogue import CarteFidelite, ClientFidelite, MouvementFidelite
from neosys_pharma.infrastructure.persistence.database import session_scope
from neosys_pharma.infrastructure.persistence.models import (
    CarteFideliteModel,
    ClientFideliteModel,
    MouvementFideliteModel,
)


class SqlAlchemyFideliteRepository:
    def __init__(self, factory: sessionmaker[Session]) -> None:
        self._factory = factory

    def enregistrer_client_fidelite(self, item: ClientFidelite) -> None:
        with session_scope(self._factory) as s:
            s.merge(
                ClientFideliteModel(
                    id=str(item.id),
                    code=item.code,
                    nom=item.nom,
                    prenom=item.prenom,
                    telephone=item.telephone,
                    email=item.email,
                    actif=item.actif,
                )
            )

    def obtenir_client_fidelite(self, item_id: UUID) -> ClientFidelite | None:
        with session_scope(self._factory) as s:
            m = s.get(ClientFideliteModel, str(item_id))
            return None if m is None else self._client(m)

    def lister_clients_fidelite(self) -> tuple[ClientFidelite, ...]:
        with session_scope(self._factory) as s:
            return tuple(
                self._client(m)
                for m in s.scalars(
                    select(ClientFideliteModel).order_by(ClientFideliteModel.nom)
                ).all()
            )

    def enregistrer_carte_fidelite(self, item: CarteFidelite) -> None:
        with session_scope(self._factory) as s:
            s.merge(
                CarteFideliteModel(
                    id=str(item.id),
                    numero=item.numero,
                    client_id=str(item.client_id),
                    type_carte=item.type_carte,
                    points=item.points,
                    actif=item.actif,
                    cree_le=item.cree_le,
                )
            )

    def obtenir_carte_fidelite(self, item_id: UUID) -> CarteFidelite | None:
        with session_scope(self._factory) as s:
            m = s.get(CarteFideliteModel, str(item_id))
            return None if m is None else self._carte(m)

    def lister_cartes_fidelite(self) -> tuple[CarteFidelite, ...]:
        with session_scope(self._factory) as s:
            return tuple(
                self._carte(m)
                for m in s.scalars(
                    select(CarteFideliteModel).order_by(CarteFideliteModel.numero)
                ).all()
            )

    def enregistrer_mouvement_fidelite(self, item: MouvementFidelite) -> None:
        with session_scope(self._factory) as s:
            s.merge(
                MouvementFideliteModel(
                    id=str(item.id),
                    carte_id=str(item.carte_id),
                    points=item.points,
                    motif=item.motif,
                    solde_apres=item.solde_apres,
                    cree_le=item.cree_le,
                )
            )

    def lister_mouvements_fidelite(self, carte_id: UUID) -> tuple[MouvementFidelite, ...]:
        with session_scope(self._factory) as s:
            return tuple(
                self._mouvement(m)
                for m in s.scalars(
                    select(MouvementFideliteModel)
                    .where(MouvementFideliteModel.carte_id == str(carte_id))
                    .order_by(MouvementFideliteModel.cree_le.desc())
                ).all()
            )

    @staticmethod
    def _client(m: ClientFideliteModel) -> ClientFidelite:
        return ClientFidelite(
            id=UUID(m.id),
            code=m.code,
            nom=m.nom,
            prenom=m.prenom,
            telephone=m.telephone,
            email=m.email,
            actif=m.actif,
        )

    @staticmethod
    def _carte(m: CarteFideliteModel) -> CarteFidelite:
        return CarteFidelite(
            id=UUID(m.id),
            numero=m.numero,
            client_id=UUID(m.client_id),
            type_carte=m.type_carte,
            points=m.points,
            actif=m.actif,
            cree_le=m.cree_le,
        )

    @staticmethod
    def _mouvement(m: MouvementFideliteModel) -> MouvementFidelite:
        return MouvementFidelite(
            id=UUID(m.id),
            carte_id=UUID(m.carte_id),
            points=m.points,
            motif=m.motif,
            solde_apres=m.solde_apres,
            cree_le=m.cree_le,
        )
