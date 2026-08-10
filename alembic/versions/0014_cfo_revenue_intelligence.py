"""CFO and revenue intelligence foundation.

Revision ID: 0014_cfo_revenue
Revises: 0013_creative_router
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0014_cfo_revenue"
down_revision: str | None = "0013_creative_router"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None
uuid = sa.Uuid()


def common() -> list[sa.Column]:
    return [
        sa.Column("id", uuid, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
    ]


def indexes(table: str, reference: str) -> None:
    op.create_index(f"ix_{table}_organization_id", table, ["organization_id"])
    op.create_index(f"ix_{table}_{reference}", table, [reference])


def org() -> sa.ForeignKeyConstraint:
    return sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"])


def upgrade() -> None:
    op.create_table(
        "financial_periods",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("period_type", sa.String(20), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.CheckConstraint("end_date >= start_date", name="valid_date_range"),
        org(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_financial_periods_organization_id", "financial_periods", ["organization_id"]
    )
    op.create_table(
        "revenue_observations",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("project_id", uuid, nullable=False),
        sa.Column("product_id", uuid),
        sa.Column("channel", sa.String(80)),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("source_type", sa.String(30), nullable=False),
        sa.Column("observation_date", sa.Date(), nullable=False),
        sa.CheckConstraint("amount >= 0", name="nonnegative_amount"),
        org(),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes("revenue_observations", "project_id")
    op.create_index("ix_revenue_observations_product_id", "revenue_observations", ["product_id"])
    op.create_table(
        "cost_observations",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("product_id", uuid, nullable=False),
        sa.Column("channel", sa.String(80)),
        sa.Column("category", sa.String(40), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("observation_date", sa.Date(), nullable=False),
        sa.CheckConstraint("amount >= 0", name="nonnegative_amount"),
        org(),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes("cost_observations", "product_id")
    op.create_table(
        "contribution_profit_assessments",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("product_id", uuid, nullable=False),
        sa.Column("period_id", uuid, nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("revenue", sa.Numeric(18, 2), nullable=False),
        sa.Column("cost", sa.Numeric(18, 2), nullable=False),
        sa.Column("contribution_profit", sa.Numeric(18, 2), nullable=False),
        sa.Column("margin_percentage", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("component_snapshot", sa.JSON(), nullable=False),
        sa.Column("formula_version", sa.String(40), nullable=False),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),
        org(),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["period_id"], ["financial_periods.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes("contribution_profit_assessments", "product_id")
    op.create_index(
        "ix_contribution_profit_assessments_period_id",
        "contribution_profit_assessments",
        ["period_id"],
    )
    op.create_table(
        "unit_economic_assessments",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("product_id", uuid, nullable=False),
        sa.Column("average_order_value", sa.Numeric(18, 2), nullable=False),
        sa.Column("customer_acquisition_cost", sa.Numeric(18, 2), nullable=False),
        sa.Column("gross_margin", sa.Float(), nullable=False),
        sa.Column("refund_rate", sa.Float(), nullable=False),
        sa.Column("dispute_rate", sa.Float(), nullable=False),
        sa.Column("lifetime_value_estimate", sa.Numeric(18, 2), nullable=False),
        sa.Column("profitability_score", sa.Float(), nullable=False),
        sa.Column("formula_version", sa.String(40), nullable=False),
        sa.CheckConstraint("gross_margin BETWEEN 0 AND 1", name="gross_margin_range"),
        sa.CheckConstraint("refund_rate BETWEEN 0 AND 1", name="refund_rate_range"),
        sa.CheckConstraint("dispute_rate BETWEEN 0 AND 1", name="dispute_rate_range"),
        sa.CheckConstraint("profitability_score BETWEEN 0 AND 100", name="profitability_range"),
        org(),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes("unit_economic_assessments", "product_id")
    op.create_table(
        "cfo_insights",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("type", sa.String(40), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("finding", sa.Text(), nullable=False),
        sa.Column("impact", sa.Text(), nullable=False),
        sa.Column("recommendation", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),
        org(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cfo_insights_organization_id", "cfo_insights", ["organization_id"])
    op.create_table(
        "financial_risk_signals",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("period_id", uuid),
        sa.Column("product_id", uuid),
        sa.Column("risk_type", sa.String(40), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("evidence_reference", sa.String(500), nullable=False),
        org(),
        sa.ForeignKeyConstraint(["period_id"], ["financial_periods.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_financial_risk_signals_organization_id", "financial_risk_signals", ["organization_id"]
    )


def downgrade() -> None:
    for table in (
        "financial_risk_signals",
        "cfo_insights",
        "unit_economic_assessments",
        "contribution_profit_assessments",
        "cost_observations",
        "revenue_observations",
        "financial_periods",
    ):
        op.drop_table(table)
