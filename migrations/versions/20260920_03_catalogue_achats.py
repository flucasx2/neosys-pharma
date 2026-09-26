"""Add active ingredients, suppliers and supplier prices."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260920_03"
down_revision: str | None = "20260919_02"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "principes_actifs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("libelle", sa.String(200), nullable=False, unique=True),
    )
    with op.batch_alter_table("produits") as batch:
        batch.add_column(sa.Column("principe_actif_id", sa.String(36)))
        batch.create_foreign_key(
            "fk_produits_principe_actif",
            "principes_actifs",
            ["principe_actif_id"],
            ["id"],
        )
    op.create_table(
        "fournisseurs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("code", sa.String(50), nullable=False, unique=True),
        sa.Column("raison_sociale", sa.String(200), nullable=False),
        sa.Column("telephone", sa.String(50), nullable=False, server_default=""),
        sa.Column("email", sa.String(200), nullable=False, server_default=""),
        sa.Column("actif", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_table(
        "tarifs_fournisseurs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "fournisseur_id",
            sa.String(36),
            sa.ForeignKey("fournisseurs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "conditionnement_id",
            sa.String(36),
            sa.ForeignKey("conditionnements.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("prix_achat", sa.Numeric(14, 2), nullable=False),
        sa.Column("reference_fournisseur", sa.String(100), nullable=False, server_default=""),
        sa.UniqueConstraint("fournisseur_id", "conditionnement_id"),
    )


def downgrade() -> None:
    op.drop_table("tarifs_fournisseurs")
    op.drop_table("fournisseurs")
    with op.batch_alter_table("produits") as batch:
        batch.drop_constraint("fk_produits_principe_actif", type_="foreignkey")
        batch.drop_column("principe_actif_id")
    op.drop_table("principes_actifs")
