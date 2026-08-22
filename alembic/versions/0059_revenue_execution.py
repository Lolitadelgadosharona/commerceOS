"""Revenue experiment execution layer.

Revision ID: 0059_revenue_execution
Revises: 0058_industry_intelligence
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0059_revenue_execution"
down_revision: str | None = "0058_industry_intelligence"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("growth_gifts") as batch:
        batch.add_column(
            sa.Column("gift_type", sa.String(50), nullable=False, server_default="other")
        )
        batch.add_column(sa.Column("before_asset_reference", sa.String(500)))
        batch.add_column(sa.Column("after_asset_reference", sa.String(500)))
        batch.add_column(
            sa.Column("customer_rationale", sa.Text(), nullable=False, server_default="")
        )
        batch.add_column(sa.Column("customer_response", sa.Text()))
    with op.batch_alter_table("growth_gifts") as batch:
        batch.alter_column("gift_type", server_default=None)
        batch.alter_column("customer_rationale", server_default=None)

    for table in ["growth_outreach_drafts", "sales_conversation_analyses"]:
        with op.batch_alter_table(table) as batch:
            batch.add_column(sa.Column("industry_profile_id", sa.Uuid()))
            batch.add_column(
                sa.Column("industry_context", sa.Text(), nullable=False, server_default="")
            )
            batch.create_foreign_key(
                op.f(f"fk_{table}_industry_profile_id_industry_growth_profiles"),
                "industry_growth_profiles",
                ["industry_profile_id"],
                ["id"],
            )
            batch.create_index(op.f(f"ix_{table}_industry_profile_id"), ["industry_profile_id"])
        with op.batch_alter_table(table) as batch:
            batch.alter_column("industry_context", server_default=None)

    with op.batch_alter_table("ai_model_policies") as batch:
        batch.add_column(
            sa.Column("provider_name", sa.String(120), nullable=False, server_default="unassigned")
        )
        batch.add_column(
            sa.Column("cost_policy", sa.String(40), nullable=False, server_default="balanced")
        )
        batch.add_column(sa.Column("cost_limit", sa.Float()))
    with op.batch_alter_table("ai_model_policies") as batch:
        batch.alter_column("provider_name", server_default=None)
        batch.alter_column("cost_policy", server_default=None)

    op.create_table(
        "daily_growth_opportunities",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("queue_date", sa.Date(), nullable=False),
        sa.Column("industry_profile_id", sa.Uuid(), nullable=False),
        sa.Column("prospect_id", sa.Uuid(), nullable=False),
        sa.Column("evidence_references", sa.JSON(), nullable=False),
        sa.Column("growth_pain", sa.Text(), nullable=False),
        sa.Column("industry_pattern_id", sa.Uuid(), nullable=False),
        sa.Column("opportunity_score", sa.Float()),
        sa.Column("service_recommendation_id", sa.Uuid(), nullable=False),
        sa.Column("growth_gift_id", sa.Uuid()),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "opportunity_score IS NULL OR opportunity_score BETWEEN 0 AND 100",
            name=op.f("ck_daily_growth_opportunities_score_range"),
        ),
        sa.CheckConstraint(
            "confidence BETWEEN 0 AND 1",
            name=op.f("ck_daily_growth_opportunities_confidence_range"),
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["industry_profile_id"], ["industry_growth_profiles.id"]),
        sa.ForeignKeyConstraint(["prospect_id"], ["growth_prospects.id"]),
        sa.ForeignKeyConstraint(["industry_pattern_id"], ["industry_growth_patterns.id"]),
        sa.ForeignKeyConstraint(
            ["service_recommendation_id"], ["growth_service_recommendations.id"]
        ),
        sa.ForeignKeyConstraint(["growth_gift_id"], ["growth_gifts.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "queue_date", "prospect_id"),
    )
    for column in [
        "organization_id",
        "queue_date",
        "industry_profile_id",
        "prospect_id",
        "industry_pattern_id",
        "service_recommendation_id",
        "growth_gift_id",
    ]:
        op.create_index(
            op.f(f"ix_daily_growth_opportunities_{column}"), "daily_growth_opportunities", [column]
        )


def downgrade() -> None:
    for column in [
        "growth_gift_id",
        "service_recommendation_id",
        "industry_pattern_id",
        "prospect_id",
        "industry_profile_id",
        "queue_date",
        "organization_id",
    ]:
        op.drop_index(
            op.f(f"ix_daily_growth_opportunities_{column}"), table_name="daily_growth_opportunities"
        )
    op.drop_table("daily_growth_opportunities")
    with op.batch_alter_table("ai_model_policies") as batch:
        batch.drop_column("cost_limit")
        batch.drop_column("cost_policy")
        batch.drop_column("provider_name")
    for table in ["sales_conversation_analyses", "growth_outreach_drafts"]:
        with op.batch_alter_table(table) as batch:
            batch.drop_index(op.f(f"ix_{table}_industry_profile_id"))
            batch.drop_constraint(
                op.f(f"fk_{table}_industry_profile_id_industry_growth_profiles"), type_="foreignkey"
            )
            batch.drop_column("industry_context")
            batch.drop_column("industry_profile_id")
    with op.batch_alter_table("growth_gifts") as batch:
        batch.drop_column("customer_response")
        batch.drop_column("customer_rationale")
        batch.drop_column("after_asset_reference")
        batch.drop_column("before_asset_reference")
        batch.drop_column("gift_type")
