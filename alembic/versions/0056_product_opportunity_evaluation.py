"""Product opportunity evaluation foundation.

Revision ID: 0056_product_evaluation
Revises: 0055_opportunity_discovery
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0056_product_evaluation"
down_revision: str | None = "0055_opportunity_discovery"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def common() -> list[sa.Column]:
    return [
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
    ]


def index(table: str, column: str) -> None:
    op.create_index(op.f(f"ix_{table}_{column}"), table, [column])


def upgrade() -> None:
    with op.batch_alter_table("product_candidates") as batch:
        batch.alter_column("opportunity_id", nullable=True)
        batch.add_column(sa.Column("opportunity_candidate_id", sa.Uuid()))
        batch.add_column(sa.Column("target_customer", sa.Text(), nullable=False, server_default=""))
        batch.add_column(
            sa.Column("product_description", sa.Text(), nullable=False, server_default="")
        )
        batch.add_column(
            sa.Column("value_proposition", sa.Text(), nullable=False, server_default="")
        )
        batch.add_column(
            sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0")
        )
        batch.create_foreign_key(
            op.f("fk_product_candidates_opportunity_candidate_id_opportunity_discovery_candidates"),
            "opportunity_discovery_candidates",
            ["opportunity_candidate_id"],
            ["id"],
            ondelete="CASCADE",
        )
    index("product_candidates", "opportunity_candidate_id")
    with op.batch_alter_table("product_candidates") as batch:
        for column in [
            "target_customer",
            "product_description",
            "value_proposition",
            "confidence_score",
        ]:
            batch.alter_column(column, server_default=None)

    op.create_table(
        "product_evaluations",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("product_candidate_id", sa.Uuid(), nullable=False),
        sa.Column("demand_fit_score", sa.Float(), nullable=False),
        sa.Column("problem_solution_fit", sa.Float(), nullable=False),
        sa.Column("estimated_price_range", sa.JSON(), nullable=False),
        sa.Column("estimated_cost_range", sa.JSON(), nullable=False),
        sa.Column("gross_margin_estimate", sa.Float(), nullable=False),
        sa.Column("shipping_complexity", sa.String(20), nullable=False),
        sa.Column("fulfillment_risk", sa.String(20), nullable=False),
        sa.Column("ip_risk", sa.String(20), nullable=False),
        sa.Column("regulatory_risk", sa.String(20), nullable=False),
        sa.Column("payment_risk", sa.String(20), nullable=False),
        sa.Column("dispute_risk", sa.String(20), nullable=False),
        sa.Column("strengths", sa.JSON(), nullable=False),
        sa.Column("weaknesses", sa.JSON(), nullable=False),
        sa.Column("assumptions", sa.JSON(), nullable=False),
        sa.Column("missing_information", sa.JSON(), nullable=False),
        sa.Column("evaluation_score", sa.Float(), nullable=False),
        sa.Column("recommendation", sa.Text(), nullable=False),
        sa.Column("formula_version", sa.String(50), nullable=False),
        *common(),
        sa.CheckConstraint(
            "demand_fit_score BETWEEN 0 AND 100",
            name=op.f("ck_product_evaluations_demand_fit_range"),
        ),
        sa.CheckConstraint(
            "problem_solution_fit BETWEEN 0 AND 100",
            name=op.f("ck_product_evaluations_solution_fit_range"),
        ),
        sa.CheckConstraint(
            "gross_margin_estimate BETWEEN 0 AND 1",
            name=op.f("ck_product_evaluations_gross_margin_range"),
        ),
        sa.CheckConstraint(
            "evaluation_score BETWEEN 0 AND 100",
            name=op.f("ck_product_evaluations_evaluation_score_range"),
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["product_candidate_id"], ["product_candidates.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_candidate_id"),
    )
    index("product_evaluations", "organization_id")
    index("product_evaluations", "product_candidate_id")

    op.create_table(
        "product_candidate_evidence",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("product_candidate_id", sa.Uuid(), nullable=False),
        sa.Column("evidence_source", sa.String(50), nullable=False),
        sa.Column("source_reference", sa.String(500), nullable=False),
        sa.Column("evidence_summary", sa.Text(), nullable=False),
        sa.Column("relevance", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        *common(),
        sa.CheckConstraint(
            "confidence BETWEEN 0 AND 1",
            name=op.f("ck_product_candidate_evidence_confidence_range"),
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["product_candidate_id"], ["product_candidates.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_candidate_id", "evidence_source", "source_reference"),
    )
    index("product_candidate_evidence", "organization_id")
    index("product_candidate_evidence", "product_candidate_id")

    if op.get_context().dialect.name == "postgresql":
        op.execute(
            """
            CREATE FUNCTION prevent_product_candidate_evidence_mutation() RETURNS trigger AS $$
            BEGIN RAISE EXCEPTION 'Product candidate evidence is append-only'; END;
            $$ LANGUAGE plpgsql;
            CREATE TRIGGER product_candidate_evidence_append_only
            BEFORE UPDATE OR DELETE ON product_candidate_evidence
            FOR EACH ROW EXECUTE FUNCTION prevent_product_candidate_evidence_mutation();
            """
        )


def downgrade() -> None:
    if op.get_context().dialect.name == "postgresql":
        op.execute(
            "DROP TRIGGER IF EXISTS product_candidate_evidence_append_only "
            "ON product_candidate_evidence"
        )
        op.execute("DROP FUNCTION IF EXISTS prevent_product_candidate_evidence_mutation()")
    for table, columns in [
        ("product_candidate_evidence", ["product_candidate_id", "organization_id"]),
        ("product_evaluations", ["product_candidate_id", "organization_id"]),
    ]:
        for column in columns:
            op.drop_index(op.f(f"ix_{table}_{column}"), table_name=table)
        op.drop_table(table)
    op.drop_index(
        op.f("ix_product_candidates_opportunity_candidate_id"),
        table_name="product_candidates",
    )
    with op.batch_alter_table("product_candidates") as batch:
        batch.drop_constraint(
            op.f("fk_product_candidates_opportunity_candidate_id_opportunity_discovery_candidates"),
            type_="foreignkey",
        )
        for column in [
            "confidence_score",
            "value_proposition",
            "product_description",
            "target_customer",
            "opportunity_candidate_id",
        ]:
            batch.drop_column(column)
        batch.alter_column("opportunity_id", nullable=False)
