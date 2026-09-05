"""Governed supplier validation and Build Readiness.

Revision ID: 0074_build_readiness
Revises: 0073_supplier_intelligence
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0074_build_readiness"
down_revision: str | None = "0073_supplier_intelligence"
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
        "supplier_candidate_promotions",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("supplier_candidate_id", sa.Uuid(), nullable=False),
        sa.Column("supplier_profile_id", sa.Uuid(), nullable=False),
        sa.Column("confirmed_by", sa.Uuid(), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=False),
        *_identity(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["supplier_candidate_id"], ["supplier_candidates.id"]),
        sa.ForeignKeyConstraint(["supplier_profile_id"], ["supplier_profiles.id"]),
        sa.ForeignKeyConstraint(["confirmed_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "supplier_candidate_id"),
    )
    _indexes(
        "supplier_candidate_promotions",
        ("organization_id", "supplier_candidate_id", "supplier_profile_id"),
    )
    op.create_table(
        "product_build_requirements",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("product_truth_id", sa.Uuid(), nullable=False),
        sa.Column("attribute_key", sa.String(100), nullable=False),
        sa.Column("display_label", sa.String(200), nullable=False),
        sa.Column("value", sa.JSON(), nullable=True),
        sa.Column("unit", sa.String(50), nullable=True),
        sa.Column("classification", sa.String(30), nullable=False),
        sa.Column("evidence_reference", sa.String(500), nullable=True),
        sa.Column("required_for_build", sa.Boolean(), nullable=False),
        sa.Column("required_for_listing", sa.Boolean(), nullable=False),
        *_identity(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_truth_id"], ["product_truth.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_truth_id", "attribute_key"),
    )
    _indexes("product_build_requirements", ("organization_id", "product_id", "product_truth_id"))
    op.create_table(
        "build_requirement_policies",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("sample_required", sa.Boolean(), nullable=False),
        sa.Column("inspection_required", sa.Boolean(), nullable=False),
        sa.Column("compliance_evidence_required", sa.Boolean(), nullable=False),
        sa.Column("packaging_validation_required", sa.Boolean(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        *_identity(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "product_id"),
    )
    _indexes("build_requirement_policies", ("organization_id", "product_id"))
    op.create_table(
        "product_samples",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("supplier_id", sa.Uuid(), nullable=False),
        sa.Column("approved_product_supplier_id", sa.Uuid(), nullable=True),
        sa.Column("sample_identifier", sa.String(150), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("requested_at", sa.Date(), nullable=True),
        sa.Column("received_at", sa.Date(), nullable=True),
        sa.Column("sample_cost", sa.Numeric(14, 4), nullable=True),
        sa.Column("shipping_cost", sa.Numeric(14, 4), nullable=True),
        sa.Column("currency", sa.String(3), nullable=True),
        sa.Column("version_reference", sa.String(250), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("evidence_reference", sa.String(500), nullable=True),
        sa.Column("recorded_by", sa.Uuid(), nullable=False),
        sa.Column("review_status", sa.String(30), nullable=False),
        sa.Column("review_dimensions", sa.JSON(), nullable=False),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("reviewed_by", sa.Uuid(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        *_identity(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["supplier_id"], ["supplier_profiles.id"]),
        sa.ForeignKeyConstraint(
            ["approved_product_supplier_id"], ["approved_product_suppliers.id"]
        ),
        sa.ForeignKeyConstraint(["recorded_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "sample_identifier"),
    )
    _indexes(
        "product_samples",
        ("organization_id", "product_id", "supplier_id", "approved_product_supplier_id"),
    )
    op.create_table(
        "supplier_validation_artifacts",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("supplier_id", sa.Uuid(), nullable=False),
        sa.Column("sample_id", sa.Uuid(), nullable=True),
        sa.Column("validation_type", sa.String(50), nullable=False),
        sa.Column("classification", sa.String(30), nullable=False),
        sa.Column("result", sa.String(30), nullable=False),
        sa.Column("observations", sa.Text(), nullable=False),
        sa.Column("critical_defects", sa.Integer(), nullable=True),
        sa.Column("major_defects", sa.Integer(), nullable=True),
        sa.Column("minor_defects", sa.Integer(), nullable=True),
        sa.Column("evidence_reference", sa.String(500), nullable=True),
        sa.Column("verified_by", sa.Uuid(), nullable=True),
        sa.Column("observed_at", sa.Date(), nullable=True),
        *_identity(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["supplier_id"], ["supplier_profiles.id"]),
        sa.ForeignKeyConstraint(["sample_id"], ["product_samples.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["verified_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _indexes(
        "supplier_validation_artifacts",
        ("organization_id", "product_id", "supplier_id", "sample_id"),
    )
    with op.batch_alter_table("product_economic_input_provenance") as batch_op:
        batch_op.add_column(sa.Column("supplier_quote_id", sa.Uuid(), nullable=True))
        batch_op.create_foreign_key(
            "fk_economic_provenance_supplier_quote",
            "supplier_quotes",
            ["supplier_quote_id"],
            ["id"],
            ondelete="SET NULL",
        )
    op.create_index(
        op.f("ix_product_economic_input_provenance_supplier_quote_id"),
        "product_economic_input_provenance",
        ["supplier_quote_id"],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_product_economic_input_provenance_supplier_quote_id"),
        table_name="product_economic_input_provenance",
    )
    with op.batch_alter_table("product_economic_input_provenance") as batch_op:
        batch_op.drop_constraint("fk_economic_provenance_supplier_quote", type_="foreignkey")
        batch_op.drop_column("supplier_quote_id")
    for table, columns in (
        (
            "supplier_validation_artifacts",
            ("sample_id", "supplier_id", "product_id", "organization_id"),
        ),
        (
            "product_samples",
            ("approved_product_supplier_id", "supplier_id", "product_id", "organization_id"),
        ),
        ("build_requirement_policies", ("product_id", "organization_id")),
        ("product_build_requirements", ("product_truth_id", "product_id", "organization_id")),
        (
            "supplier_candidate_promotions",
            ("supplier_profile_id", "supplier_candidate_id", "organization_id"),
        ),
    ):
        for column in columns:
            op.drop_index(op.f(f"ix_{table}_{column}"), table_name=table)
        op.drop_table(table)
