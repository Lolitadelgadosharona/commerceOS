"""AI sales and support decision foundation.

Revision ID: 0012_ai_sales_support
Revises: 0011_conversation_commerce
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0012_ai_sales_support"
down_revision: str | None = "0011_conversation_commerce"
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
        "sales_intelligence_profiles",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("customer_id", uuid, nullable=False),
        sa.Column("conversation_id", uuid, nullable=False),
        sa.Column("product_id", uuid),
        sa.Column("intent", sa.String(40), nullable=False),
        sa.Column("estimated_value", sa.Numeric(14, 2)),
        sa.Column("repeat_probability", sa.Float()),
        sa.Column("risk_level", sa.String(20)),
        sa.CheckConstraint(
            "repeat_probability IS NULL OR repeat_probability BETWEEN 0 AND 1",
            name="repeat_probability_range",
        ),
        org(),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversation_threads.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes("sales_intelligence_profiles", "customer_id")
    op.create_index(
        "ix_sales_intelligence_profiles_conversation_id",
        "sales_intelligence_profiles",
        ["conversation_id"],
    )
    op.create_table(
        "sales_recommendations",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("sales_profile_id", uuid, nullable=False),
        sa.Column("recommendation_type", sa.String(40), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),
        org(),
        sa.ForeignKeyConstraint(
            ["sales_profile_id"], ["sales_intelligence_profiles.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes("sales_recommendations", "sales_profile_id")
    op.create_table(
        "support_case_intelligence",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("conversation_id", uuid, nullable=False),
        sa.Column("issue_category", sa.String(30), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("customer_impact", sa.Text(), nullable=False),
        sa.Column("risk_level", sa.String(20), nullable=False),
        sa.Column("recommended_resolution", sa.Text(), nullable=False),
        org(),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversation_threads.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes("support_case_intelligence", "conversation_id")
    op.create_table(
        "customer_risk_signals",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("customer_id", uuid, nullable=False),
        sa.Column("risk_type", sa.String(30), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("evidence_reference", sa.String(500), nullable=False),
        org(),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes("customer_risk_signals", "customer_id")
    op.create_table(
        "ai_action_policies",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("action_type", sa.String(50), nullable=False),
        sa.Column("allowed", sa.Boolean(), nullable=False),
        sa.Column("requires_approval", sa.Boolean(), nullable=False),
        sa.Column("domain", sa.String(30), nullable=False),
        org(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "action_type"),
    )
    op.create_index(
        "ix_ai_action_policies_organization_id", "ai_action_policies", ["organization_id"]
    )


def downgrade() -> None:
    for table in (
        "ai_action_policies",
        "customer_risk_signals",
        "support_case_intelligence",
        "sales_recommendations",
        "sales_intelligence_profiles",
    ):
        op.drop_table(table)
