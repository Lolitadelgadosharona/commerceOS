"""Governed Listing Truth, claims, evidence, and FAQ.

Revision ID: 0075_listing_intelligence
Revises: 0074_build_readiness
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0075_listing_intelligence"
down_revision: str | None = "0074_build_readiness"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _identity() -> list[sa.Column]:
    return [
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
    ]


def _indexes(table: str, columns: tuple[str, ...]) -> None:
    for column in columns:
        op.create_index(op.f(f"ix_{table}_{column}"), table, [column])


def upgrade() -> None:
    op.create_table(
        "listing_versions",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("product_truth_id", sa.Uuid(), nullable=False),
        sa.Column("product_truth_version", sa.Integer(), nullable=False),
        sa.Column("listing_version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("title", sa.String(250), nullable=False),
        sa.Column("subtitle", sa.String(500)),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("customer_problem", sa.Text()),
        sa.Column("solution", sa.Text()),
        sa.Column("features", sa.JSON(), nullable=False),
        sa.Column("benefits", sa.JSON(), nullable=False),
        sa.Column("specifications", sa.JSON(), nullable=False),
        sa.Column("use_cases", sa.JSON(), nullable=False),
        sa.Column("whats_included", sa.JSON(), nullable=False),
        sa.Column("warnings", sa.JSON(), nullable=False),
        sa.Column("care_usage", sa.Text()),
        sa.Column("shipping_facts", sa.Text()),
        sa.Column("return_facts", sa.Text()),
        sa.Column("risk_reversal", sa.Text()),
        sa.Column("seo_title", sa.String(250)),
        sa.Column("meta_description", sa.String(500)),
        sa.Column("slug_suggestion", sa.String(250)),
        sa.Column("primary_topic", sa.String(250)),
        sa.Column("secondary_topics", sa.JSON(), nullable=False),
        sa.Column("structured_attributes", sa.JSON(), nullable=False),
        sa.Column("commercial_price", sa.Numeric(14, 4)),
        sa.Column("currency", sa.String(3)),
        sa.Column("price_status", sa.String(30), nullable=False),
        sa.Column("change_reason", sa.Text(), nullable=False),
        sa.Column("approval_request_id", sa.Uuid()),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("approved_by", sa.Uuid()),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        *_identity(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_truth_id"], ["product_truth.id"]),
        sa.ForeignKeyConstraint(["approval_request_id"], ["approval_requests.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_id", "listing_version"),
        sa.CheckConstraint("listing_version > 0", name="listing_version_positive"),
    )
    _indexes("listing_versions", ("organization_id", "product_id", "product_truth_id"))
    op.create_table(
        "listing_claims",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("listing_version_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("claim_text", sa.Text(), nullable=False),
        sa.Column("claim_type", sa.String(50), nullable=False),
        sa.Column("classification", sa.String(30), nullable=False),
        sa.Column("support_status", sa.String(30), nullable=False),
        sa.Column("risk_category", sa.String(50), nullable=False),
        sa.Column("review_status", sa.String(30), nullable=False),
        sa.Column("human_review_required", sa.Boolean(), nullable=False),
        sa.Column("blocking", sa.Boolean(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        *_identity(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["listing_version_id"], ["listing_versions.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _indexes("listing_claims", ("organization_id", "listing_version_id", "product_id"))
    op.create_table(
        "listing_claim_evidence",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("claim_id", sa.Uuid(), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("source_reference", sa.String(500), nullable=False),
        sa.Column("evidence_text", sa.Text(), nullable=False),
        sa.Column("classification", sa.String(30), nullable=False),
        *_identity(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["claim_id"], ["listing_claims.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("claim_id", "source_type", "source_reference"),
    )
    _indexes("listing_claim_evidence", ("organization_id", "claim_id"))
    op.create_table(
        "listing_faqs",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("listing_version_id", sa.Uuid(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text()),
        sa.Column("answer_status", sa.String(40), nullable=False),
        sa.Column("evidence_reference", sa.String(500)),
        *_identity(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["listing_version_id"], ["listing_versions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    _indexes("listing_faqs", ("organization_id", "listing_version_id"))


def downgrade() -> None:
    for table in ("listing_faqs", "listing_claim_evidence", "listing_claims", "listing_versions"):
        op.drop_table(table)
