"""Add sales preparation tables."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260919_02"
down_revision: str | None = "20260919_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "postes_vente",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("code", sa.String(50), nullable=False, unique=True),
        sa.Column("secteur_id", sa.String(36), nullable=False),
        sa.Column(
            "emplacement_id",
            sa.String(36),
            sa.ForeignKey("emplacements.id"),
            nullable=False,
        ),
    )
    op.create_table(
        "ventes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "poste_id",
            sa.String(36),
            sa.ForeignKey("postes_vente.id"),
            nullable=False,
        ),
        sa.Column("secteur_id", sa.String(36), nullable=False),
        sa.Column(
            "emplacement_id",
            sa.String(36),
            sa.ForeignKey("emplacements.id"),
            nullable=False,
        ),
        sa.Column("date_commerciale", sa.Date(), nullable=False),
        sa.Column("etat", sa.String(40), nullable=False),
    )
    op.create_table(
        "lignes_vente",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "vente_id",
            sa.String(36),
            sa.ForeignKey("ventes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "conditionnement_id",
            sa.String(36),
            sa.ForeignKey("conditionnements.id"),
            nullable=False,
        ),
        sa.Column("designation", sa.String(200), nullable=False),
        sa.Column("quantite", sa.Integer(), nullable=False),
        sa.Column("prix_unitaire", sa.Numeric(14, 2), nullable=False),
    )
    op.create_table(
        "allocations_lots",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "vente_id",
            sa.String(36),
            sa.ForeignKey("ventes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "ligne_vente_id",
            sa.String(36),
            sa.ForeignKey("lignes_vente.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("lot_id", sa.String(36), sa.ForeignKey("lots.id"), nullable=False),
        sa.Column("quantite", sa.Integer(), nullable=False),
        sa.Column("date_expiration", sa.Date(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("allocations_lots")
    op.drop_table("lignes_vente")
    op.drop_table("ventes")
    op.drop_table("postes_vente")
