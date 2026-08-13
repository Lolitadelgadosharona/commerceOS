"""Strategic account intelligence foundation."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0032_strategic_accounts"
down_revision: str | None = "0031_customer_360"
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
    ]


def base() -> list[sa.Constraint]:
    return [
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    ]


def idx(table: str, *columns: str) -> None:
    for column in columns:
        op.create_index(f"ix_{table}_{column}", table, [column])


def upgrade() -> None:
    op.create_table(
        "strategic_account_profiles",
        *common(),
        sa.Column("customer_id", uuid, nullable=False),
        sa.Column("project_id", uuid),
        sa.Column("account_status", sa.String(30), nullable=False),
        sa.Column("relationship_stage", sa.String(50), nullable=False),
        sa.Column("strategic_tier", sa.String(30), nullable=False),
        sa.Column("relationship_strength", sa.Float(), nullable=False),
        sa.Column("commercial_potential", sa.Float(), nullable=False),
        sa.Column("expansion_potential", sa.Float(), nullable=False),
        sa.Column("replenishment_potential", sa.Float(), nullable=False),
        sa.Column("risk_level", sa.String(30), nullable=False),
        sa.Column("last_meaningful_activity_at", sa.DateTime(timezone=True)),
        sa.Column("next_review_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("relationship_strength BETWEEN 0 AND 100", name="relationship_range"),
        sa.CheckConstraint("commercial_potential BETWEEN 0 AND 100", name="commercial_range"),
        sa.CheckConstraint("expansion_potential BETWEEN 0 AND 100", name="expansion_range"),
        sa.CheckConstraint("replenishment_potential BETWEEN 0 AND 100", name="replenishment_range"),
        sa.CheckConstraint(
            "account_status IN ('candidate','active','watch','dormant','closed')",
            name="status_values",
        ),
        sa.CheckConstraint(
            "strategic_tier IN ('standard','growth','strategic','key')", name="tier_values"
        ),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.UniqueConstraint("organization_id", "customer_id"),
        *base(),
    )
    idx("strategic_account_profiles", "organization_id", "customer_id")
    op.create_table(
        "account_stakeholders",
        *common(),
        sa.Column("strategic_account_id", uuid, nullable=False),
        sa.Column("contact_reference", sa.String(500), nullable=False),
        sa.Column("role", sa.String(100), nullable=False),
        sa.Column("decision_influence", sa.Float(), nullable=False),
        sa.Column("decision_maker", sa.Boolean(), nullable=False),
        sa.Column("relationship_strength", sa.Float(), nullable=False),
        sa.Column("evidence_reference", sa.Text()),
        sa.CheckConstraint("decision_influence BETWEEN 0 AND 100", name="influence_range"),
        sa.CheckConstraint("relationship_strength BETWEEN 0 AND 100", name="relationship_range"),
        sa.ForeignKeyConstraint(
            ["strategic_account_id"], ["strategic_account_profiles.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint("organization_id", "strategic_account_id", "contact_reference"),
        *base(),
    )
    idx("account_stakeholders", "organization_id", "strategic_account_id")
    op.create_table(
        "replenishment_assessments",
        *common(),
        sa.Column("strategic_account_id", uuid, nullable=False),
        sa.Column("product_reference", sa.String(500)),
        sa.Column("historical_purchase_references", sa.JSON(), nullable=False),
        sa.Column("purchase_frequency_indicator", sa.Float()),
        sa.Column("last_purchase_date", sa.Date()),
        sa.Column("expected_replenishment_cycle_days", sa.Integer()),
        sa.Column("behavior_indicators", sa.JSON(), nullable=False),
        sa.Column("conversation_evidence", sa.JSON(), nullable=False),
        sa.Column("estimated_next_purchase_start", sa.Date()),
        sa.Column("estimated_next_purchase_end", sa.Date()),
        sa.Column("replenishment_probability", sa.Float()),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("evidence_summary", sa.Text()),
        sa.Column("assessment_version", sa.String(50), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.CheckConstraint("replenishment_probability BETWEEN 0 AND 1", name="probability_range"),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),
        sa.CheckConstraint(
            "status IN ('draft','review','current','expired')", name="status_values"
        ),
        sa.ForeignKeyConstraint(
            ["strategic_account_id"], ["strategic_account_profiles.id"], ondelete="CASCADE"
        ),
        *base(),
    )
    idx("replenishment_assessments", "organization_id", "strategic_account_id")
    op.create_table(
        "customer_expansion_opportunities",
        *common(),
        sa.Column("strategic_account_id", uuid, nullable=False),
        sa.Column("opportunity_type", sa.String(40), nullable=False),
        sa.Column("product_reference", sa.String(500)),
        sa.Column("estimated_value_indicator", sa.Float()),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("risk_indicator", sa.Float(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),
        sa.CheckConstraint("risk_indicator BETWEEN 0 AND 100", name="risk_range"),
        sa.CheckConstraint(
            "status IN ('identified','review','ready','dismissed','expired')", name="status_values"
        ),
        sa.ForeignKeyConstraint(
            ["strategic_account_id"], ["strategic_account_profiles.id"], ondelete="CASCADE"
        ),
        *base(),
    )
    idx("customer_expansion_opportunities", "organization_id", "strategic_account_id")
    op.create_table(
        "customer_next_best_actions",
        *common(),
        sa.Column("customer_id", uuid, nullable=False),
        sa.Column("strategic_account_id", uuid),
        sa.Column("recommendation_type", sa.String(40), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("evidence_references", sa.JSON(), nullable=False),
        sa.Column("priority", sa.String(20), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("recommended_time_window", sa.Date()),
        sa.Column("human_review_required", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("formula_or_rule_version", sa.String(50), nullable=False),
        sa.Column("decision_queue_item_id", uuid),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),
        sa.CheckConstraint(
            "priority IN ('low','normal','high','critical')", name="priority_values"
        ),
        sa.CheckConstraint(
            "status IN ('draft','reviewed','accepted','rejected')", name="status_values"
        ),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["strategic_account_id"], ["strategic_account_profiles.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["decision_queue_item_id"], ["decision_queue_items.id"]),
        *base(),
    )
    idx("customer_next_best_actions", "organization_id", "customer_id")
    op.create_table(
        "strategic_account_scores",
        *common(),
        sa.Column("strategic_account_id", uuid, nullable=False),
        sa.Column("input_values", sa.JSON(), nullable=False),
        sa.Column("weights", sa.JSON(), nullable=False),
        sa.Column("formula_version", sa.String(50), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("evidence_coverage", sa.Float(), nullable=False),
        sa.CheckConstraint("score BETWEEN 0 AND 100", name="score_range"),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),
        sa.ForeignKeyConstraint(
            ["strategic_account_id"], ["strategic_account_profiles.id"], ondelete="CASCADE"
        ),
        *base(),
    )
    idx("strategic_account_scores", "organization_id", "strategic_account_id")


def downgrade() -> None:
    for table in (
        "strategic_account_scores",
        "customer_next_best_actions",
        "customer_expansion_opportunities",
        "replenishment_assessments",
        "account_stakeholders",
        "strategic_account_profiles",
    ):
        op.drop_table(table)
