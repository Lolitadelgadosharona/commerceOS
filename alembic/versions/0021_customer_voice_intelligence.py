"""Customer voice intelligence foundation.

Revision ID: 0021_customer_voice
Revises: 0020_reddit_intelligence
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0021_customer_voice"
down_revision: str | None = "0020_reddit_intelligence"
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


def organization() -> sa.ForeignKeyConstraint:
    return sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"])


def org_index(table: str) -> None:
    op.create_index(f"ix_{table}_organization_id", table, ["organization_id"])


def upgrade() -> None:
    op.create_table(
        "customer_pain_clusters",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("category", sa.String(80), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("severity_score", sa.Float(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("scoring_evidence", sa.JSON(), nullable=False),
        sa.CheckConstraint("severity_score BETWEEN 0 AND 100", name="severity_range"),
        sa.CheckConstraint("confidence_score BETWEEN 0 AND 1", name="confidence_range"),
        organization(),
        sa.PrimaryKeyConstraint("id"),
    )
    org_index("customer_pain_clusters")
    op.create_table(
        "pain_cluster_memberships",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("cluster_id", uuid, nullable=False),
        sa.Column("pain_candidate_id", uuid, nullable=False),
        sa.Column("relevance_score", sa.Float(), nullable=False),
        sa.CheckConstraint("relevance_score BETWEEN 0 AND 1", name="relevance_range"),
        organization(),
        sa.ForeignKeyConstraint(["cluster_id"], ["customer_pain_clusters.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["pain_candidate_id"], ["customer_pain_candidates.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    org_index("pain_cluster_memberships")
    op.create_index(
        "ix_pain_cluster_memberships_cluster_id", "pain_cluster_memberships", ["cluster_id"]
    )
    op.create_index(
        "ix_pain_cluster_memberships_pain_candidate_id",
        "pain_cluster_memberships",
        ["pain_candidate_id"],
    )
    op.create_table(
        "customer_language_insights",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("cluster_id", uuid, nullable=False),
        sa.Column("phrase", sa.Text(), nullable=False),
        sa.Column("context", sa.Text(), nullable=False),
        sa.Column("usage_type", sa.String(20), nullable=False),
        sa.Column("frequency", sa.Integer(), nullable=False),
        sa.CheckConstraint("frequency >= 0", name="frequency_nonnegative"),
        organization(),
        sa.ForeignKeyConstraint(["cluster_id"], ["customer_pain_clusters.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    org_index("customer_language_insights")
    op.create_index(
        "ix_customer_language_insights_cluster_id",
        "customer_language_insights",
        ["cluster_id"],
    )
    op.create_table(
        "purchase_intent_signals",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("source_record_id", uuid, nullable=False),
        sa.Column("intent_type", sa.String(30), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("intent_score", sa.Float(), nullable=False),
        sa.CheckConstraint("confidence_score BETWEEN 0 AND 1", name="confidence_range"),
        sa.CheckConstraint("intent_score BETWEEN 0 AND 100", name="intent_score_range"),
        organization(),
        sa.ForeignKeyConstraint(
            ["source_record_id"], ["market_data_records.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    org_index("purchase_intent_signals")
    op.create_index(
        "ix_purchase_intent_signals_source_record_id",
        "purchase_intent_signals",
        ["source_record_id"],
    )


def downgrade() -> None:
    for table in (
        "purchase_intent_signals",
        "customer_language_insights",
        "pain_cluster_memberships",
        "customer_pain_clusters",
    ):
        op.drop_table(table)
