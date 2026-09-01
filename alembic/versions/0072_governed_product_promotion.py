"""Governed product promotion and Product Truth drafts.

Revision ID: 0072_governed_product_promotion
Revises: 0071_intelligence_provenance
"""

from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import uuid4

import sqlalchemy as sa

from alembic import op

revision: str = "0072_governed_product_promotion"
down_revision: str | None = "0071_intelligence_provenance"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "product_promotions",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("product_hypothesis_id", sa.Uuid(), nullable=False),
        sa.Column("opportunity_id", sa.Uuid(), nullable=False),
        sa.Column("brand_id", sa.Uuid(), nullable=False),
        sa.Column("approval_request_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=True),
        sa.Column("requested_by", sa.Uuid(), nullable=False),
        sa.Column("promoted_by", sa.Uuid(), nullable=True),
        sa.Column("promoted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["approval_request_id"], ["approval_requests.id"]),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.id"]),
        sa.ForeignKeyConstraint(["opportunity_id"], ["market_opportunities.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["product_hypothesis_id"], ["product_hypotheses.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["promoted_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["requested_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("approval_request_id"),
        sa.UniqueConstraint("organization_id", "product_hypothesis_id"),
        sa.UniqueConstraint("product_id"),
    )
    for column in (
        "organization_id",
        "product_hypothesis_id",
        "opportunity_id",
        "brand_id",
        "approval_request_id",
        "product_id",
    ):
        op.create_index(op.f(f"ix_product_promotions_{column}"), "product_promotions", [column])

    op.create_table(
        "product_truth_drafts",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("features", sa.JSON(), nullable=False),
        sa.Column("specifications", sa.JSON(), nullable=False),
        sa.Column("approved_claims", sa.JSON(), nullable=False),
        sa.Column("restricted_claims", sa.JSON(), nullable=False),
        sa.Column("usage_notes", sa.Text(), nullable=False),
        sa.Column("change_reason", sa.Text(), nullable=False),
        sa.Column("supporting_evidence", sa.JSON(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("approval_request_id", sa.Uuid(), nullable=True),
        sa.Column("truth_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["approval_request_id"], ["approval_requests.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["truth_id"], ["product_truth.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("approval_request_id"),
        sa.UniqueConstraint("truth_id"),
    )
    op.create_index(
        op.f("ix_product_truth_drafts_organization_id"),
        "product_truth_drafts",
        ["organization_id"],
    )
    op.create_index(
        op.f("ix_product_truth_drafts_product_id"),
        "product_truth_drafts",
        ["product_id"],
    )

    connection = op.get_bind()
    economics = sa.table(
        "product_economics",
        sa.column("id", sa.Uuid()),
        sa.column("organization_id", sa.Uuid()),
        sa.column("selling_price", sa.Numeric()),
        sa.column("estimated_product_cost", sa.Numeric()),
        sa.column("estimated_shipping_cost", sa.Numeric()),
        sa.column("payment_cost", sa.Numeric()),
        sa.column("estimated_marketing_cost", sa.Numeric()),
    )
    provenance = sa.table(
        "product_economic_input_provenance",
        sa.column("id", sa.Uuid()),
        sa.column("organization_id", sa.Uuid()),
        sa.column("product_economics_id", sa.Uuid()),
        sa.column("metric", sa.String()),
        sa.column("value", sa.Numeric()),
        sa.column("classification", sa.String()),
        sa.column("source", sa.String()),
        sa.column("confidence", sa.Float()),
        sa.column("as_of", sa.DateTime(timezone=True)),
        sa.column("evidence_reference", sa.String()),
        sa.column("notes", sa.Text()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
        sa.column("version", sa.Integer()),
    )
    existing = {
        (row.product_economics_id, row.metric)
        for row in connection.execute(
            sa.select(provenance.c.product_economics_id, provenance.c.metric)
        )
    }
    now = datetime.now(UTC)
    metric_columns = (
        "selling_price",
        "estimated_product_cost",
        "estimated_shipping_cost",
        "payment_cost",
        "estimated_marketing_cost",
    )
    records: list[dict[str, object]] = []
    for row in connection.execute(sa.select(economics)).mappings():
        for metric in metric_columns:
            if (row["id"], metric) in existing:
                continue
            records.append(
                {
                    "id": uuid4(),
                    "organization_id": row["organization_id"],
                    "product_economics_id": row["id"],
                    "metric": metric,
                    "value": row[metric],
                    "classification": "legacy_unprovenanced",
                    "source": "legacy_product_economics",
                    "confidence": None,
                    "as_of": None,
                    "evidence_reference": None,
                    "notes": "Backfilled without claiming source provenance.",
                    "created_at": now,
                    "updated_at": now,
                    "version": 1,
                }
            )
    if records:
        op.bulk_insert(provenance, records)


def downgrade() -> None:
    op.execute(
        "DELETE FROM product_economic_input_provenance "
        "WHERE classification = 'legacy_unprovenanced' "
        "AND source = 'legacy_product_economics'"
    )
    op.drop_index(op.f("ix_product_truth_drafts_product_id"), table_name="product_truth_drafts")
    op.drop_index(
        op.f("ix_product_truth_drafts_organization_id"), table_name="product_truth_drafts"
    )
    op.drop_table("product_truth_drafts")
    for column in reversed(
        (
            "organization_id",
            "product_hypothesis_id",
            "opportunity_id",
            "brand_id",
            "approval_request_id",
            "product_id",
        )
    ):
        op.drop_index(op.f(f"ix_product_promotions_{column}"), table_name="product_promotions")
    op.drop_table("product_promotions")
