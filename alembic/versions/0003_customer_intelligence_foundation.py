"""Customer intelligence foundation.

Revision ID: 0003_customer_intelligence
Revises: 0002_governance_identity
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003_customer_intelligence"
down_revision: str | None = "0002_governance_identity"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

uuid = sa.Uuid()


def timestamps(*, versioned: bool = True) -> list[sa.Column]:
    columns = [
        sa.Column("id", uuid, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]
    if versioned:
        columns.append(sa.Column("version", sa.Integer(), nullable=False))
    return columns


def upgrade() -> None:
    op.create_table(
        "signal_sources",
        *timestamps(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "source_type", "name"),
    )
    op.create_index("ix_signal_sources_organization_id", "signal_sources", ["organization_id"])
    op.create_table(
        "customer_signals",
        *timestamps(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("signal_source_id", uuid, nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("source_reference", sa.String(500), nullable=False),
        sa.Column("customer_id", uuid),
        sa.Column("signal_type", sa.String(50), nullable=False),
        sa.Column("content_reference", sa.Text(), nullable=False),
        sa.Column("sentiment", sa.String(30), nullable=False),
        sa.Column("severity", sa.String(30), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["signal_source_id"], ["signal_sources.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("confidence >= 0 AND confidence <= 1", name="confidence_range"),
        sa.UniqueConstraint("organization_id", "source_type", "source_reference"),
    )
    op.create_index("ix_customer_signals_customer_id", "customer_signals", ["customer_id"])
    op.create_index("ix_customer_signals_organization_id", "customer_signals", ["organization_id"])
    op.create_index(
        "ix_customer_signals_signal_source_id", "customer_signals", ["signal_source_id"]
    )
    op.create_index(
        "ix_customer_signals_type_created",
        "customer_signals",
        ["organization_id", "signal_type", "created_at"],
    )
    op.create_table(
        "customer_voice_clusters",
        *timestamps(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("signal_count", sa.Integer(), nullable=False),
        sa.Column("severity", sa.String(30), nullable=False),
        sa.Column("trend_direction", sa.String(30), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("signal_count >= 0", name="signal_count_nonnegative"),
    )
    op.create_index(
        "ix_customer_voice_clusters_organization_id",
        "customer_voice_clusters",
        ["organization_id"],
    )
    op.create_table(
        "signal_cluster_memberships",
        *timestamps(versioned=False),
        sa.Column("cluster_id", uuid, nullable=False),
        sa.Column("signal_id", uuid, nullable=False),
        sa.ForeignKeyConstraint(["cluster_id"], ["customer_voice_clusters.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["signal_id"], ["customer_signals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cluster_id", "signal_id"),
    )
    op.create_index(
        "ix_signal_cluster_memberships_cluster_id",
        "signal_cluster_memberships",
        ["cluster_id"],
    )
    op.create_index(
        "ix_signal_cluster_memberships_signal_id",
        "signal_cluster_memberships",
        ["signal_id"],
    )
    op.create_table(
        "customer_insights",
        *timestamps(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("cluster_id", uuid),
        sa.Column("title", sa.String(250), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("evidence_count", sa.Integer(), nullable=False),
        sa.Column("impact_level", sa.String(30), nullable=False),
        sa.Column("recommended_action", sa.Text(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.ForeignKeyConstraint(["cluster_id"], ["customer_voice_clusters.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("evidence_count >= 1", name="evidence_count_positive"),
    )
    op.create_index("ix_customer_insights_cluster_id", "customer_insights", ["cluster_id"])
    op.create_index(
        "ix_customer_insights_organization_id", "customer_insights", ["organization_id"]
    )
    op.create_table(
        "insight_evidence",
        *timestamps(versioned=False),
        sa.Column("insight_id", uuid, nullable=False),
        sa.Column("signal_id", uuid, nullable=False),
        sa.ForeignKeyConstraint(["insight_id"], ["customer_insights.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["signal_id"], ["customer_signals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("insight_id", "signal_id"),
    )
    op.create_index("ix_insight_evidence_insight_id", "insight_evidence", ["insight_id"])
    op.create_index("ix_insight_evidence_signal_id", "insight_evidence", ["signal_id"])


def downgrade() -> None:
    for table in (
        "insight_evidence",
        "customer_insights",
        "signal_cluster_memberships",
        "customer_voice_clusters",
        "customer_signals",
        "signal_sources",
    ):
        op.drop_table(table)
