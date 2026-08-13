"""marketplace customer voice foundation

Revision ID: 0037_marketplace_voice
Revises: 0036_external_connectors
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0037_marketplace_voice"
down_revision: str | None = "0036_external_connectors"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "marketplace_review_evidence",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("connector_id", sa.Uuid(), nullable=False),
        sa.Column("ingestion_job_id", sa.Uuid(), nullable=True),
        sa.Column("source_record_id", sa.Uuid(), nullable=False),
        sa.Column("marketplace", sa.String(30), nullable=False),
        sa.Column("source_identity", sa.String(500), nullable=False),
        sa.Column("product_reference", sa.String(500), nullable=False),
        sa.Column("rating", sa.Float(), nullable=False),
        sa.Column("review_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("review_text_metadata", sa.JSON(), nullable=False),
        sa.Column("verified_indicator", sa.Boolean(), nullable=True),
        sa.Column("evidence_hash", sa.String(64), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "rating >= 0 AND rating <= 5", name=op.f("ck_marketplace_review_evidence_rating_range")
        ),
        sa.ForeignKeyConstraint(
            ["connector_id"],
            ["market_connector_definitions.id"],
            name=op.f("fk_marketplace_review_evidence_connector_id_market_connector_definitions"),
        ),
        sa.ForeignKeyConstraint(
            ["ingestion_job_id"],
            ["market_ingestion_jobs.id"],
            name=op.f("fk_marketplace_review_evidence_ingestion_job_id_market_ingestion_jobs"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_marketplace_review_evidence_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["source_record_id"],
            ["market_data_records.id"],
            name=op.f("fk_marketplace_review_evidence_source_record_id_market_data_records"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_marketplace_review_evidence")),
        sa.UniqueConstraint(
            "source_record_id", name=op.f("uq_marketplace_review_evidence_source_record_id")
        ),
        sa.UniqueConstraint(
            "organization_id", "marketplace", "source_identity", name="uq_marketplace_review_source"
        ),
        sa.UniqueConstraint("organization_id", "evidence_hash", name="uq_marketplace_review_hash"),
    )
    for column in ("organization_id", "connector_id", "ingestion_job_id", "evidence_hash"):
        op.create_index(
            op.f(f"ix_marketplace_review_evidence_{column}"),
            "marketplace_review_evidence",
            [column],
        )

    op.create_table(
        "normalized_marketplace_reviews",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("review_evidence_id", sa.Uuid(), nullable=False),
        sa.Column("sentiment_metadata", sa.JSON(), nullable=False),
        sa.Column("topic_metadata", sa.JSON(), nullable=False),
        sa.Column("customer_language", sa.Text(), nullable=False),
        sa.Column("product_reference", sa.String(500), nullable=False),
        sa.Column("evidence_confidence", sa.Float(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "evidence_confidence BETWEEN 0 AND 1",
            name=op.f("ck_normalized_marketplace_reviews_evidence_confidence_range"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_normalized_marketplace_reviews_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["review_evidence_id"],
            ["marketplace_review_evidence.id"],
            name=op.f(
                "fk_normalized_marketplace_reviews_review_evidence_id_marketplace_review_evidence"
            ),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_normalized_marketplace_reviews")),
        sa.UniqueConstraint(
            "review_evidence_id", name=op.f("uq_normalized_marketplace_reviews_review_evidence_id")
        ),
    )
    op.create_index(
        op.f("ix_normalized_marketplace_reviews_organization_id"),
        "normalized_marketplace_reviews",
        ["organization_id"],
    )
    op.create_index(
        op.f("ix_normalized_marketplace_reviews_review_evidence_id"),
        "normalized_marketplace_reviews",
        ["review_evidence_id"],
    )

    op.create_table(
        "marketplace_evidence_links",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("review_evidence_id", sa.Uuid(), nullable=False),
        sa.Column("target_type", sa.String(40), nullable=False),
        sa.Column("target_id", sa.Uuid(), nullable=False),
        sa.Column("evidence_strength", sa.Float(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "evidence_strength BETWEEN 0 AND 1",
            name=op.f("ck_marketplace_evidence_links_evidence_strength_range"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_marketplace_evidence_links_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["review_evidence_id"],
            ["marketplace_review_evidence.id"],
            name=op.f(
                "fk_marketplace_evidence_links_review_evidence_id_marketplace_review_evidence"
            ),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_marketplace_evidence_links")),
        sa.UniqueConstraint(
            "review_evidence_id", "target_type", "target_id", name="uq_marketplace_evidence_target"
        ),
    )
    for column in ("organization_id", "review_evidence_id", "target_id"):
        op.create_index(
            op.f(f"ix_marketplace_evidence_links_{column}"), "marketplace_evidence_links", [column]
        )

    op.create_table(
        "competitive_marketplace_observations",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("review_evidence_id", sa.Uuid(), nullable=False),
        sa.Column("competitor_reference", sa.String(500), nullable=False),
        sa.Column("product_observations", sa.JSON(), nullable=False),
        sa.Column("customer_preference_signals", sa.JSON(), nullable=False),
        sa.Column("recurring_complaints", sa.JSON(), nullable=False),
        sa.Column("observation_count", sa.Integer(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "confidence BETWEEN 0 AND 1",
            name=op.f("ck_competitive_marketplace_observations_confidence_range"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_competitive_marketplace_observations_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["review_evidence_id"],
            ["marketplace_review_evidence.id"],
            name=op.f(
                "fk_competitive_marketplace_observations_review_evidence_id_marketplace_review_evidence"
            ),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_competitive_marketplace_observations")),
    )
    op.create_index(
        op.f("ix_competitive_marketplace_observations_organization_id"),
        "competitive_marketplace_observations",
        ["organization_id"],
    )
    op.create_index(
        op.f("ix_competitive_marketplace_observations_review_evidence_id"),
        "competitive_marketplace_observations",
        ["review_evidence_id"],
    )

    if op.get_bind().dialect.name == "postgresql":
        op.execute("""
        CREATE FUNCTION prevent_marketplace_review_mutation() RETURNS trigger AS $$
        BEGIN RAISE EXCEPTION 'Marketplace review evidence is immutable'; END;
        $$ LANGUAGE plpgsql;
        CREATE TRIGGER marketplace_review_evidence_immutable
        BEFORE UPDATE OR DELETE ON marketplace_review_evidence
        FOR EACH ROW EXECUTE FUNCTION prevent_marketplace_review_mutation();
        """)


def downgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        op.execute(
            "DROP TRIGGER IF EXISTS marketplace_review_evidence_immutable "
            "ON marketplace_review_evidence"
        )
        op.execute("DROP FUNCTION IF EXISTS prevent_marketplace_review_mutation()")
    op.drop_table("competitive_marketplace_observations")
    op.drop_table("marketplace_evidence_links")
    op.drop_table("normalized_marketplace_reviews")
    op.drop_table("marketplace_review_evidence")
