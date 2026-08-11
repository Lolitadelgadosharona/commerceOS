"""Product commercial risk intelligence foundation."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0023_product_risk"
down_revision: str | None = "0022_product_opportunity"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None
uuid = sa.Uuid()


def common() -> list[sa.Column]:
    return [
        sa.Column("id", uuid, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("product_candidate_id", uuid, nullable=False),
    ]


def constraints() -> list[sa.Constraint]:
    return [
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["product_candidate_id"], ["product_candidates.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    ]


def indexes(table: str) -> None:
    op.create_index(f"ix_{table}_organization_id", table, ["organization_id"])
    op.create_index(f"ix_{table}_product_candidate_id", table, ["product_candidate_id"])


def upgrade() -> None:
    op.create_table(
        "product_risk_signals",
        *common(),
        sa.Column("risk_type", sa.String(40), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),
        *constraints(),
    )
    indexes("product_risk_signals")
    op.create_table(
        "product_risk_assessments",
        *common(),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("risk_level", sa.String(20), nullable=False),
        sa.Column("formula_version", sa.String(40), nullable=False),
        sa.Column("assessment_inputs", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.CheckConstraint("risk_score BETWEEN 0 AND 100", name="risk_range"),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),
        *constraints(),
    )
    indexes("product_risk_assessments")
    op.create_table(
        "commercial_viability_assessments",
        *common(),
        sa.Column("opportunity_score", sa.Float(), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("adjusted_score", sa.Float(), nullable=False),
        sa.Column("recommendation", sa.String(20), nullable=False),
        sa.Column("reasoning", sa.Text(), nullable=False),
        sa.CheckConstraint("opportunity_score BETWEEN 0 AND 100", name="opportunity_range"),
        sa.CheckConstraint("risk_score BETWEEN 0 AND 100", name="risk_range"),
        sa.CheckConstraint("adjusted_score BETWEEN 0 AND 100", name="adjusted_range"),
        *constraints(),
    )
    indexes("commercial_viability_assessments")


def downgrade() -> None:
    for table in (
        "commercial_viability_assessments",
        "product_risk_assessments",
        "product_risk_signals",
    ):
        op.drop_table(table)
