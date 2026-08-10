"""Product Truth foundation.

Revision ID: 0006_product_truth
Revises: 0005_product_intelligence
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0006_product_truth"
down_revision: str | None = "0005_product_intelligence"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None
uuid = sa.Uuid()


def common(*, include_version: bool = True) -> list[sa.Column]:
    columns = [
        sa.Column("id", uuid, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]
    if include_version:
        columns.append(sa.Column("version", sa.Integer(), nullable=False))
    return columns


def indexes(table: str, *references: str) -> None:
    op.create_index(f"ix_{table}_organization_id", table, ["organization_id"])
    for reference in references:
        op.create_index(f"ix_{table}_{reference}", table, [reference])


def upgrade() -> None:
    op.create_table(
        "products",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("name", sa.String(250), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(150), nullable=False),
        sa.Column("brand_id", uuid, nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes("products", "brand_id")
    op.create_table(
        "product_truth",
        *common(include_version=False),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("product_id", uuid, nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("features", sa.JSON(), nullable=False),
        sa.Column("specifications", sa.JSON(), nullable=False),
        sa.Column("approved_claims", sa.JSON(), nullable=False),
        sa.Column("restricted_claims", sa.JSON(), nullable=False),
        sa.Column("usage_notes", sa.Text(), nullable=False),
        sa.Column("created_by", uuid, nullable=False),
        sa.Column("approval_id", uuid, nullable=False),
        sa.CheckConstraint("version > 0", name="version_positive"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["approval_id"], ["approval_requests.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("approval_id"),
        sa.UniqueConstraint("product_id", "version"),
    )
    indexes("product_truth", "product_id")
    op.create_table(
        "product_knowledge_items",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("product_id", uuid, nullable=False),
        sa.Column("type", sa.String(30), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("approval_status", sa.String(30), nullable=False),
        sa.CheckConstraint("confidence >= 0 AND confidence <= 1", name="confidence_range"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes("product_knowledge_items", "product_id")
    op.create_table(
        "product_claim_policies",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("brand_id", uuid, nullable=False),
        sa.Column("claim_type", sa.String(100), nullable=False),
        sa.Column("allowed", sa.Boolean(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("evidence_required", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("brand_id", "claim_type"),
    )
    indexes("product_claim_policies", "brand_id")


def downgrade() -> None:
    for table in ("product_claim_policies", "product_knowledge_items", "product_truth", "products"):
        op.drop_table(table)
