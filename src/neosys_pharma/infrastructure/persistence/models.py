from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class PrincipeActifModel(Base):
    __tablename__ = "principes_actifs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    libelle: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)


class MarqueModel(Base):
    __tablename__ = "marques"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    libelle: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)


class ProduitModel(Base):
    __tablename__ = "produits"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    type_produit: Mapped[str] = mapped_column(String(30), nullable=False)
    reference: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    designation: Mapped[str] = mapped_column(String(200), nullable=False)
    cip7: Mapped[str | None] = mapped_column(String(7), unique=True)
    principe_actif_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("principes_actifs.id")
    )
    principe_actif: Mapped[str | None] = mapped_column(String(200))
    marque: Mapped[str | None] = mapped_column(String(120))
    marque_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("marques.id"))
    pris_en_charge_cnamgs: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="0"
    )
    taux_prise_en_charge_cnamgs: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("0"), server_default="0"
    )


class ConditionnementModel(Base):
    __tablename__ = "conditionnements"
    __table_args__ = (UniqueConstraint("produit_id", "code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    produit_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("produits.id", ondelete="CASCADE"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    libelle: Mapped[str] = mapped_column(String(200), nullable=False)
    prix_vente: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)


class FournisseurModel(Base):
    __tablename__ = "fournisseurs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    raison_sociale: Mapped[str] = mapped_column(String(200), nullable=False)
    telephone: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    email: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    actif: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class TarifFournisseurModel(Base):
    __tablename__ = "tarifs_fournisseurs"
    __table_args__ = (UniqueConstraint("fournisseur_id", "conditionnement_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    fournisseur_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("fournisseurs.id", ondelete="CASCADE"), nullable=False
    )
    conditionnement_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("conditionnements.id", ondelete="CASCADE"), nullable=False
    )
    prix_achat: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    reference_fournisseur: Mapped[str] = mapped_column(String(100), nullable=False, default="")


class OrganismePriseEnChargeModel(Base):
    __tablename__ = "organismes_prise_en_charge"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    nom: Mapped[str] = mapped_column(String(200), nullable=False)
    type_organisme: Mapped[str] = mapped_column(String(40), nullable=False)
    documents_requis: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    actif: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    taux_prise_en_charge: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("0"), server_default="0"
    )


class ClientFideliteModel(Base):
    __tablename__ = "clients_fidelite"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    nom: Mapped[str] = mapped_column(String(150), nullable=False)
    prenom: Mapped[str] = mapped_column(String(150), nullable=False, default="")
    telephone: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    email: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    actif: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class CarteFideliteModel(Base):
    __tablename__ = "cartes_fidelite"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    numero: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    client_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("clients_fidelite.id"), nullable=False
    )
    type_carte: Mapped[str] = mapped_column(String(20), nullable=False)
    points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    actif: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class MouvementFideliteModel(Base):
    __tablename__ = "mouvements_fidelite"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    carte_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cartes_fidelite.id"), nullable=False
    )
    points: Mapped[int] = mapped_column(Integer, nullable=False)
    motif: Mapped[str] = mapped_column(String(300), nullable=False)
    solde_apres: Mapped[int] = mapped_column(Integer, nullable=False)
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CommandeAchatModel(Base):
    __tablename__ = "commandes_achats"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    numero_interne: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    fournisseur_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("fournisseurs.id"), nullable=False
    )
    emplacement_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("emplacements.id"), nullable=False
    )
    date_commande: Mapped[date] = mapped_column(Date, nullable=False)
    date_arrivee: Mapped[date] = mapped_column(Date, nullable=False)
    numero_fournisseur: Mapped[str] = mapped_column(String(100), nullable=False, default="")


class LigneCommandeAchatModel(Base):
    __tablename__ = "lignes_commandes_achats"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    commande_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("commandes_achats.id", ondelete="CASCADE"), nullable=False
    )
    conditionnement_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("conditionnements.id"), nullable=False
    )
    designation: Mapped[str] = mapped_column(String(300), nullable=False)
    cip7: Mapped[str] = mapped_column(String(7), nullable=False, default="")
    quantite_commandee: Mapped[int] = mapped_column(Integer, nullable=False)
    quantite_recue: Mapped[int] = mapped_column(Integer, nullable=False)
    numero_lot: Mapped[str] = mapped_column(String(100), nullable=False)
    date_expiration: Mapped[date] = mapped_column(Date, nullable=False)
    prix_unitaire: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)


class LotModel(Base):
    __tablename__ = "lots"
    __table_args__ = (UniqueConstraint("conditionnement_id", "numero"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    conditionnement_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("conditionnements.id"), nullable=False
    )
    numero: Mapped[str] = mapped_column(String(100), nullable=False)
    date_expiration: Mapped[date] = mapped_column(Date, nullable=False)
    etat: Mapped[str] = mapped_column(String(30), nullable=False)


class EmplacementModel(Base):
    __tablename__ = "emplacements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    libelle: Mapped[str] = mapped_column(String(120), nullable=False)
    autorise_vente: Mapped[bool] = mapped_column(Boolean, nullable=False)


class StockEmplacementModel(Base):
    __tablename__ = "stocks_emplacements"

    lot_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("lots.id", ondelete="CASCADE"), primary_key=True
    )
    emplacement_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("emplacements.id"), primary_key=True
    )
    quantite_physique: Mapped[int] = mapped_column(Integer, nullable=False)
    quantite_reservee: Mapped[int] = mapped_column(Integer, nullable=False)


class MouvementStockModel(Base):
    __tablename__ = "mouvements_stock"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    type_mouvement: Mapped[str] = mapped_column(String(40), nullable=False)
    lot_id: Mapped[str] = mapped_column(String(36), ForeignKey("lots.id"), nullable=False)
    quantite: Mapped[int] = mapped_column(Integer, nullable=False)
    emplacement_source_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("emplacements.id")
    )
    emplacement_destination_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("emplacements.id")
    )
    motif: Mapped[str] = mapped_column(String(300), nullable=False)
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PosteVenteModel(Base):
    __tablename__ = "postes_vente"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    secteur_id: Mapped[str] = mapped_column(String(36), nullable=False)
    emplacement_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("emplacements.id"), nullable=False
    )
    caisse_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("caisses.id"))


class CaisseModel(Base):
    __tablename__ = "caisses"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    libelle: Mapped[str] = mapped_column(String(150), nullable=False)
    actif: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class CompteOperationModel(Base):
    __tablename__ = "comptes_operation"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    nom: Mapped[str] = mapped_column(String(150), nullable=False)
    role: Mapped[str] = mapped_column(String(30), nullable=False)
    poste_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("postes_vente.id"))
    caisse: Mapped[str] = mapped_column(String(50), nullable=False)
    actif: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class VenteModel(Base):
    __tablename__ = "ventes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    poste_id: Mapped[str] = mapped_column(String(36), ForeignKey("postes_vente.id"), nullable=False)
    secteur_id: Mapped[str] = mapped_column(String(36), nullable=False)
    emplacement_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("emplacements.id"), nullable=False
    )
    date_commerciale: Mapped[date] = mapped_column(Date, nullable=False)
    etat: Mapped[str] = mapped_column(String(40), nullable=False)
    organisme_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("organismes_prise_en_charge.id")
    )
    patient_nom: Mapped[str] = mapped_column(String(150), nullable=False, default="")
    patient_prenom: Mapped[str] = mapped_column(String(150), nullable=False, default="")
    informations_prise_en_charge: Mapped[dict[str, str]] = mapped_column(
        JSON, nullable=False, default=dict
    )
    encaissement_id: Mapped[str | None] = mapped_column(String(36))
    reglements: Mapped[list[dict[str, str]]] = mapped_column(JSON, nullable=False, default=list)
    carte_fidelite_id: Mapped[str | None] = mapped_column(String(36))
    points_utilises: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    encaissee_le: Mapped[datetime | None] = mapped_column(DateTime)


class LigneVenteModel(Base):
    __tablename__ = "lignes_vente"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    vente_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("ventes.id", ondelete="CASCADE"), nullable=False
    )
    conditionnement_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("conditionnements.id"), nullable=False
    )
    designation: Mapped[str] = mapped_column(String(200), nullable=False)
    quantite: Mapped[int] = mapped_column(Integer, nullable=False)
    prix_unitaire: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)


class AllocationLotModel(Base):
    __tablename__ = "allocations_lots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    vente_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("ventes.id", ondelete="CASCADE"), nullable=False
    )
    ligne_vente_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("lignes_vente.id", ondelete="CASCADE"), nullable=False
    )
    lot_id: Mapped[str] = mapped_column(String(36), ForeignKey("lots.id"), nullable=False)
    quantite: Mapped[int] = mapped_column(Integer, nullable=False)
    date_expiration: Mapped[date] = mapped_column(Date, nullable=False)
    emplacement_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("emplacements.id"))
