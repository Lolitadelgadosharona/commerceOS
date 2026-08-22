"""First revenue machine prospect acquisition foundation.

Revision ID: 0061_prospect_acquisition
Revises: 0060_revenue_validation
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0061_prospect_acquisition"
down_revision: str | None = "0060_revenue_validation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def common() -> list[sa.Column]:
    return [
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
    ]


def indexes(table: str, columns: list[str]) -> None:
    for column in columns:
        op.create_index(op.f(f"ix_{table}_{column}"), table, [column])


def upgrade() -> None:
    with op.batch_alter_table("prospect_discovery_sources") as batch:
        batch.add_column(
            sa.Column("adapter_key", sa.String(120), nullable=False, server_default="manual")
        )
        batch.add_column(
            sa.Column(
                "collection_mode", sa.String(30), nullable=False, server_default="human_review"
            )
        )
    with op.batch_alter_table("prospect_discovery_sources") as batch:
        batch.alter_column("adapter_key", server_default=None)
        batch.alter_column("collection_mode", server_default=None)

    op.create_table(
        "website_evidence_snapshots",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("candidate_id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("source_url", sa.String(1000), nullable=False),
        sa.Column("business_name", sa.String(250), nullable=False),
        sa.Column("location", sa.String(250)),
        sa.Column("services", sa.JSON(), nullable=False),
        sa.Column("website_structure", sa.JSON(), nullable=False),
        sa.Column("homepage_signals", sa.JSON(), nullable=False),
        sa.Column("booking_flow_signals", sa.JSON(), nullable=False),
        sa.Column("seo_signals", sa.JSON(), nullable=False),
        sa.Column("geo_visibility_signals", sa.JSON(), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        *common(),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="website_evidence_conf_range"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["candidate_id"], ["prospect_candidates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_id"], ["prospect_discovery_sources.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes("website_evidence_snapshots", ["organization_id", "candidate_id", "source_id"])

    op.create_table(
        "business_profile_evidence_snapshots",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("candidate_id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("source_reference", sa.String(1000), nullable=False),
        sa.Column("review_count", sa.Integer()),
        sa.Column("rating", sa.Float()),
        sa.Column("location", sa.String(250)),
        sa.Column("business_category", sa.String(160)),
        sa.Column("customer_language", sa.JSON(), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        *common(),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="bp_ev_conf"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["candidate_id"], ["prospect_candidates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_id"], ["prospect_discovery_sources.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes("business_profile_evidence_snapshots", ["organization_id", "candidate_id", "source_id"])

    op.create_table(
        "instagram_evidence_snapshots",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("candidate_id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("profile_reference", sa.String(1000), nullable=False),
        sa.Column("profile_information", sa.JSON(), nullable=False),
        sa.Column("posting_frequency", sa.String(120)),
        sa.Column("content_themes", sa.JSON(), nullable=False),
        sa.Column("brand_signals", sa.JSON(), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        *common(),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="instagram_evidence_conf_range"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["candidate_id"], ["prospect_candidates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_id"], ["prospect_discovery_sources.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes("instagram_evidence_snapshots", ["organization_id", "candidate_id", "source_id"])


def downgrade() -> None:
    for table in [
        "instagram_evidence_snapshots",
        "business_profile_evidence_snapshots",
        "website_evidence_snapshots",
    ]:
        for column in ["source_id", "candidate_id", "organization_id"]:
            op.drop_index(op.f(f"ix_{table}_{column}"), table_name=table)
        op.drop_table(table)
    with op.batch_alter_table("prospect_discovery_sources") as batch:
        batch.drop_column("collection_mode")
        batch.drop_column("adapter_key")
