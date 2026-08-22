"""GrowthOS revenue engine foundation v2.

Revision ID: 0057_growthos_revenue_v2
Revises: 0056_product_evaluation
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0057_growthos_revenue_v2"
down_revision: str | None = "0056_product_evaluation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def common() -> list[sa.Column]:
    return [
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
    ]


def index(table: str, column: str) -> None:
    op.create_index(op.f(f"ix_{table}_{column}"), table, [column])


def upgrade() -> None:
    with op.batch_alter_table("growth_opportunity_analyses") as batch:
        batch.add_column(sa.Column("purchase_probability", sa.Float()))
        batch.create_check_constraint(
            op.f("ck_growth_opportunity_analyses_purchase_probability_range"),
            "purchase_probability IS NULL OR purchase_probability BETWEEN 0 AND 1",
        )
    with op.batch_alter_table("growth_gifts") as batch:
        batch.add_column(sa.Column("observed_issue", sa.Text(), nullable=False, server_default=""))
        batch.add_column(
            sa.Column("recommended_improvement", sa.Text(), nullable=False, server_default="")
        )
        batch.add_column(sa.Column("expected_value", sa.Text(), nullable=False, server_default=""))
        batch.add_column(
            sa.Column("preview_type", sa.String(40), nullable=False, server_default="other")
        )
        batch.add_column(
            sa.Column("preview_status", sa.String(30), nullable=False, server_default="draft")
        )
    with op.batch_alter_table("growth_gifts") as batch:
        for column in [
            "observed_issue",
            "recommended_improvement",
            "expected_value",
            "preview_type",
            "preview_status",
        ]:
            batch.alter_column(column, server_default=None)

    op.create_table(
        "business_growth_profiles",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("prospect_id", sa.Uuid(), nullable=False),
        sa.Column("business_identity", sa.JSON(), nullable=False),
        sa.Column("industry", sa.String(120), nullable=False),
        sa.Column("location", sa.String(250)),
        sa.Column("evidence_references", sa.JSON(), nullable=False),
        sa.Column("digital_presence", sa.JSON(), nullable=False),
        sa.Column("customer_signals", sa.JSON(), nullable=False),
        sa.Column("strengths", sa.JSON(), nullable=False),
        sa.Column("weaknesses", sa.JSON(), nullable=False),
        sa.Column("growth_opportunities", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        *common(),
        sa.CheckConstraint(
            "confidence BETWEEN 0 AND 1",
            name=op.f("ck_business_growth_profiles_confidence_range"),
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["prospect_id"], ["growth_prospects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("prospect_id"),
    )
    index("business_growth_profiles", "organization_id")
    index("business_growth_profiles", "prospect_id")

    op.create_table(
        "growth_prospect_rankings",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("prospect_id", sa.Uuid(), nullable=False),
        sa.Column("pain_severity", sa.Float()),
        sa.Column("business_impact", sa.Float()),
        sa.Column("accessibility", sa.Float()),
        sa.Column("buying_signals", sa.Float()),
        sa.Column("solution_fit", sa.Float()),
        sa.Column("score", sa.Float()),
        sa.Column("missing_inputs", sa.JSON(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("formula_version", sa.String(80), nullable=False),
        *common(),
        sa.CheckConstraint(
            "score IS NULL OR score BETWEEN 0 AND 100",
            name=op.f("ck_growth_prospect_rankings_score_range"),
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["prospect_id"], ["growth_prospects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("prospect_id"),
    )
    index("growth_prospect_rankings", "organization_id")
    index("growth_prospect_rankings", "prospect_id")


def downgrade() -> None:
    for table, columns in [
        ("growth_prospect_rankings", ["prospect_id", "organization_id"]),
        ("business_growth_profiles", ["prospect_id", "organization_id"]),
    ]:
        for column in columns:
            op.drop_index(op.f(f"ix_{table}_{column}"), table_name=table)
        op.drop_table(table)
    with op.batch_alter_table("growth_gifts") as batch:
        for column in [
            "preview_status",
            "preview_type",
            "expected_value",
            "recommended_improvement",
            "observed_issue",
        ]:
            batch.drop_column(column)
    with op.batch_alter_table("growth_opportunity_analyses") as batch:
        batch.drop_constraint(
            op.f("ck_growth_opportunity_analyses_purchase_probability_range"),
            type_="check",
        )
        batch.drop_column("purchase_probability")
