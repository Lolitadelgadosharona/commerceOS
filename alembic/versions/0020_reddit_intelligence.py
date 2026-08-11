"""Reddit market intelligence connector v1.

Revision ID: 0020_reddit_intelligence
Revises: 0019_market_connectors
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0020_reddit_intelligence"
down_revision: str | None = "0019_market_connectors"
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


def organization_index(table: str) -> None:
    op.create_index(f"ix_{table}_organization_id", table, ["organization_id"])


def upgrade() -> None:
    for name, type_ in (
        ("source_platform", sa.String(30)),
        ("external_id", sa.String(120)),
        ("subreddit", sa.String(120)),
        ("title", sa.String(500)),
        ("content", sa.Text()),
        ("author_reference", sa.String(120)),
        ("engagement_metrics", sa.JSON()),
        ("published_at", sa.DateTime(timezone=True)),
    ):
        op.add_column("market_data_records", sa.Column(name, type_))
    op.create_index("ix_market_data_records_external_id", "market_data_records", ["external_id"])
    op.add_column("market_ingestion_jobs", sa.Column("source_platform", sa.String(30)))

    op.create_table(
        "reddit_connectors",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("connector_definition_id", uuid, nullable=False),
        sa.Column("subreddit_scope", sa.JSON(), nullable=False),
        sa.Column("keyword_scope", sa.JSON(), nullable=False),
        sa.Column("time_window", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        organization(),
        sa.ForeignKeyConstraint(["connector_definition_id"], ["market_connector_definitions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("connector_definition_id"),
    )
    organization_index("reddit_connectors")
    op.create_table(
        "customer_pain_candidates",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("source_record_id", uuid, nullable=False),
        sa.Column("pain_category", sa.String(30), nullable=False),
        sa.Column("customer_language", sa.Text(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.CheckConstraint("confidence_score BETWEEN 0 AND 1", name="confidence_range"),
        organization(),
        sa.ForeignKeyConstraint(
            ["source_record_id"], ["market_data_records.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    organization_index("customer_pain_candidates")
    op.create_index(
        "ix_customer_pain_candidates_source_record_id",
        "customer_pain_candidates",
        ["source_record_id"],
    )
    op.create_table(
        "pain_evidence",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("pain_candidate_id", uuid, nullable=False),
        sa.Column("source_record_id", uuid, nullable=False),
        sa.Column("evidence_strength", sa.Float(), nullable=False),
        sa.CheckConstraint("evidence_strength BETWEEN 0 AND 1", name="evidence_strength_range"),
        organization(),
        sa.ForeignKeyConstraint(
            ["pain_candidate_id"], ["customer_pain_candidates.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["source_record_id"], ["market_data_records.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    organization_index("pain_evidence")
    op.create_index("ix_pain_evidence_pain_candidate_id", "pain_evidence", ["pain_candidate_id"])


def downgrade() -> None:
    op.drop_table("pain_evidence")
    op.drop_table("customer_pain_candidates")
    op.drop_table("reddit_connectors")
    op.drop_column("market_ingestion_jobs", "source_platform")
    op.drop_index("ix_market_data_records_external_id", table_name="market_data_records")
    for name in (
        "published_at",
        "engagement_metrics",
        "author_reference",
        "content",
        "title",
        "subreddit",
        "external_id",
        "source_platform",
    ):
        op.drop_column("market_data_records", name)
