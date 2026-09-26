"""Sépare caisses et conserve les informations patient."""

import sqlalchemy as sa
from alembic import op

revision = "20260921_08"
down_revision = "20260920_07"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "caisses",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("code", sa.String(50), unique=True, nullable=False),
        sa.Column("libelle", sa.String(150), nullable=False),
        sa.Column("actif", sa.Boolean(), nullable=False),
    )
    with op.batch_alter_table("postes_vente") as b:
        b.add_column(sa.Column("caisse_id", sa.String(36), sa.ForeignKey("caisses.id")))
    with op.batch_alter_table("ventes") as b:
        b.add_column(
            sa.Column("organisme_id", sa.String(36), sa.ForeignKey("organismes_prise_en_charge.id"))
        )
        b.add_column(sa.Column("patient_nom", sa.String(150), nullable=False, server_default=""))
        b.add_column(sa.Column("patient_prenom", sa.String(150), nullable=False, server_default=""))
        b.add_column(
            sa.Column(
                "informations_prise_en_charge", sa.JSON(), nullable=False, server_default="{}"
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("ventes") as b:
        b.drop_column("informations_prise_en_charge")
        b.drop_column("patient_prenom")
        b.drop_column("patient_nom")
        b.drop_column("organisme_id")
    with op.batch_alter_table("postes_vente") as b:
        b.drop_column("caisse_id")
    op.drop_table("caisses")
