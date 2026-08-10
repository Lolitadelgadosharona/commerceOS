"""Listing intelligence and GEO foundation.

Revision ID: 0008_listing_geo
Revises: 0007_supplier_intelligence
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0008_listing_geo"
down_revision: str | None = "0007_supplier_intelligence"
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


def foundations() -> list[object]:
    return [
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("product_id", uuid, nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    ]


def indexes(table: str) -> None:
    op.create_index(f"ix_{table}_organization_id", table, ["organization_id"])
    op.create_index(f"ix_{table}_product_id", table, ["product_id"])


def upgrade() -> None:
    op.create_table(
        "listing_strategies",
        *common(),
        *foundations(),
        sa.Column("target_customer", sa.Text(), nullable=False),
        sa.Column("value_proposition", sa.Text(), nullable=False),
        sa.Column("positioning", sa.Text(), nullable=False),
        sa.Column("differentiation", sa.Text(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.UniqueConstraint("product_id"),
    )
    indexes("listing_strategies")
    op.create_table(
        "customer_questions",
        *common(),
        *foundations(),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("question_type", sa.String(30), nullable=False),
        sa.Column("source_reference", sa.String(500), nullable=False),
        sa.Column("importance_score", sa.Float(), nullable=False),
        sa.CheckConstraint("importance_score BETWEEN 0 AND 100", name="importance_range"),
        sa.UniqueConstraint("product_id", "question", "source_reference"),
    )
    indexes("customer_questions")
    op.create_table(
        "product_discovery_knowledge",
        *common(),
        *foundations(),
        sa.Column("entity_type", sa.String(30), nullable=False),
        sa.Column("entity_name", sa.String(250), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("relationship", sa.String(250), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.CheckConstraint("confidence_score BETWEEN 0 AND 1", name="confidence_range"),
        sa.UniqueConstraint("product_id", "entity_type", "entity_name", "relationship"),
    )
    indexes("product_discovery_knowledge")
    op.create_table(
        "content_briefs",
        *common(),
        *foundations(),
        sa.Column("headline_direction", sa.Text(), nullable=False),
        sa.Column("key_benefits", sa.JSON(), nullable=False),
        sa.Column("proof_points", sa.JSON(), nullable=False),
        sa.Column("objections", sa.JSON(), nullable=False),
        sa.Column("trust_elements", sa.JSON(), nullable=False),
    )
    indexes("content_briefs")
    op.create_table(
        "listing_evidence",
        *common(),
        *foundations(),
        sa.Column("evidence_type", sa.String(50), nullable=False),
        sa.Column("source_reference", sa.String(500), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.CheckConstraint("confidence_score BETWEEN 0 AND 1", name="confidence_range"),
        sa.UniqueConstraint("product_id", "evidence_type", "source_reference"),
    )
    indexes("listing_evidence")


def downgrade() -> None:
    for table in (
        "listing_evidence",
        "content_briefs",
        "product_discovery_knowledge",
        "customer_questions",
        "listing_strategies",
    ):
        op.drop_table(table)
