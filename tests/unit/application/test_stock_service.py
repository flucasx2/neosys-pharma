from datetime import date
from uuid import uuid4

import pytest

from neosys_pharma.application.dto import AjusterStock, ReceptionnerLot, TransfererStock
from neosys_pharma.application.services import StockService
from neosys_pharma.domain.shared import DomainError
from neosys_pharma.domain.stock import Inventaire, TypeMouvement
from neosys_pharma.infrastructure.persistence import InMemoryStockRepository


def _service() -> tuple[StockService, InMemoryStockRepository]:
    depot = InMemoryStockRepository()
    return StockService(depot, Inventaire()), depot


def test_receptionner_puis_consulter_un_lot() -> None:
    service, depot = _service()
    rayon = service.creer_emplacement(code="RAY-1", libelle="Rayon 1")
    conditionnement_id = uuid4()

    lot = service.receptionner_lot(
        ReceptionnerLot(
            conditionnement_id=conditionnement_id,
            numero_lot="LOT-APP-001",
            date_expiration=date(2027, 12, 31),
            emplacement_id=rayon.id,
            quantite=20,
            motif="Bon de livraison BL-100",
        )
    )

    lignes = service.consulter_stock(
        conditionnement_id=conditionnement_id,
        emplacement_id=rayon.id,
    )
    assert len(lignes) == 1
    assert lignes[0].lot_id == lot.id
    assert lignes[0].quantite_disponible == 20
    assert depot.lister_mouvements()[0].type is TypeMouvement.RECEPTION


def test_transferer_et_ajuster_le_stock() -> None:
    service, depot = _service()
    reserve = service.creer_emplacement(code="RES-1", libelle="Réserve", autorise_vente=False)
    rayon = service.creer_emplacement(code="RAY-1", libelle="Rayon 1")
    lot = service.receptionner_lot(
        ReceptionnerLot(
            conditionnement_id=uuid4(),
            numero_lot="LOT-APP-002",
            date_expiration=date(2028, 1, 31),
            emplacement_id=reserve.id,
            quantite=30,
            motif="Réception",
        )
    )

    service.transferer(
        TransfererStock(
            lot_id=lot.id,
            source_id=reserve.id,
            destination_id=rayon.id,
            quantite=10,
            motif="Réassort",
        )
    )
    mouvement = service.ajuster(
        AjusterStock(
            lot_id=lot.id,
            emplacement_id=rayon.id,
            nouvelle_quantite=9,
            motif="Un article cassé",
        )
    )

    assert depot.obtenir_position(lot_id=lot.id, emplacement_id=reserve.id).quantite_physique == 20  # type: ignore[union-attr]
    assert depot.obtenir_position(lot_id=lot.id, emplacement_id=rayon.id).quantite_physique == 9  # type: ignore[union-attr]
    assert mouvement is not None
    assert mouvement.type is TypeMouvement.AJUSTEMENT_NEGATIF
    assert len(depot.lister_mouvements()) == 4


def test_receptionner_dans_un_emplacement_inconnu_est_refuse() -> None:
    service, _ = _service()

    with pytest.raises(DomainError, match="emplacement est inconnu"):
        service.receptionner_lot(
            ReceptionnerLot(
                conditionnement_id=uuid4(),
                numero_lot="LOT-APP-003",
                date_expiration=date(2028, 2, 29),
                emplacement_id=uuid4(),
                quantite=5,
                motif="Réception",
            )
        )


def test_consulter_un_emplacement_inconnu_est_refuse() -> None:
    service, _ = _service()

    with pytest.raises(DomainError, match="emplacement est inconnu"):
        service.consulter_stock(
            conditionnement_id=uuid4(),
            emplacement_id=uuid4(),
        )
