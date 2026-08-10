"""Supplier intelligence foundation.

Revision ID: 0007_supplier_intelligence
Revises: 0006_product_truth
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0007_supplier_intelligence"
down_revision: str | None = "0006_product_truth"
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


def indexes(table: str, *references: str) -> None:
    op.create_index(f"ix_{table}_organization_id", table, ["organization_id"])
    for reference in references:
        op.create_index(f"ix_{table}_{reference}", table, [reference])


def supplier_fk(column: str = "supplier_id") -> sa.ForeignKeyConstraint:
    return sa.ForeignKeyConstraint([column], ["supplier_profiles.id"], ondelete="CASCADE")


def upgrade() -> None:
    op.create_table(
        "supplier_profiles",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("name", sa.String(250), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("country", sa.String(100), nullable=False),
        sa.Column("capabilities", sa.JSON(), nullable=False),
        sa.Column("certifications", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes("supplier_profiles")
    score_columns = [
        "quality_score",
        "price_score",
        "lead_time_score",
        "communication_score",
        "compliance_score",
        "overall_score",
    ]
    op.create_table(
        "supplier_evaluations",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("supplier_id", uuid, nullable=False),
        *(sa.Column(name, sa.Float(), nullable=False) for name in score_columns),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("formula_version", sa.String(30), nullable=False),
        *(
            sa.CheckConstraint(
                f"{name} BETWEEN 0 AND 100", name=f"{name.removesuffix('_score')}_range"
            )
            for name in score_columns
        ),
        sa.CheckConstraint("confidence_score BETWEEN 0 AND 1", name="confidence_range"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        supplier_fk(),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes("supplier_evaluations", "supplier_id")
    op.create_table(
        "supplier_risks",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("supplier_id", uuid, nullable=False),
        sa.Column("risk_type", sa.String(30), nullable=False),
        sa.Column("severity", sa.String(30), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        supplier_fk(),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes("supplier_risks", "supplier_id")
    op.create_table(
        "product_supplier_matches",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("product_id", uuid, nullable=False),
        sa.Column("supplier_id", uuid, nullable=False),
        sa.Column("match_score", sa.Float(), nullable=False),
        sa.Column("recommended", sa.Boolean(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.CheckConstraint("match_score BETWEEN 0 AND 100", name="match_range"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        supplier_fk(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_id", "supplier_id"),
    )
    indexes("product_supplier_matches", "product_id", "supplier_id")
    op.create_table(
        "supplier_decision_records",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("product_id", uuid, nullable=False),
        sa.Column("selected_supplier_id", uuid, nullable=False),
        sa.Column("decision_reason", sa.Text(), nullable=False),
        sa.Column("evidence_reference", sa.String(500), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        supplier_fk("selected_supplier_id"),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes("supplier_decision_records", "product_id", "selected_supplier_id")


def downgrade() -> None:
    for table in (
        "supplier_decision_records",
        "product_supplier_matches",
        "supplier_risks",
        "supplier_evaluations",
        "supplier_profiles",
    ):
        op.drop_table(table)
