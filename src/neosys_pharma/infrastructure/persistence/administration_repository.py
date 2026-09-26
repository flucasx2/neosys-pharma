from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from neosys_pharma.domain.administration import Caisse, CompteOperation
from neosys_pharma.infrastructure.persistence.database import session_scope
from neosys_pharma.infrastructure.persistence.models import CaisseModel, CompteOperationModel


class SqlAlchemyAdministrationRepository:
    def __init__(self, factory: sessionmaker[Session]) -> None:
        self._factory = factory

    def enregistrer_caisse(self, item: Caisse) -> None:
        with session_scope(self._factory) as s:
            s.merge(
                CaisseModel(id=str(item.id), code=item.code, libelle=item.libelle, actif=item.actif)
            )

    def lister_caisses(self) -> tuple[Caisse, ...]:
        with session_scope(self._factory) as s:
            return tuple(
                Caisse(id=UUID(m.id), code=m.code, libelle=m.libelle, actif=m.actif)
                for m in s.scalars(select(CaisseModel).order_by(CaisseModel.code)).all()
            )

    def enregistrer_compte(self, item: CompteOperation) -> None:
        with session_scope(self._factory) as s:
            s.merge(
                CompteOperationModel(
                    id=str(item.id),
                    code=item.code,
                    nom=item.nom,
                    role=item.role,
                    poste_id=str(item.poste_id) if item.poste_id else None,
                    caisse=item.caisse,
                    actif=item.actif,
                )
            )

    def obtenir_compte(self, item_id: UUID) -> CompteOperation | None:
        with session_scope(self._factory) as s:
            m = s.get(CompteOperationModel, str(item_id))
            return None if m is None else self._domain(m)

    def lister_comptes(self) -> tuple[CompteOperation, ...]:
        with session_scope(self._factory) as s:
            return tuple(
                self._domain(m)
                for m in s.scalars(
                    select(CompteOperationModel).order_by(CompteOperationModel.code)
                ).all()
            )

    @staticmethod
    def _domain(m: CompteOperationModel) -> CompteOperation:
        return CompteOperation(
            id=UUID(m.id),
            code=m.code,
            nom=m.nom,
            role=m.role,
            poste_id=UUID(m.poste_id) if m.poste_id else None,
            caisse=m.caisse,
            actif=m.actif,
        )
