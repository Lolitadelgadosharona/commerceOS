"""Product intelligence foundation.

Revision ID: 0005_product_intelligence
Revises: 0004_opportunity_intelligence
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005_product_intelligence"
down_revision: str | None = "0004_opportunity_intelligence"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None
uuid = sa.Uuid()


def timestamps() -> list[sa.Column]:
    return [
        sa.Column("id", uuid, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
    ]


def product_fk() -> sa.ForeignKeyConstraint:
    return sa.ForeignKeyConstraint(["product_id"], ["product_hypotheses.id"], ondelete="CASCADE")


def indexes(table: str, product: bool = True) -> None:
    op.create_index(f"ix_{table}_organization_id", table, ["organization_id"])
    if product:
        op.create_index(f"ix_{table}_product_id", table, ["product_id"])


def upgrade() -> None:
    op.create_table(
        "product_hypotheses",
        *timestamps(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("opportunity_id", uuid, nullable=False),
        sa.Column("name", sa.String(250), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("customer_problem", sa.Text(), nullable=False),
        sa.Column("solution_description", sa.Text(), nullable=False),
        sa.Column("target_customer", sa.String(500), nullable=False),
        sa.Column("target_market", sa.String(250), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.CheckConstraint(
            "confidence_score >= 0 AND confidence_score <= 1", name="confidence_range"
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["opportunity_id"], ["market_opportunities.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes("product_hypotheses", product=False)
    op.create_index(
        "ix_product_hypotheses_opportunity_id", "product_hypotheses", ["opportunity_id"]
    )
    op.create_table(
        "product_economics",
        *timestamps(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("product_id", uuid, nullable=False),
        sa.Column("selling_price", sa.Numeric(14, 2), nullable=False),
        sa.Column("estimated_product_cost", sa.Numeric(14, 2), nullable=False),
        sa.Column("estimated_shipping_cost", sa.Numeric(14, 2), nullable=False),
        sa.Column("payment_cost", sa.Numeric(14, 2), nullable=False),
        sa.Column("estimated_marketing_cost", sa.Numeric(14, 2), nullable=False),
        sa.Column("contribution_margin", sa.Numeric(14, 2), nullable=False),
        sa.Column("margin_percentage", sa.Numeric(9, 4), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.CheckConstraint("selling_price > 0", name="selling_price_positive"),
        sa.CheckConstraint("estimated_product_cost >= 0", name="product_cost_nonnegative"),
        sa.CheckConstraint("estimated_shipping_cost >= 0", name="shipping_cost_nonnegative"),
        sa.CheckConstraint("payment_cost >= 0", name="payment_cost_nonnegative"),
        sa.CheckConstraint("estimated_marketing_cost >= 0", name="marketing_cost_nonnegative"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        product_fk(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_id"),
    )
    indexes("product_economics")
    op.create_table(
        "supplier_candidates",
        *timestamps(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("product_id", uuid, nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("supplier_reference", sa.String(500), nullable=False),
        sa.Column("estimated_cost", sa.Numeric(14, 2), nullable=False),
        sa.Column("minimum_order_quantity", sa.Integer(), nullable=False),
        sa.Column("lead_time", sa.String(200), nullable=False),
        sa.Column("quality_notes", sa.Text(), nullable=False),
        sa.Column("risk_level", sa.String(30), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        product_fk(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_id", "source_type", "supplier_reference"),
    )
    indexes("supplier_candidates")
    op.create_table(
        "product_risks",
        *timestamps(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("product_id", uuid, nullable=False),
        sa.Column("risk_type", sa.String(30), nullable=False),
        sa.Column("severity", sa.String(30), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        product_fk(),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes("product_risks")
    op.create_table(
        "product_investment_scores",
        *timestamps(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("product_id", uuid, nullable=False),
        sa.Column("opportunity_score", sa.Float(), nullable=False),
        sa.Column("margin_score", sa.Float(), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("competition_score", sa.Float(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("overall_score", sa.Float(), nullable=False),
        sa.Column("formula_version", sa.String(30), nullable=False),
        *[
            sa.CheckConstraint(
                f"{column} BETWEEN 0 AND 100", name=f"{column.removesuffix('_score')}_range"
            )
            for column in (
                "opportunity_score",
                "margin_score",
                "risk_score",
                "competition_score",
                "confidence_score",
                "overall_score",
            )
        ],
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        product_fk(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_id"),
    )
    indexes("product_investment_scores")


def downgrade() -> None:
    for table in (
        "product_investment_scores",
        "product_risks",
        "supplier_candidates",
        "product_economics",
        "product_hypotheses",
    ):
        op.drop_table(table)
