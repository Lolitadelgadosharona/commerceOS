"""GrowthOS revenue machine completion.

Revision ID: 0063_revenue_machine_completion
Revises: 0062_discovery_automation
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0063_revenue_machine_completion"
down_revision: str | None = "0062_discovery_automation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def common() -> list[sa.Column]:
    return [
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
    ]


def indexes(table: str, columns: list[str]) -> None:
    for column in columns:
        op.create_index(op.f(f"ix_{table}_{column}"), table, [column])


def upgrade() -> None:
    op.create_table(
        "growth_diagnoses",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("prospect_id", sa.Uuid(), nullable=False),
        sa.Column("industry_profile_id", sa.Uuid()),
        sa.Column("business_situation", sa.Text(), nullable=False),
        sa.Column("growth_problems", sa.JSON(), nullable=False),
        sa.Column("evidence_references", sa.JSON(), nullable=False),
        sa.Column("customer_impact", sa.Text(), nullable=False),
        sa.Column("recommended_improvements", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("risks", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("ai_request_id", sa.Uuid()),
        *common(),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="growth_diag_conf"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["prospect_id"], ["growth_prospects.id"]),
        sa.ForeignKeyConstraint(["industry_profile_id"], ["industry_growth_profiles.id"]),
        sa.ForeignKeyConstraint(["ai_request_id"], ["ai_requests.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes(
        "growth_diagnoses",
        ["organization_id", "prospect_id", "industry_profile_id", "ai_request_id"],
    )
    op.create_table(
        "growth_offer_recommendations",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("prospect_id", sa.Uuid(), nullable=False),
        sa.Column("diagnosis_id", sa.Uuid(), nullable=False),
        sa.Column("offer_type", sa.String(40), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("customer_fit", sa.Text(), nullable=False),
        sa.Column("scope_summary", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("risks", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("formula_version", sa.String(80), nullable=False),
        *common(),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="growth_offer_conf"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["prospect_id"], ["growth_prospects.id"]),
        sa.ForeignKeyConstraint(["diagnosis_id"], ["growth_diagnoses.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes("growth_offer_recommendations", ["organization_id", "prospect_id", "diagnosis_id"])
    op.create_table(
        "industry_delivery_knowledge",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("industry_profile_id", sa.Uuid(), nullable=False),
        sa.Column("knowledge_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(250), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("evidence_references", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("version_label", sa.String(40), nullable=False),
        *common(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["industry_profile_id"], ["industry_growth_profiles.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes("industry_delivery_knowledge", ["organization_id", "industry_profile_id"])
    with op.batch_alter_table("growth_gifts") as batch:
        batch.add_column(sa.Column("growth_diagnosis_id", sa.Uuid()))
        batch.add_column(
            sa.Column("personalized_diagnosis", sa.Text(), nullable=False, server_default="")
        )
        batch.add_column(
            sa.Column("implementation_scope", sa.Text(), nullable=False, server_default="")
        )
        batch.add_column(
            sa.Column("customer_value_explanation", sa.Text(), nullable=False, server_default="")
        )
        batch.create_foreign_key(
            "fk_growth_gifts_diagnosis", "growth_diagnoses", ["growth_diagnosis_id"], ["id"]
        )
        batch.create_index(op.f("ix_growth_gifts_growth_diagnosis_id"), ["growth_diagnosis_id"])
    with op.batch_alter_table("growth_outreach_drafts") as batch:
        batch.add_column(sa.Column("growth_diagnosis_id", sa.Uuid()))
        batch.add_column(
            sa.Column("message_versions", sa.JSON(), nullable=False, server_default="{}")
        )
        batch.create_foreign_key(
            "fk_growth_outreach_diagnosis", "growth_diagnoses", ["growth_diagnosis_id"], ["id"]
        )
        batch.create_index(
            op.f("ix_growth_outreach_drafts_growth_diagnosis_id"), ["growth_diagnosis_id"]
        )
    with op.batch_alter_table("sales_conversation_analyses") as batch:
        batch.add_column(
            sa.Column(
                "reply_classification", sa.String(40), nullable=False, server_default="unknown"
            )
        )
        batch.add_column(
            sa.Column("response_risk", sa.String(40), nullable=False, server_default="unknown")
        )


def downgrade() -> None:
    with op.batch_alter_table("sales_conversation_analyses") as batch:
        batch.drop_column("response_risk")
        batch.drop_column("reply_classification")
    with op.batch_alter_table("growth_outreach_drafts") as batch:
        batch.drop_index(op.f("ix_growth_outreach_drafts_growth_diagnosis_id"))
        batch.drop_constraint("fk_growth_outreach_diagnosis", type_="foreignkey")
        batch.drop_column("message_versions")
        batch.drop_column("growth_diagnosis_id")
    with op.batch_alter_table("growth_gifts") as batch:
        batch.drop_index(op.f("ix_growth_gifts_growth_diagnosis_id"))
        batch.drop_constraint("fk_growth_gifts_diagnosis", type_="foreignkey")
        batch.drop_column("customer_value_explanation")
        batch.drop_column("implementation_scope")
        batch.drop_column("personalized_diagnosis")
        batch.drop_column("growth_diagnosis_id")
    for table, columns in [
        ("industry_delivery_knowledge", ["industry_profile_id", "organization_id"]),
        ("growth_offer_recommendations", ["diagnosis_id", "prospect_id", "organization_id"]),
        (
            "growth_diagnoses",
            ["ai_request_id", "industry_profile_id", "prospect_id", "organization_id"],
        ),
    ]:
        for column in columns:
            op.drop_index(op.f(f"ix_{table}_{column}"), table_name=table)
        op.drop_table(table)
