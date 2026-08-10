"""Creative strategy foundation.

Revision ID: 0009_creative_strategy
Revises: 0008_listing_geo
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0009_creative_strategy"
down_revision: str | None = "0008_listing_geo"
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
        "creative_strategies",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("product_id", uuid, nullable=False),
        sa.Column("target_audience", sa.Text(), nullable=False),
        sa.Column("marketing_objective", sa.Text(), nullable=False),
        sa.Column("core_message", sa.Text(), nullable=False),
        sa.Column("emotional_angle", sa.Text(), nullable=False),
        sa.Column("creative_direction", sa.Text(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        org(),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_id"),
    )
    indexes("creative_strategies", "product_id")
    op.create_table(
        "creative_hypotheses",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("strategy_id", uuid, nullable=False),
        sa.Column("hypothesis", sa.Text(), nullable=False),
        sa.Column("expected_behavior", sa.Text(), nullable=False),
        sa.Column("success_metric", sa.String(250), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.CheckConstraint("confidence_score BETWEEN 0 AND 1", name="confidence_range"),
        org(),
        sa.ForeignKeyConstraint(["strategy_id"], ["creative_strategies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes("creative_hypotheses", "strategy_id")
    op.create_table(
        "creative_briefs",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("strategy_id", uuid, nullable=False),
        sa.Column("platform", sa.String(50), nullable=False),
        sa.Column("audience", sa.Text(), nullable=False),
        sa.Column("hook", sa.Text(), nullable=False),
        sa.Column("story_structure", sa.Text(), nullable=False),
        sa.Column("proof_points", sa.Text(), nullable=False),
        sa.Column("cta", sa.Text(), nullable=False),
        sa.Column("content_format", sa.String(30), nullable=False),
        org(),
        sa.ForeignKeyConstraint(["strategy_id"], ["creative_strategies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes("creative_briefs", "strategy_id")
    op.create_table(
        "creative_channel_fits",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("product_id", uuid, nullable=False),
        sa.Column("channel", sa.String(30), nullable=False),
        sa.Column("suitability_score", sa.Float(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.CheckConstraint("suitability_score BETWEEN 0 AND 100", name="suitability_range"),
        org(),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_id", "channel"),
    )
    indexes("creative_channel_fits", "product_id")
    op.create_table(
        "creative_experiments",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("hypothesis_id", uuid, nullable=False),
        sa.Column("variant_name", sa.String(250), nullable=False),
        sa.Column("test_objective", sa.Text(), nullable=False),
        sa.Column("metric", sa.String(250), nullable=False),
        sa.Column("result", sa.Text()),
        sa.Column("status", sa.String(30), nullable=False),
        org(),
        sa.ForeignKeyConstraint(["hypothesis_id"], ["creative_hypotheses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes("creative_experiments", "hypothesis_id")


def downgrade() -> None:
    for table in (
        "creative_experiments",
        "creative_channel_fits",
        "creative_briefs",
        "creative_hypotheses",
        "creative_strategies",
    ):
        op.drop_table(table)
