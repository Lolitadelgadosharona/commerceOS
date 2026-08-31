"""Intelligence provenance foundation.

Revision ID: 0071_intelligence_provenance
Revises: 0066_live_revenue_support
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0071_intelligence_provenance"
down_revision: str | None = "0066_live_revenue_support"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "product_economic_input_provenance",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("product_economics_id", sa.Uuid(), nullable=False),
        sa.Column("metric", sa.String(60), nullable=False),
        sa.Column("value", sa.Numeric(14, 4), nullable=True),
        sa.Column("classification", sa.String(30), nullable=False),
        sa.Column("source", sa.String(250), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("as_of", sa.DateTime(timezone=True), nullable=True),
        sa.Column("evidence_reference", sa.String(500), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "value IS NULL OR value >= 0",
            name=op.f("ck_product_economic_input_provenance_value_nonnegative"),
        ),
        sa.CheckConstraint(
            "confidence IS NULL OR confidence BETWEEN 0 AND 1",
            name=op.f("ck_product_economic_input_provenance_confidence_range"),
        ),
        sa.CheckConstraint(
            "(classification = 'unknown' AND value IS NULL) OR "
            "(classification <> 'unknown' AND value IS NOT NULL)",
            name=op.f("ck_product_economic_input_provenance_unknown_value_semantics"),
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["product_economics_id"],
            ["product_economics.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_economics_id", "metric"),
    )
    op.create_index(
        op.f("ix_product_economic_input_provenance_organization_id"),
        "product_economic_input_provenance",
        ["organization_id"],
    )
    op.create_index(
        op.f("ix_product_economic_input_provenance_product_economics_id"),
        "product_economic_input_provenance",
        ["product_economics_id"],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_product_economic_input_provenance_product_economics_id"),
        table_name="product_economic_input_provenance",
    )
    op.drop_index(
        op.f("ix_product_economic_input_provenance_organization_id"),
        table_name="product_economic_input_provenance",
    )
    op.drop_table("product_economic_input_provenance")
