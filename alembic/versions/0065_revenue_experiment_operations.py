"""Revenue experiment operation layer.

Revision ID: 0065_revenue_experiment_operations
Revises: 0064_revenue_launch_foundation
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0065_revenue_experiment_operations"
down_revision: str | None = "0064_revenue_launch_foundation"
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
        "daily_experiment_workspace_items",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("workspace_date", sa.Date(), nullable=False),
        sa.Column("revenue_experiment_id", sa.Uuid(), nullable=False),
        sa.Column("prospect_id", sa.Uuid(), nullable=False),
        sa.Column("daily_opportunity_id", sa.Uuid()),
        sa.Column("diagnosis_id", sa.Uuid()),
        sa.Column("growth_gift_id", sa.Uuid()),
        sa.Column("offer_recommendation_id", sa.Uuid()),
        sa.Column("priority", sa.Float()),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("review_notes", sa.Text(), nullable=False),
        sa.Column("reviewed_by", sa.Uuid()),
        *common(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["revenue_experiment_id"], ["revenue_experiments.id"]),
        sa.ForeignKeyConstraint(["prospect_id"], ["growth_prospects.id"]),
        sa.ForeignKeyConstraint(["daily_opportunity_id"], ["daily_growth_opportunities.id"]),
        sa.ForeignKeyConstraint(["diagnosis_id"], ["growth_diagnoses.id"]),
        sa.ForeignKeyConstraint(["growth_gift_id"], ["growth_gifts.id"]),
        sa.ForeignKeyConstraint(["offer_recommendation_id"], ["growth_offer_recommendations.id"]),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id", "workspace_date", "revenue_experiment_id", "prospect_id"
        ),
    )
    indexes(
        "daily_experiment_workspace_items",
        [
            "organization_id",
            "workspace_date",
            "revenue_experiment_id",
            "prospect_id",
            "daily_opportunity_id",
            "diagnosis_id",
            "growth_gift_id",
            "offer_recommendation_id",
            "reviewed_by",
        ],
    )
    op.create_table(
        "email_workflow_references",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("prospect_id", sa.Uuid(), nullable=False),
        sa.Column("outreach_draft_id", sa.Uuid()),
        sa.Column("email_account_reference", sa.String(500), nullable=False),
        sa.Column("draft_reference", sa.String(500)),
        sa.Column("thread_reference", sa.String(500)),
        sa.Column("inbound_reply_reference", sa.String(500)),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("recorded_by", sa.Uuid(), nullable=False),
        *common(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["prospect_id"], ["growth_prospects.id"]),
        sa.ForeignKeyConstraint(["outreach_draft_id"], ["growth_outreach_drafts.id"]),
        sa.ForeignKeyConstraint(["recorded_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes(
        "email_workflow_references",
        ["organization_id", "prospect_id", "outreach_draft_id", "recorded_by"],
    )
    op.create_table(
        "growth_customer_feedback",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("revenue_experiment_id", sa.Uuid(), nullable=False),
        sa.Column("prospect_id", sa.Uuid(), nullable=False),
        sa.Column("conversation_analysis_id", sa.Uuid()),
        sa.Column("customer_response", sa.Text(), nullable=False),
        sa.Column("interest_level", sa.String(30), nullable=False),
        sa.Column("objection_category", sa.String(80)),
        sa.Column("reason_lost", sa.Text()),
        sa.Column("reason_won", sa.Text()),
        sa.Column("learning_signal", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("learning_observation_id", sa.Uuid()),
        sa.Column("reviewed_by", sa.Uuid()),
        *common(),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="growth_feedback_conf"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["revenue_experiment_id"], ["revenue_experiments.id"]),
        sa.ForeignKeyConstraint(["prospect_id"], ["growth_prospects.id"]),
        sa.ForeignKeyConstraint(["conversation_analysis_id"], ["sales_conversation_analyses.id"]),
        sa.ForeignKeyConstraint(["learning_observation_id"], ["learning_observations.id"]),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes(
        "growth_customer_feedback",
        [
            "organization_id",
            "revenue_experiment_id",
            "prospect_id",
            "conversation_analysis_id",
            "reviewed_by",
        ],
    )
    op.create_index(
        op.f("ix_growth_customer_feedback_learning_observation_id"),
        "growth_customer_feedback",
        ["learning_observation_id"],
        unique=True,
    )


def downgrade() -> None:
    for table, columns in [
        (
            "growth_customer_feedback",
            [
                "reviewed_by",
                "learning_observation_id",
                "conversation_analysis_id",
                "prospect_id",
                "revenue_experiment_id",
                "organization_id",
            ],
        ),
        (
            "email_workflow_references",
            ["recorded_by", "outreach_draft_id", "prospect_id", "organization_id"],
        ),
        (
            "daily_experiment_workspace_items",
            [
                "reviewed_by",
                "offer_recommendation_id",
                "growth_gift_id",
                "diagnosis_id",
                "daily_opportunity_id",
                "prospect_id",
                "revenue_experiment_id",
                "workspace_date",
                "organization_id",
            ],
        ),
    ]:
        for column in columns:
            op.drop_index(op.f(f"ix_{table}_{column}"), table_name=table)
        op.drop_table(table)
