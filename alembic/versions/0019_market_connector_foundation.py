"""Market intelligence connector foundation.

Revision ID: 0019_market_connectors
Revises: 0018_opportunity_analysis
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0019_market_connectors"
down_revision: str | None = "0018_opportunity_analysis"
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


def indexes(table: str, reference: str | None = None) -> None:
    op.create_index(f"ix_{table}_organization_id", table, ["organization_id"])
    if reference:
        op.create_index(f"ix_{table}_{reference}", table, [reference])


def upgrade() -> None:
    op.create_table(
        "market_connector_definitions",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("platform", sa.String(80), nullable=False),
        sa.Column("connector_type", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("configuration_schema", sa.JSON(), nullable=False),
        organization(),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes("market_connector_definitions")
    op.create_table(
        "market_data_records",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("source_id", uuid, nullable=False),
        sa.Column("external_reference", sa.String(500), nullable=False),
        sa.Column("content_type", sa.String(80), nullable=False),
        sa.Column("raw_content", sa.Text(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        organization(),
        sa.ForeignKeyConstraint(["source_id"], ["market_connector_definitions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes("market_data_records", "source_id")
    op.create_table(
        "normalized_market_items",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("source_record_id", uuid, nullable=False),
        sa.Column("category", sa.String(150), nullable=False),
        sa.Column("topic", sa.String(200), nullable=False),
        sa.Column("customer_language", sa.Text(), nullable=False),
        sa.Column("signal_type", sa.String(80), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),
        organization(),
        sa.ForeignKeyConstraint(
            ["source_record_id"], ["market_data_records.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes("normalized_market_items", "source_record_id")
    op.create_table(
        "market_ingestion_jobs",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("source_id", uuid, nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("record_count", sa.Integer(), nullable=False),
        sa.CheckConstraint("record_count >= 0", name="record_count_nonnegative"),
        organization(),
        sa.ForeignKeyConstraint(["source_id"], ["market_connector_definitions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes("market_ingestion_jobs", "source_id")


def downgrade() -> None:
    for table in (
        "market_ingestion_jobs",
        "normalized_market_items",
        "market_data_records",
        "market_connector_definitions",
    ):
        op.drop_table(table)
