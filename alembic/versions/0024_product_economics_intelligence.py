"""Product economics and margin intelligence foundation."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0024_product_economics"
down_revision: str | None = "0023_product_risk"
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
        sa.Column("product_candidate_id", uuid, nullable=False),
    ]


def constraints() -> list[sa.Constraint]:
    return [
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["product_candidate_id"], ["product_candidates.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    ]


def indexes(table: str) -> None:
    op.create_index(f"ix_{table}_organization_id", table, ["organization_id"])
    op.create_index(f"ix_{table}_product_candidate_id", table, ["product_candidate_id"])


def upgrade() -> None:
    money = sa.Numeric(19, 4)
    rate = sa.Numeric(7, 6)
    score = sa.Numeric(7, 4)
    op.create_table(
        "product_economic_profiles",
        *common(),
        sa.Column("product_cost", money, nullable=False),
        sa.Column("shipping_cost", money, nullable=False),
        sa.Column("packaging_cost", money, nullable=False),
        sa.Column("transaction_cost", money, nullable=False),
        sa.Column("estimated_acquisition_cost", money, nullable=False),
        sa.Column("refund_rate_assumption", rate, nullable=False),
        sa.Column("dispute_rate_assumption", rate, nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("confidence", rate, nullable=False),
        sa.CheckConstraint("product_cost >= 0", name="product_cost_nonnegative"),
        sa.CheckConstraint("shipping_cost >= 0", name="shipping_cost_nonnegative"),
        sa.CheckConstraint("packaging_cost >= 0", name="packaging_cost_nonnegative"),
        sa.CheckConstraint("transaction_cost >= 0", name="transaction_cost_nonnegative"),
        sa.CheckConstraint("estimated_acquisition_cost >= 0", name="acquisition_nonnegative"),
        sa.CheckConstraint("refund_rate_assumption BETWEEN 0 AND 1", name="refund_rate_range"),
        sa.CheckConstraint("dispute_rate_assumption BETWEEN 0 AND 1", name="dispute_rate_range"),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),
        *constraints(),
    )
    indexes("product_economic_profiles")
    op.create_table(
        "product_profit_assessments",
        *common(),
        sa.Column("selling_price", money, nullable=False),
        sa.Column("gross_margin", money, nullable=False),
        sa.Column("contribution_profit", money, nullable=False),
        sa.Column("margin_score", score, nullable=False),
        sa.Column("confidence", rate, nullable=False),
        sa.Column("formula_version", sa.String(40), nullable=False),
        sa.CheckConstraint("selling_price > 0", name="selling_price_positive"),
        sa.CheckConstraint("margin_score BETWEEN 0 AND 100", name="margin_score_range"),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),
        *constraints(),
    )
    indexes("product_profit_assessments")
    op.create_table(
        "profit_scenario_assessments",
        *common(),
        sa.Column("scenario", sa.String(20), nullable=False),
        sa.Column("revenue", money, nullable=False),
        sa.Column("cost", money, nullable=False),
        sa.Column("profit", money, nullable=False),
        sa.Column("margin", sa.Numeric(9, 4), nullable=False),
        *constraints(),
    )
    indexes("profit_scenario_assessments")
    op.create_table(
        "risk_adjusted_profit_assessments",
        *common(),
        sa.Column("opportunity_score", score, nullable=False),
        sa.Column("risk_score", score, nullable=False),
        sa.Column("profit_score", score, nullable=False),
        sa.Column("final_score", score, nullable=False),
        sa.Column("recommendation", sa.String(20), nullable=False),
        sa.CheckConstraint("opportunity_score BETWEEN 0 AND 100", name="opportunity_range"),
        sa.CheckConstraint("risk_score BETWEEN 0 AND 100", name="risk_range"),
        sa.CheckConstraint("profit_score BETWEEN 0 AND 100", name="profit_range"),
        sa.CheckConstraint("final_score BETWEEN 0 AND 100", name="final_range"),
        *constraints(),
    )
    indexes("risk_adjusted_profit_assessments")


def downgrade() -> None:
    for table in (
        "risk_adjusted_profit_assessments",
        "profit_scenario_assessments",
        "product_profit_assessments",
        "product_economic_profiles",
    ):
        op.drop_table(table)
