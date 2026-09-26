"""Add CNAMGS coverage and coverage organizations."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260920_05"
down_revision: str | None = "20260920_04"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("produits") as batch:
        batch.add_column(
            sa.Column(
                "pris_en_charge_cnamgs",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )
        batch.add_column(
            sa.Column(
                "taux_prise_en_charge_cnamgs",
                sa.Numeric(5, 2),
                nullable=False,
                server_default="0",
            )
        )
    op.create_table(
        "organismes_prise_en_charge",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("code", sa.String(50), nullable=False, unique=True),
        sa.Column("nom", sa.String(200), nullable=False),
        sa.Column("type_organisme", sa.String(40), nullable=False),
        sa.Column("documents_requis", sa.JSON(), nullable=False),
        sa.Column("actif", sa.Boolean(), nullable=False, server_default=sa.true()),
    )


def downgrade() -> None:
    op.drop_table("organismes_prise_en_charge")
    with op.batch_alter_table("produits") as batch:
        batch.drop_column("taux_prise_en_charge_cnamgs")
        batch.drop_column("pris_en_charge_cnamgs")
