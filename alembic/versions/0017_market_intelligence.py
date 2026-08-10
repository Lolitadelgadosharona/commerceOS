"""Market intelligence data foundation.

Revision ID: 0017_market_intelligence
Revises: 0016_commerce_execution
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0017_market_intelligence"
down_revision: str | None = "0016_commerce_execution"
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


def indexes(table: str, reference: str | None = None) -> None:
    op.create_index(f"ix_{table}_organization_id", table, ["organization_id"])
    if reference:
        op.create_index(f"ix_{table}_{reference}", table, [reference])


def upgrade() -> None:
    op.create_table(
        "market_data_sources",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("platform", sa.String(40), nullable=False),
        sa.Column("source_type", sa.String(40), nullable=False),
        sa.Column("access_method", sa.String(40), nullable=False),
        sa.Column("reliability_score", sa.Float(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.CheckConstraint("reliability_score BETWEEN 0 AND 1", name="reliability_range"),
        org(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "name"),
    )
    indexes("market_data_sources")
    op.create_table(
        "market_signals",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("source_id", uuid, nullable=False),
        sa.Column("region", sa.String(120), nullable=False),
        sa.Column("category", sa.String(150), nullable=False),
        sa.Column("signal_type", sa.String(80), nullable=False),
        sa.Column("title", sa.String(250), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("trend_direction", sa.String(20), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.CheckConstraint("confidence_score BETWEEN 0 AND 1", name="confidence_range"),
        org(),
        sa.ForeignKeyConstraint(["source_id"], ["market_data_sources.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes("market_signals", "source_id")
    op.create_table(
        "market_signal_evidence",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("signal_id", uuid, nullable=False),
        sa.Column("evidence_type", sa.String(60), nullable=False),
        sa.Column("content_reference", sa.String(500), nullable=False),
        sa.Column("strength_score", sa.Float(), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("strength_score BETWEEN 0 AND 1", name="strength_range"),
        org(),
        sa.ForeignKeyConstraint(["signal_id"], ["market_signals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("signal_id", "evidence_type", "content_reference"),
    )
    indexes("market_signal_evidence", "signal_id")
    op.create_table(
        "market_signal_clusters",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("category", sa.String(150), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("impact_score", sa.Float(), nullable=False),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),
        sa.CheckConstraint("impact_score BETWEEN 0 AND 100", name="impact_range"),
        org(),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes("market_signal_clusters")
    op.create_table(
        "market_signal_cluster_memberships",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("cluster_id", uuid, nullable=False),
        sa.Column("signal_id", uuid, nullable=False),
        org(),
        sa.ForeignKeyConstraint(["cluster_id"], ["market_signal_clusters.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["signal_id"], ["market_signals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cluster_id", "signal_id"),
    )
    indexes("market_signal_cluster_memberships")
    op.create_table(
        "market_signal_opportunity_links",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("signal_id", uuid, nullable=False),
        sa.Column("opportunity_id", uuid, nullable=False),
        org(),
        sa.ForeignKeyConstraint(["signal_id"], ["market_signals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["opportunity_id"], ["market_opportunities.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("signal_id", "opportunity_id"),
    )
    indexes("market_signal_opportunity_links")


def downgrade() -> None:
    for table in (
        "market_signal_opportunity_links",
        "market_signal_cluster_memberships",
        "market_signal_clusters",
        "market_signal_evidence",
        "market_signals",
        "market_data_sources",
    ):
        op.drop_table(table)
