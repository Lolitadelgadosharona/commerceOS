"""AI discovery listing intelligence foundation."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0026_ai_discovery_listing"
down_revision: str | None = "0025_launch_preparation"
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
        sa.Column("product_id", uuid, nullable=False),
    ]


def constraints() -> list[sa.Constraint]:
    return [
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    ]


def indexes(table: str) -> None:
    op.create_index(f"ix_{table}_organization_id", table, ["organization_id"])
    op.create_index(f"ix_{table}_product_id", table, ["product_id"])


def upgrade() -> None:
    op.create_table(
        "listing_blueprints",
        *common(),
        sa.Column("title_strategy", sa.Text(), nullable=False),
        sa.Column("benefit_structure", sa.JSON(), nullable=False),
        sa.Column("feature_structure", sa.JSON(), nullable=False),
        sa.Column("faq_structure", sa.JSON(), nullable=False),
        sa.Column("trust_elements", sa.JSON(), nullable=False),
        sa.Column("comparison_points", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),
        *constraints(),
    )
    indexes("listing_blueprints")
    op.create_table(
        "geo_knowledge_assets",
        *common(),
        sa.Column("entity_description", sa.Text(), nullable=False),
        sa.Column("attributes", sa.JSON(), nullable=False),
        sa.Column("use_cases", sa.JSON(), nullable=False),
        sa.Column("customer_questions", sa.JSON(), nullable=False),
        sa.Column("answer_structure", sa.JSON(), nullable=False),
        sa.Column("evidence_reference", sa.String(500), nullable=False),
        *constraints(),
    )
    indexes("geo_knowledge_assets")
    score_fields = (
        "truth_score",
        "customer_language_score",
        "geo_score",
        "trust_score",
        "conversion_score",
        "overall_score",
    )
    checks = {
        "truth_score": "truth_range",
        "customer_language_score": "language_range",
        "geo_score": "geo_range",
        "trust_score": "trust_range",
        "conversion_score": "conversion_range",
        "overall_score": "overall_range",
    }
    op.create_table(
        "listing_quality_assessments",
        *common(),
        *(sa.Column(field, sa.Float(), nullable=False) for field in score_fields),
        *(
            sa.CheckConstraint(f"{field} BETWEEN 0 AND 100", name=name)
            for field, name in checks.items()
        ),
        *constraints(),
    )
    indexes("listing_quality_assessments")
    op.create_table(
        "ai_discovery_readiness_assessments",
        *common(),
        sa.Column("coverage_score", sa.Float(), nullable=False),
        sa.Column("missing_information", sa.JSON(), nullable=False),
        sa.Column("recommendation", sa.Text(), nullable=False),
        sa.CheckConstraint("coverage_score BETWEEN 0 AND 100", name="coverage_range"),
        *constraints(),
    )
    indexes("ai_discovery_readiness_assessments")


def downgrade() -> None:
    for table in (
        "ai_discovery_readiness_assessments",
        "listing_quality_assessments",
        "geo_knowledge_assets",
        "listing_blueprints",
    ):
        op.drop_table(table)
