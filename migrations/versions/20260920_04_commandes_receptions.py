"""Add CIP7, brands and purchase order receipts."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260920_04"
down_revision: str | None = "20260920_03"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "marques",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("libelle", sa.String(120), nullable=False, unique=True),
    )
    with op.batch_alter_table("produits") as batch:
        batch.add_column(sa.Column("cip7", sa.String(7)))
        batch.add_column(sa.Column("marque_id", sa.String(36)))
        batch.create_unique_constraint("uq_produits_cip7", ["cip7"])
        batch.create_foreign_key("fk_produits_marque", "marques", ["marque_id"], ["id"])
    op.create_table(
        "commandes_achats",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("numero_interne", sa.String(40), nullable=False, unique=True),
        sa.Column(
            "fournisseur_id", sa.String(36), sa.ForeignKey("fournisseurs.id"), nullable=False
        ),
        sa.Column(
            "emplacement_id", sa.String(36), sa.ForeignKey("emplacements.id"), nullable=False
        ),
        sa.Column("date_commande", sa.Date(), nullable=False),
        sa.Column("date_arrivee", sa.Date(), nullable=False),
        sa.Column("numero_fournisseur", sa.String(100), nullable=False, server_default=""),
    )
    op.create_table(
        "lignes_commandes_achats",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "commande_id",
            sa.String(36),
            sa.ForeignKey("commandes_achats.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "conditionnement_id",
            sa.String(36),
            sa.ForeignKey("conditionnements.id"),
            nullable=False,
        ),
        sa.Column("designation", sa.String(300), nullable=False),
        sa.Column("cip7", sa.String(7), nullable=False, server_default=""),
        sa.Column("quantite_commandee", sa.Integer(), nullable=False),
        sa.Column("quantite_recue", sa.Integer(), nullable=False),
        sa.Column("numero_lot", sa.String(100), nullable=False),
        sa.Column("date_expiration", sa.Date(), nullable=False),
        sa.Column("prix_unitaire", sa.Numeric(14, 2), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("lignes_commandes_achats")
    op.drop_table("commandes_achats")
    with op.batch_alter_table("produits") as batch:
        batch.drop_constraint("fk_produits_marque", type_="foreignkey")
        batch.drop_constraint("uq_produits_cip7", type_="unique")
        batch.drop_column("marque_id")
        batch.drop_column("cip7")
    op.drop_table("marques")
