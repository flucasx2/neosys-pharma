"""Ajoute taux organismes et comptes opérateurs."""

import sqlalchemy as sa
from alembic import op

revision = "20260920_07"
down_revision = "20260920_06"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("organismes_prise_en_charge") as batch:
        batch.add_column(
            sa.Column("taux_prise_en_charge", sa.Numeric(5, 2), nullable=False, server_default="0")
        )
    op.create_table(
        "comptes_operation",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("code", sa.String(50), unique=True, nullable=False),
        sa.Column("nom", sa.String(150), nullable=False),
        sa.Column("role", sa.String(30), nullable=False),
        sa.Column("poste_id", sa.String(36), sa.ForeignKey("postes_vente.id")),
        sa.Column("caisse", sa.String(50), nullable=False),
        sa.Column("actif", sa.Boolean(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("comptes_operation")
    with op.batch_alter_table("organismes_prise_en_charge") as batch:
        batch.drop_column("taux_prise_en_charge")
