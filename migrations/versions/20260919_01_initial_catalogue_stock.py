"""Initial catalogue and stock schema."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260919_01"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "produits",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("type_produit", sa.String(30), nullable=False),
        sa.Column("reference", sa.String(50), nullable=False, unique=True),
        sa.Column("designation", sa.String(200), nullable=False),
        sa.Column("principe_actif", sa.String(200)),
        sa.Column("marque", sa.String(120)),
    )
    op.create_table(
        "emplacements",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("code", sa.String(50), nullable=False, unique=True),
        sa.Column("libelle", sa.String(120), nullable=False),
        sa.Column("autorise_vente", sa.Boolean(), nullable=False),
    )
    op.create_table(
        "conditionnements",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "produit_id",
            sa.String(36),
            sa.ForeignKey("produits.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("libelle", sa.String(200), nullable=False),
        sa.Column("prix_vente", sa.Numeric(14, 2), nullable=False),
        sa.UniqueConstraint("produit_id", "code"),
    )
    op.create_table(
        "lots",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "conditionnement_id",
            sa.String(36),
            sa.ForeignKey("conditionnements.id"),
            nullable=False,
        ),
        sa.Column("numero", sa.String(100), nullable=False),
        sa.Column("date_expiration", sa.Date(), nullable=False),
        sa.Column("etat", sa.String(30), nullable=False),
        sa.UniqueConstraint("conditionnement_id", "numero"),
    )
    op.create_table(
        "stocks_emplacements",
        sa.Column(
            "lot_id",
            sa.String(36),
            sa.ForeignKey("lots.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "emplacement_id",
            sa.String(36),
            sa.ForeignKey("emplacements.id"),
            primary_key=True,
        ),
        sa.Column("quantite_physique", sa.Integer(), nullable=False),
        sa.Column("quantite_reservee", sa.Integer(), nullable=False),
    )
    op.create_table(
        "mouvements_stock",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("type_mouvement", sa.String(40), nullable=False),
        sa.Column("lot_id", sa.String(36), sa.ForeignKey("lots.id"), nullable=False),
        sa.Column(
            "emplacement_source_id",
            sa.String(36),
            sa.ForeignKey("emplacements.id"),
        ),
        sa.Column(
            "emplacement_destination_id",
            sa.String(36),
            sa.ForeignKey("emplacements.id"),
        ),
        sa.Column("quantite", sa.Integer(), nullable=False),
        sa.Column("motif", sa.String(300), nullable=False),
        sa.Column("cree_le", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("mouvements_stock")
    op.drop_table("stocks_emplacements")
    op.drop_table("lots")
    op.drop_table("conditionnements")
    op.drop_table("emplacements")
    op.drop_table("produits")
