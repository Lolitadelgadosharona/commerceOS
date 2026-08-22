"""GrowthOS revenue activation layer.

Revision ID: 0050_growthos_activation
Revises: 0049_growthos_discovery
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0050_growthos_activation"
down_revision: str | None = "0049_growthos_discovery"
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
    with op.batch_alter_table("growth_prospects") as batch:
        batch.add_column(sa.Column("source_candidate_id", sa.Uuid()))
        batch.create_foreign_key(
            "fk_growth_prospects_source_candidate_id_prospect_candidates",
            "prospect_candidates",
            ["source_candidate_id"],
            ["id"],
        )
        batch.create_index(
            op.f("ix_growth_prospects_source_candidate_id"),
            ["source_candidate_id"],
            unique=True,
        )
    with op.batch_alter_table("growth_gifts") as batch:
        batch.add_column(
            sa.Column(
                "evidence_reference",
                sa.JSON(),
                nullable=False,
                server_default=sa.text("'[]'"),
            )
        )
    op.execute("UPDATE growth_gifts SET status = 'delivered' WHERE status = 'sent'")
    with op.batch_alter_table("growth_outreach_drafts") as batch:
        batch.add_column(
            sa.Column("subject_options", sa.JSON(), nullable=False, server_default=sa.text("'[]'"))
        )
        for name in [
            "opening_sentence",
            "personalized_context",
            "problem_observation",
            "gift_explanation",
            "soft_cta",
        ]:
            batch.add_column(
                sa.Column(name, sa.Text(), nullable=False, server_default=sa.text("''"))
            )
    with op.batch_alter_table("sales_conversation_analyses") as batch:
        batch.add_column(
            sa.Column("customer_reply", sa.Text(), nullable=False, server_default=sa.text("''"))
        )
        batch.add_column(
            sa.Column(
                "buying_signal",
                sa.String(80),
                nullable=False,
                server_default=sa.text("'unknown'"),
            )
        )
        batch.add_column(sa.Column("objection_type", sa.String(80)))
    op.create_table(
        "revenue_experiments",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(250), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("target_segment", sa.Text(), nullable=False),
        sa.Column("offer_type", sa.String(120), nullable=False),
        sa.Column("message_strategy", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        *common(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "name"),
    )
    indexed("revenue_experiments", ["organization_id", "created_by"])
    op.create_table(
        "prospect_experiment_links",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("experiment_id", sa.Uuid(), nullable=False),
        sa.Column("prospect_id", sa.Uuid(), nullable=False),
        sa.Column("assigned_offer", sa.Text(), nullable=False),
        sa.Column("assigned_message", sa.Text(), nullable=False),
        sa.Column("result_status", sa.String(20), nullable=False),
        *common(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["experiment_id"], ["revenue_experiments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["prospect_id"], ["growth_prospects.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("experiment_id", "prospect_id"),
    )
    indexed("prospect_experiment_links", ["organization_id", "experiment_id", "prospect_id"])
    op.create_table(
        "outreach_tracking_events",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("prospect_experiment_link_id", sa.Uuid(), nullable=False),
        sa.Column("outreach_draft_id", sa.Uuid()),
        sa.Column("event_type", sa.String(30), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("recorded_by", sa.Uuid(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        *common(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["prospect_experiment_link_id"],
            ["prospect_experiment_links.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["outreach_draft_id"], ["growth_outreach_drafts.id"]),
        sa.ForeignKeyConstraint(["recorded_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    indexed(
        "outreach_tracking_events",
        ["organization_id", "prospect_experiment_link_id", "outreach_draft_id", "recorded_by"],
    )
    if op.get_context().dialect.name == "postgresql":
        op.execute(
            """
            CREATE FUNCTION prevent_outreach_tracking_event_mutation() RETURNS trigger AS $$
            BEGIN RAISE EXCEPTION 'Outreach tracking events are append-only'; END;
            $$ LANGUAGE plpgsql;
            CREATE TRIGGER outreach_tracking_events_append_only
            BEFORE UPDATE OR DELETE ON outreach_tracking_events
            FOR EACH ROW EXECUTE FUNCTION prevent_outreach_tracking_event_mutation();
            """
        )


def downgrade() -> None:
    if op.get_context().dialect.name == "postgresql":
        op.execute(
            "DROP TRIGGER IF EXISTS outreach_tracking_events_append_only "
            "ON outreach_tracking_events"
        )
        op.execute("DROP FUNCTION IF EXISTS prevent_outreach_tracking_event_mutation()")
    for table, columns in [
        (
            "outreach_tracking_events",
            ["recorded_by", "outreach_draft_id", "prospect_experiment_link_id", "organization_id"],
        ),
        ("prospect_experiment_links", ["prospect_id", "experiment_id", "organization_id"]),
        ("revenue_experiments", ["created_by", "organization_id"]),
    ]:
        for column in columns:
            op.drop_index(op.f(f"ix_{table}_{column}"), table_name=table)
        op.drop_table(table)
    with op.batch_alter_table("sales_conversation_analyses") as batch:
        batch.drop_column("objection_type")
        batch.drop_column("buying_signal")
        batch.drop_column("customer_reply")
    with op.batch_alter_table("growth_outreach_drafts") as batch:
        for name in [
            "soft_cta",
            "gift_explanation",
            "problem_observation",
            "personalized_context",
            "opening_sentence",
            "subject_options",
        ]:
            batch.drop_column(name)
    op.execute("UPDATE growth_gifts SET status = 'sent' WHERE status = 'delivered'")
    with op.batch_alter_table("growth_gifts") as batch:
        batch.drop_column("evidence_reference")
    with op.batch_alter_table("growth_prospects") as batch:
        batch.drop_index(op.f("ix_growth_prospects_source_candidate_id"))
        batch.drop_constraint(
            "fk_growth_prospects_source_candidate_id_prospect_candidates",
            type_="foreignkey",
        )
        batch.drop_column("source_candidate_id")
