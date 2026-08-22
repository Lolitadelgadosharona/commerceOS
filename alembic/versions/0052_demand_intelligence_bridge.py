"""GrowthOS to CommerceOS demand intelligence bridge.

Revision ID: 0052_demand_bridge
Revises: 0051_growthos_conversation
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0052_demand_bridge"
down_revision: str | None = "0051_growthos_conversation"
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
    op.create_table(
        "demand_signals",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("source_domain", sa.String(40), nullable=False),
        sa.Column("source_reference_id", sa.Uuid(), nullable=False),
        sa.Column("customer_segment", sa.String(250), nullable=False),
        sa.Column("category", sa.String(80), nullable=False),
        sa.Column("problem_statement", sa.Text(), nullable=False),
        sa.Column("customer_language", sa.Text(), nullable=False),
        sa.Column("frequency", sa.Integer(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("evidence_count", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        *common(),
        sa.CheckConstraint(
            "confidence BETWEEN 0 AND 1", name=op.f("ck_demand_signals_confidence_range")
        ),
        sa.CheckConstraint("frequency > 0", name=op.f("ck_demand_signals_positive_frequency")),
        sa.CheckConstraint(
            "evidence_count > 0", name=op.f("ck_demand_signals_positive_evidence_count")
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ["organization_id", "source_reference_id"]:
        op.create_index(op.f(f"ix_demand_signals_{column}"), "demand_signals", [column])

    op.create_table(
        "demand_signal_evidence",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("demand_signal_id", sa.Uuid(), nullable=False),
        sa.Column("source_type", sa.String(80), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("evidence_text", sa.Text(), nullable=False),
        *common(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["demand_signal_id"], ["demand_signals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ["organization_id", "demand_signal_id", "source_id"]:
        op.create_index(
            op.f(f"ix_demand_signal_evidence_{column}"),
            "demand_signal_evidence",
            [column],
        )

    if op.get_context().dialect.name == "postgresql":
        op.execute(
            """
            CREATE FUNCTION prevent_demand_evidence_mutation() RETURNS trigger AS $$
            BEGIN RAISE EXCEPTION 'Demand signal evidence is append-only'; END;
            $$ LANGUAGE plpgsql;
            CREATE TRIGGER demand_evidence_append_only
            BEFORE UPDATE OR DELETE ON demand_signal_evidence
            FOR EACH ROW EXECUTE FUNCTION prevent_demand_evidence_mutation();
            """
        )


def downgrade() -> None:
    if op.get_context().dialect.name == "postgresql":
        op.execute("DROP TRIGGER IF EXISTS demand_evidence_append_only ON demand_signal_evidence")
        op.execute("DROP FUNCTION IF EXISTS prevent_demand_evidence_mutation()")
    for column in ["source_id", "demand_signal_id", "organization_id"]:
        op.drop_index(
            op.f(f"ix_demand_signal_evidence_{column}"),
            table_name="demand_signal_evidence",
        )
    op.drop_table("demand_signal_evidence")
    for column in ["source_reference_id", "organization_id"]:
        op.drop_index(op.f(f"ix_demand_signals_{column}"), table_name="demand_signals")
    op.drop_table("demand_signals")
