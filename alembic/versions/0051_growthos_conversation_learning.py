"""GrowthOS customer conversation intelligence and learning loop.

Revision ID: 0051_growthos_conversation
Revises: 0050_growthos_activation
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0051_growthos_conversation"
down_revision: str | None = "0050_growthos_activation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def common() -> list[sa.Column]:
    return [
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
    ]


def indexed(table: str, columns: list[str]) -> None:
    for column in columns:
        op.create_index(op.f(f"ix_{table}_{column}"), table, [column])


def upgrade() -> None:
    with op.batch_alter_table("sales_conversation_analyses") as batch:
        batch.add_column(
            sa.Column("urgency", sa.String(40), nullable=False, server_default=sa.text("'unknown'"))
        )
        batch.add_column(
            sa.Column("status", sa.String(30), nullable=False, server_default=sa.text("'draft'"))
        )
    op.create_table(
        "growth_objection_records",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("analysis_id", sa.Uuid(), nullable=False),
        sa.Column("prospect_id", sa.Uuid(), nullable=False),
        sa.Column("objection_type", sa.String(40), nullable=False),
        sa.Column("customer_segment", sa.String(250), nullable=False),
        sa.Column("original_message", sa.Text(), nullable=False),
        sa.Column("suggested_response", sa.Text(), nullable=False),
        sa.Column("outcome", sa.String(40), nullable=False),
        *common(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["analysis_id"], ["sales_conversation_analyses.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["prospect_id"], ["growth_prospects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    indexed("growth_objection_records", ["organization_id", "analysis_id", "prospect_id"])
    op.create_table(
        "growth_sales_learning_signals",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("analysis_id", sa.Uuid(), nullable=False),
        sa.Column("objection_record_id", sa.Uuid()),
        sa.Column("learning_observation_id", sa.Uuid(), nullable=False),
        sa.Column("signal_type", sa.String(80), nullable=False),
        sa.Column("insight", sa.Text(), nullable=False),
        sa.Column("future_recommendation", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        *common(),
        sa.CheckConstraint(
            "confidence BETWEEN 0 AND 1",
            name=op.f("ck_growth_sales_learning_signals_growth_sales_learning_confidence_range"),
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["analysis_id"], ["sales_conversation_analyses.id"]),
        sa.ForeignKeyConstraint(["objection_record_id"], ["growth_objection_records.id"]),
        sa.ForeignKeyConstraint(["learning_observation_id"], ["learning_observations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    indexed(
        "growth_sales_learning_signals",
        ["organization_id", "analysis_id", "objection_record_id"],
    )
    op.create_index(
        op.f("ix_growth_sales_learning_signals_learning_observation_id"),
        "growth_sales_learning_signals",
        ["learning_observation_id"],
        unique=True,
    )
    op.create_table(
        "growth_message_performance_observations",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("outreach_draft_id", sa.Uuid(), nullable=False),
        sa.Column("prospect_experiment_link_id", sa.Uuid()),
        sa.Column("customer_segment", sa.String(250), nullable=False),
        sa.Column("message_strategy", sa.Text(), nullable=False),
        sa.Column("outcome", sa.String(40), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        *common(),
        sa.CheckConstraint(
            "confidence BETWEEN 0 AND 1",
            name=op.f(
                "ck_growth_message_performance_observations_"
                "growth_message_performance_confidence_range"
            ),
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["outreach_draft_id"], ["growth_outreach_drafts.id"]),
        sa.ForeignKeyConstraint(["prospect_experiment_link_id"], ["prospect_experiment_links.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    indexed(
        "growth_message_performance_observations",
        ["organization_id", "outreach_draft_id", "prospect_experiment_link_id"],
    )
    if op.get_context().dialect.name == "postgresql":
        op.execute(
            """
            CREATE FUNCTION prevent_growth_message_performance_mutation() RETURNS trigger AS $$
            BEGIN RAISE EXCEPTION 'Message performance observations are append-only'; END;
            $$ LANGUAGE plpgsql;
            CREATE TRIGGER growth_message_performance_append_only
            BEFORE UPDATE OR DELETE ON growth_message_performance_observations
            FOR EACH ROW EXECUTE FUNCTION prevent_growth_message_performance_mutation();
            """
        )


def downgrade() -> None:
    if op.get_context().dialect.name == "postgresql":
        op.execute(
            "DROP TRIGGER IF EXISTS growth_message_performance_append_only "
            "ON growth_message_performance_observations"
        )
        op.execute("DROP FUNCTION IF EXISTS prevent_growth_message_performance_mutation()")
    for table, columns in [
        (
            "growth_message_performance_observations",
            ["prospect_experiment_link_id", "outreach_draft_id", "organization_id"],
        ),
        (
            "growth_sales_learning_signals",
            ["objection_record_id", "analysis_id", "organization_id"],
        ),
        ("growth_objection_records", ["prospect_id", "analysis_id", "organization_id"]),
    ]:
        if table == "growth_sales_learning_signals":
            op.drop_index(
                op.f("ix_growth_sales_learning_signals_learning_observation_id"),
                table_name=table,
            )
        for column in columns:
            op.drop_index(op.f(f"ix_{table}_{column}"), table_name=table)
        op.drop_table(table)
    with op.batch_alter_table("sales_conversation_analyses") as batch:
        batch.drop_column("status")
        batch.drop_column("urgency")
