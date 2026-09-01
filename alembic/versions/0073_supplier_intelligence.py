"""Governed supplier intelligence, quotes, and Product-Supplier approvals.

Revision ID: 0073_supplier_intelligence
Revises: 0072_governed_product_promotion
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0073_supplier_intelligence"
down_revision: str | None = "0072_governed_product_promotion"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _identity_columns() -> list[sa.Column]:
    return [
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "supplier_evidence",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("supplier_id", sa.Uuid(), nullable=False),
        sa.Column("field_name", sa.String(100), nullable=False),
        sa.Column("value", sa.JSON(), nullable=True),
        sa.Column("classification", sa.String(30), nullable=False),
        sa.Column("source", sa.String(250), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("as_of", sa.DateTime(timezone=True), nullable=True),
        sa.Column("evidence_reference", sa.String(500), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        *_identity_columns(),
        sa.CheckConstraint(
            "confidence IS NULL OR confidence BETWEEN 0 AND 1", name="confidence_range"
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["supplier_id"], ["supplier_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_supplier_evidence_organization_id"), "supplier_evidence", ["organization_id"]
    )
    op.create_index(op.f("ix_supplier_evidence_supplier_id"), "supplier_evidence", ["supplier_id"])

    op.create_table(
        "supplier_quotes",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("supplier_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("unit_price", sa.Numeric(14, 4), nullable=True),
        sa.Column("minimum_order_quantity", sa.Integer(), nullable=True),
        sa.Column("price_tiers", sa.JSON(), nullable=False),
        sa.Column("sample_cost", sa.Numeric(14, 4), nullable=True),
        sa.Column("tooling_cost", sa.Numeric(14, 4), nullable=True),
        sa.Column("packaging_cost", sa.Numeric(14, 4), nullable=True),
        sa.Column("incoterm", sa.String(30), nullable=True),
        sa.Column("payment_terms", sa.String(250), nullable=True),
        sa.Column("lead_time", sa.String(200), nullable=True),
        sa.Column("quote_date", sa.Date(), nullable=False),
        sa.Column("valid_until", sa.Date(), nullable=True),
        sa.Column("classification", sa.String(30), nullable=False),
        sa.Column("source", sa.String(250), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("evidence_reference", sa.String(500), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        *_identity_columns(),
        sa.CheckConstraint("unit_price IS NULL OR unit_price >= 0", name="unit_price_nonnegative"),
        sa.CheckConstraint(
            "minimum_order_quantity IS NULL OR minimum_order_quantity >= 1", name="moq_positive"
        ),
        sa.CheckConstraint(
            "sample_cost IS NULL OR sample_cost >= 0", name="sample_cost_nonnegative"
        ),
        sa.CheckConstraint(
            "tooling_cost IS NULL OR tooling_cost >= 0", name="tooling_cost_nonnegative"
        ),
        sa.CheckConstraint(
            "packaging_cost IS NULL OR packaging_cost >= 0", name="packaging_cost_nonnegative"
        ),
        sa.CheckConstraint(
            "confidence IS NULL OR confidence BETWEEN 0 AND 1", name="confidence_range"
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["supplier_id"], ["supplier_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("organization_id", "supplier_id", "product_id"):
        op.create_index(op.f(f"ix_supplier_quotes_{column}"), "supplier_quotes", [column])

    op.create_table(
        "approved_product_suppliers",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("supplier_id", sa.Uuid(), nullable=False),
        sa.Column("source_candidate_id", sa.Uuid(), nullable=True),
        sa.Column("approval_request_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(30), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("approved_by", sa.Uuid(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        *_identity_columns(),
        sa.ForeignKeyConstraint(["approval_request_id"], ["approval_requests.id"]),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["source_candidate_id"], ["supplier_candidates.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["supplier_id"], ["supplier_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("approval_request_id"),
        sa.UniqueConstraint("product_id", "supplier_id"),
    )
    for column in (
        "organization_id",
        "product_id",
        "supplier_id",
        "source_candidate_id",
        "approval_request_id",
    ):
        op.create_index(
            op.f(f"ix_approved_product_suppliers_{column}"), "approved_product_suppliers", [column]
        )


def downgrade() -> None:
    for column in reversed(
        (
            "organization_id",
            "product_id",
            "supplier_id",
            "source_candidate_id",
            "approval_request_id",
        )
    ):
        op.drop_index(
            op.f(f"ix_approved_product_suppliers_{column}"), table_name="approved_product_suppliers"
        )
    op.drop_table("approved_product_suppliers")
    for column in reversed(("organization_id", "supplier_id", "product_id")):
        op.drop_index(op.f(f"ix_supplier_quotes_{column}"), table_name="supplier_quotes")
    op.drop_table("supplier_quotes")
    op.drop_index(op.f("ix_supplier_evidence_supplier_id"), table_name="supplier_evidence")
    op.drop_index(op.f("ix_supplier_evidence_organization_id"), table_name="supplier_evidence")
    op.drop_table("supplier_evidence")
