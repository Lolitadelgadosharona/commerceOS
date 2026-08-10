"""Opportunity intelligence analysis foundation.

Revision ID: 0018_opportunity_analysis
Revises: 0017_market_intelligence
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0018_opportunity_analysis"
down_revision: str | None = "0017_market_intelligence"
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


def org() -> sa.ForeignKeyConstraint:
    return sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"])


def indexes(table: str, reference: str) -> None:
    op.create_index(f"ix_{table}_organization_id", table, ["organization_id"])
    op.create_index(f"ix_{table}_{reference}", table, [reference])


def upgrade() -> None:
    op.create_table(
        "market_signal_analyses",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("signal_id", uuid, nullable=False),
        sa.Column("analysis_type", sa.String(60), nullable=False),
        sa.Column("market_impact", sa.Text(), nullable=False),
        sa.Column("timing_assessment", sa.Text(), nullable=False),
        sa.Column("customer_relevance", sa.Text(), nullable=False),
        sa.Column("commercial_relevance", sa.Text(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.CheckConstraint("confidence_score BETWEEN 0 AND 1", name="confidence_range"),
        org(),
        sa.ForeignKeyConstraint(["signal_id"], ["market_signals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes("market_signal_analyses", "signal_id")
    op.create_table(
        "opportunity_assessments",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("market_opportunity_id", uuid, nullable=False),
        sa.Column("demand_score", sa.Float(), nullable=False),
        sa.Column("timing_score", sa.Float(), nullable=False),
        sa.Column("evidence_score", sa.Float(), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("commercial_score", sa.Float(), nullable=False),
        sa.Column("overall_score", sa.Float(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("formula_version", sa.String(40), nullable=False),
        sa.CheckConstraint("demand_score BETWEEN 0 AND 100", name="demand_range"),
        sa.CheckConstraint("timing_score BETWEEN 0 AND 100", name="timing_range"),
        sa.CheckConstraint("evidence_score BETWEEN 0 AND 100", name="evidence_range"),
        sa.CheckConstraint("risk_score BETWEEN 0 AND 100", name="risk_range"),
        sa.CheckConstraint("commercial_score BETWEEN 0 AND 100", name="commercial_range"),
        sa.CheckConstraint("overall_score BETWEEN 0 AND 100", name="overall_range"),
        org(),
        sa.ForeignKeyConstraint(
            ["market_opportunity_id"], ["market_opportunities.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes("opportunity_assessments", "market_opportunity_id")
    op.create_table(
        "opportunity_reports",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("opportunity_id", uuid, nullable=False),
        sa.Column("title", sa.String(250), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("evidence_summary", sa.Text(), nullable=False),
        sa.Column("recommended_actions", sa.JSON(), nullable=False),
        sa.Column("risk_summary", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("decision_queue_item_id", uuid),
        org(),
        sa.ForeignKeyConstraint(
            ["opportunity_id"], ["market_opportunities.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["decision_queue_item_id"], ["decision_queue_items.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes("opportunity_reports", "opportunity_id")


def downgrade() -> None:
    for table in ("opportunity_reports", "opportunity_assessments", "market_signal_analyses"):
        op.drop_table(table)
