"""Revenue conversation intelligence foundation."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0041_revenue_conversation"
down_revision: str | None = "0040_growth_experiments"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def common() -> list[sa.Column]:
    return [
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
    ]


def upgrade() -> None:
    with op.batch_alter_table("customer_journey_events") as batch:
        batch.add_column(sa.Column("confidence", sa.Float(), nullable=False, server_default="1"))
        batch.create_check_constraint("confidence_range", "confidence BETWEEN 0 AND 1")
        batch.alter_column("confidence", server_default=None)

    with op.batch_alter_table("customer_value_assessments") as batch:
        batch.add_column(
            sa.Column("contribution_potential", sa.Float(), nullable=False, server_default="0")
        )
        batch.add_column(
            sa.Column("risk_indicators", sa.JSON(), nullable=False, server_default="[]")
        )
        batch.add_column(sa.Column("confidence", sa.Float(), nullable=False, server_default="1"))
        batch.create_check_constraint(
            "contribution_range", "contribution_potential BETWEEN 0 AND 100"
        )
        batch.create_check_constraint("confidence_range", "confidence BETWEEN 0 AND 1")
        batch.alter_column("contribution_potential", server_default=None)
        batch.alter_column("risk_indicators", server_default=None)
        batch.alter_column("confidence", server_default=None)

    op.create_table(
        "customer_intent_journeys",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("evidence_references", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        *common(),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "customer_id"),
    )
    op.create_table(
        "sales_intent_signals",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("evidence_references", sa.JSON(), nullable=False),
        sa.Column("intent_type", sa.String(40), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("recommendation", sa.Text(), nullable=False),
        *common(),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "support_learning_signals",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("source_issue_id", sa.Uuid(), nullable=False),
        sa.Column("customer_impact", sa.Text(), nullable=False),
        sa.Column("root_cause_category", sa.String(60), nullable=False),
        sa.Column("recommendation", sa.Text(), nullable=False),
        *common(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["source_issue_id"], ["support_case_intelligence.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for table, columns in {
        "customer_intent_journeys": ["organization_id", "customer_id"],
        "sales_intent_signals": ["organization_id", "customer_id"],
        "support_learning_signals": ["organization_id", "source_issue_id"],
    }.items():
        for column in columns:
            op.create_index(op.f(f"ix_{table}_{column}"), table, [column])


def downgrade() -> None:
    op.drop_table("support_learning_signals")
    op.drop_table("sales_intent_signals")
    op.drop_table("customer_intent_journeys")
    with op.batch_alter_table("customer_value_assessments") as batch:
        batch.drop_constraint("confidence_range", type_="check")
        batch.drop_constraint("contribution_range", type_="check")
        batch.drop_column("confidence")
        batch.drop_column("risk_indicators")
        batch.drop_column("contribution_potential")
    with op.batch_alter_table("customer_journey_events") as batch:
        batch.drop_constraint("confidence_range", type_="check")
        batch.drop_column("confidence")
