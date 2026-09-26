"""Ajoute les clients et cartes de fidélité."""

import sqlalchemy as sa
from alembic import op

revision = "20260920_06"
down_revision = "20260920_05"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "clients_fidelite",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("code", sa.String(50), nullable=False, unique=True),
        sa.Column("nom", sa.String(150), nullable=False),
        sa.Column("prenom", sa.String(150), nullable=False),
        sa.Column("telephone", sa.String(50), nullable=False),
        sa.Column("email", sa.String(200), nullable=False),
        sa.Column("actif", sa.Boolean(), nullable=False),
    )
    op.create_table(
        "cartes_fidelite",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("numero", sa.String(50), nullable=False, unique=True),
        sa.Column("client_id", sa.String(36), sa.ForeignKey("clients_fidelite.id"), nullable=False),
        sa.Column("type_carte", sa.String(20), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("actif", sa.Boolean(), nullable=False),
        sa.Column("cree_le", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "mouvements_fidelite",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("carte_id", sa.String(36), sa.ForeignKey("cartes_fidelite.id"), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("motif", sa.String(300), nullable=False),
        sa.Column("solde_apres", sa.Integer(), nullable=False),
        sa.Column("cree_le", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("mouvements_fidelite")
    op.drop_table("cartes_fidelite")
    op.drop_table("clients_fidelite")
