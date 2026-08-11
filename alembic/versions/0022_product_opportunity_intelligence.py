"""Customer need to product opportunity foundation."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0022_product_opportunity"
down_revision: str | None = "0021_customer_voice"
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


def org() -> sa.ForeignKeyConstraint:
    return sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"])


def idx(table: str, refs: tuple[str, ...] = ()) -> None:
    op.create_index(f"ix_{table}_organization_id", table, ["organization_id"])
    for ref in refs:
        op.create_index(f"ix_{table}_{ref}", table, [ref])


def upgrade() -> None:
    op.create_table(
        "customer_needs",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(80), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.CheckConstraint("confidence_score BETWEEN 0 AND 1", name="confidence_range"),
        org(),
        sa.PrimaryKeyConstraint("id"),
    )
    idx("customer_needs")
    op.create_table(
        "pain_need_mappings",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("pain_cluster_id", uuid, nullable=False),
        sa.Column("need_id", uuid, nullable=False),
        sa.Column("mapping_strength", sa.Float(), nullable=False),
        sa.Column("evidence_count", sa.Integer(), nullable=False),
        sa.CheckConstraint("mapping_strength BETWEEN 0 AND 1", name="mapping_strength_range"),
        org(),
        sa.ForeignKeyConstraint(
            ["pain_cluster_id"], ["customer_pain_clusters.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["need_id"], ["customer_needs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    idx("pain_need_mappings", ("pain_cluster_id", "need_id"))
    op.create_table(
        "product_solution_hypotheses",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("need_id", uuid, nullable=False),
        sa.Column("product_category", sa.String(120), nullable=False),
        sa.Column("solution_description", sa.Text(), nullable=False),
        sa.Column("fit_score", sa.Float(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.CheckConstraint("fit_score BETWEEN 0 AND 100", name="fit_range"),
        sa.CheckConstraint("confidence_score BETWEEN 0 AND 1", name="confidence_range"),
        org(),
        sa.ForeignKeyConstraint(["need_id"], ["customer_needs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    idx("product_solution_hypotheses", ("need_id",))
    columns = [
        sa.Column(name, sa.Float(), nullable=False)
        for name in (
            "pain_strength",
            "solution_fit",
            "intent_score",
            "competition_score",
            "margin_score",
            "risk_score",
            "overall_score",
        )
    ]
    checks = [
        sa.CheckConstraint(f"{field} BETWEEN 0 AND 100", name=name)
        for field, name in {
            "pain_strength": "pain_range",
            "solution_fit": "fit_range",
            "intent_score": "intent_range",
            "competition_score": "competition_range",
            "margin_score": "margin_range",
            "risk_score": "risk_range",
            "overall_score": "overall_range",
        }.items()
    ]
    op.create_table(
        "customer_backed_opportunity_assessments",
        *common(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("opportunity_id", uuid, nullable=False),
        sa.Column("need_id", uuid, nullable=False),
        *columns,
        sa.Column("formula_version", sa.String(40), nullable=False),
        *checks,
        org(),
        sa.ForeignKeyConstraint(
            ["opportunity_id"], ["market_opportunities.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["need_id"], ["customer_needs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    idx("customer_backed_opportunity_assessments", ("opportunity_id", "need_id"))


def downgrade() -> None:
    for table in (
        "customer_backed_opportunity_assessments",
        "product_solution_hypotheses",
        "pain_need_mappings",
        "customer_needs",
    ):
        op.drop_table(table)
