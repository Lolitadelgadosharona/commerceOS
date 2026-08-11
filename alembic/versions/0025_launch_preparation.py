"""Product launch preparation foundation."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0025_launch_preparation"
down_revision: str | None = "0024_product_economics"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None
uuid = sa.Uuid()


def common() -> list[sa.Column]:
    return [
        sa.Column("id", uuid, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("product_id", uuid, nullable=False),
    ]


def constraints() -> list[sa.Constraint]:
    return [
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    ]


def indexes(table: str) -> None:
    op.create_index(f"ix_{table}_organization_id", table, ["organization_id"])
    op.create_index(f"ix_{table}_product_id", table, ["product_id"])


def upgrade() -> None:
    op.create_table(
        "product_positioning",
        *common(),
        sa.Column("target_customer", sa.Text(), nullable=False),
        sa.Column("customer_problem", sa.Text(), nullable=False),
        sa.Column("primary_benefit", sa.Text(), nullable=False),
        sa.Column("differentiation", sa.Text(), nullable=False),
        sa.Column("positioning_statement", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),
        *constraints(),
    )
    indexes("product_positioning")
    op.create_table(
        "offer_strategies",
        *common(),
        sa.Column("pricing_hypothesis", sa.Text(), nullable=False),
        sa.Column("bundle_strategy", sa.Text(), nullable=False),
        sa.Column("guarantee_strategy", sa.Text(), nullable=False),
        sa.Column("bonus_strategy", sa.Text(), nullable=False),
        sa.Column("urgency_strategy", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),
        *constraints(),
    )
    indexes("offer_strategies")
    op.create_table(
        "product_objection_maps",
        *common(),
        sa.Column("objection_type", sa.String(80), nullable=False),
        sa.Column("customer_language", sa.Text(), nullable=False),
        sa.Column("recommended_response", sa.Text(), nullable=False),
        sa.Column("evidence_reference", sa.String(500), nullable=False),
        *constraints(),
    )
    indexes("product_objection_maps")
    op.create_table(
        "launch_preparation_packages",
        *common(),
        sa.Column("positioning_status", sa.String(20), nullable=False),
        sa.Column("offer_status", sa.String(20), nullable=False),
        sa.Column("objection_status", sa.String(20), nullable=False),
        sa.Column("creative_readiness", sa.String(20), nullable=False),
        sa.Column("listing_readiness", sa.String(20), nullable=False),
        sa.Column("launch_score", sa.Float(), nullable=False),
        sa.CheckConstraint("launch_score BETWEEN 0 AND 100", name="score_range"),
        *constraints(),
    )
    indexes("launch_preparation_packages")


def downgrade() -> None:
    for table in (
        "launch_preparation_packages",
        "product_objection_maps",
        "offer_strategies",
        "product_positioning",
    ):
        op.drop_table(table)
