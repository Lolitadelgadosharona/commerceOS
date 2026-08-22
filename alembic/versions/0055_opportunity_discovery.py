"""Opportunity discovery engine foundation.

Revision ID: 0055_opportunity_discovery
Revises: 0054_demand_enhancement
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0055_opportunity_discovery"
down_revision: str | None = "0054_demand_enhancement"
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
    with op.batch_alter_table("opportunity_discovery_candidates") as batch:
        batch.alter_column("discovery_run_id", nullable=True)
        batch.add_column(
            sa.Column("category", sa.String(150), nullable=False, server_default="uncategorized")
        )
        batch.add_column(
            sa.Column("opportunity_description", sa.Text(), nullable=False, server_default="")
        )
        batch.add_column(sa.Column("market_context", sa.Text(), nullable=False, server_default=""))
    with op.batch_alter_table("opportunity_discovery_candidates") as batch:
        batch.alter_column("category", server_default=None)
        batch.alter_column("opportunity_description", server_default=None)
        batch.alter_column("market_context", server_default=None)

    op.create_table(
        "opportunity_candidate_evidence",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("opportunity_candidate_id", sa.Uuid(), nullable=False),
        sa.Column("demand_signal_id", sa.Uuid(), nullable=False),
        sa.Column("evidence_type", sa.String(40), nullable=False),
        sa.Column("evidence_summary", sa.Text(), nullable=False),
        sa.Column("contribution", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        *common(),
        sa.CheckConstraint(
            "confidence BETWEEN 0 AND 1",
            name=op.f("ck_opportunity_candidate_evidence_candidate_evidence_conf"),
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["opportunity_candidate_id"],
            ["opportunity_discovery_candidates.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["demand_signal_id"], ["demand_signals.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("opportunity_candidate_id", "demand_signal_id"),
    )
    op.create_index(
        op.f("ix_opportunity_candidate_evidence_organization_id"),
        "opportunity_candidate_evidence",
        ["organization_id"],
    )
    op.create_index(
        op.f("ix_opportunity_candidate_evidence_opportunity_candidate_id"),
        "opportunity_candidate_evidence",
        ["opportunity_candidate_id"],
    )
    op.create_index(
        op.f("ix_opportunity_candidate_evidence_demand_signal_id"),
        "opportunity_candidate_evidence",
        ["demand_signal_id"],
    )

    op.create_table(
        "opportunity_candidate_assessments",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("opportunity_candidate_id", sa.Uuid(), nullable=False),
        sa.Column("demand_strength", sa.String(20), nullable=False),
        sa.Column("signal_diversity", sa.Integer(), nullable=False),
        sa.Column("market_timing", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("risks", sa.JSON(), nullable=False),
        sa.Column("missing_information", sa.JSON(), nullable=False),
        sa.Column("assumptions", sa.JSON(), nullable=False),
        *common(),
        sa.CheckConstraint(
            "confidence BETWEEN 0 AND 1",
            name=op.f("ck_opportunity_candidate_assessments_candidate_assessment_conf"),
        ),
        sa.CheckConstraint(
            "signal_diversity > 0",
            name=op.f("ck_opportunity_candidate_assessments_diversity_positive"),
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["opportunity_candidate_id"],
            ["opportunity_discovery_candidates.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("opportunity_candidate_id"),
    )
    op.create_index(
        op.f("ix_opportunity_candidate_assessments_organization_id"),
        "opportunity_candidate_assessments",
        ["organization_id"],
    )
    op.create_index(
        op.f("ix_opportunity_candidate_assessments_opportunity_candidate_id"),
        "opportunity_candidate_assessments",
        ["opportunity_candidate_id"],
    )

    if op.get_context().dialect.name == "postgresql":
        op.execute("""
        CREATE FUNCTION prevent_opportunity_evidence_mutation() RETURNS trigger AS $$
        BEGIN RAISE EXCEPTION 'Opportunity evidence is append-only'; END;
        $$ LANGUAGE plpgsql;
        CREATE TRIGGER opportunity_candidate_evidence_append_only
        BEFORE UPDATE OR DELETE ON opportunity_candidate_evidence
        FOR EACH ROW EXECUTE FUNCTION prevent_opportunity_evidence_mutation();
        """)


def downgrade() -> None:
    if op.get_context().dialect.name == "postgresql":
        op.execute(
            "DROP TRIGGER IF EXISTS opportunity_candidate_evidence_append_only "
            "ON opportunity_candidate_evidence"
        )
        op.execute("DROP FUNCTION IF EXISTS prevent_opportunity_evidence_mutation()")
    for table, columns in [
        ("opportunity_candidate_assessments", ["opportunity_candidate_id", "organization_id"]),
        (
            "opportunity_candidate_evidence",
            ["demand_signal_id", "opportunity_candidate_id", "organization_id"],
        ),
    ]:
        for column in columns:
            op.drop_index(op.f(f"ix_{table}_{column}"), table_name=table)
        op.drop_table(table)
    with op.batch_alter_table("opportunity_discovery_candidates") as batch:
        batch.drop_column("market_context")
        batch.drop_column("opportunity_description")
        batch.drop_column("category")
        batch.alter_column("discovery_run_id", nullable=False)
