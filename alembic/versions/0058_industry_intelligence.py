"""Industry intelligence and AI growth service foundation.

Revision ID: 0058_industry_intelligence
Revises: 0057_growthos_revenue_v2
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0058_industry_intelligence"
down_revision: str | None = "0057_growthos_revenue_v2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def common() -> list[sa.Column]:
    return [
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
    ]


def indexes(table: str, columns: list[str]) -> None:
    for column in columns:
        op.create_index(op.f(f"ix_{table}_{column}"), table, [column])


def upgrade() -> None:
    op.create_table(
        "industry_growth_profiles",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("industry_key", sa.String(120), nullable=False),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("vertical", sa.String(120), nullable=False),
        sa.Column("scope_notes", sa.Text(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        *common(),
        sa.CheckConstraint(
            "confidence BETWEEN 0 AND 1",
            name=op.f("ck_industry_growth_profiles_industry_profile_confidence_range"),
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "industry_key"),
    )
    indexes("industry_growth_profiles", ["organization_id"])

    op.create_table(
        "industry_growth_evidence",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("industry_profile_id", sa.Uuid(), nullable=False),
        sa.Column("evidence_type", sa.String(80), nullable=False),
        sa.Column("source_reference", sa.String(1000), nullable=False),
        sa.Column("observation", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        *common(),
        sa.CheckConstraint(
            "confidence BETWEEN 0 AND 1",
            name=op.f("ck_industry_growth_evidence_industry_evidence_confidence_range"),
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["industry_profile_id"], ["industry_growth_profiles.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes("industry_growth_evidence", ["organization_id", "industry_profile_id"])

    op.create_table(
        "industry_growth_patterns",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("industry_profile_id", sa.Uuid(), nullable=False),
        sa.Column("pattern_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(250), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("evidence_references", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        *common(),
        sa.CheckConstraint(
            "confidence BETWEEN 0 AND 1",
            name=op.f("ck_industry_growth_patterns_industry_pattern_confidence_range"),
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["industry_profile_id"], ["industry_growth_profiles.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes("industry_growth_patterns", ["organization_id", "industry_profile_id"])

    op.create_table(
        "growth_geo_assessments",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("prospect_id", sa.Uuid(), nullable=False),
        sa.Column("industry_profile_id", sa.Uuid()),
        sa.Column("website_signals", sa.JSON(), nullable=False),
        sa.Column("social_signals", sa.JSON(), nullable=False),
        sa.Column("review_signals", sa.JSON(), nullable=False),
        sa.Column("visibility_gaps", sa.JSON(), nullable=False),
        sa.Column("recommendations", sa.JSON(), nullable=False),
        sa.Column("evidence_references", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        *common(),
        sa.CheckConstraint(
            "confidence BETWEEN 0 AND 1",
            name=op.f("ck_growth_geo_assessments_growth_geo_confidence_range"),
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["prospect_id"], ["growth_prospects.id"]),
        sa.ForeignKeyConstraint(["industry_profile_id"], ["industry_growth_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("prospect_id"),
    )
    indexes("growth_geo_assessments", ["organization_id", "prospect_id", "industry_profile_id"])

    op.create_table(
        "growth_service_recommendations",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("prospect_id", sa.Uuid(), nullable=False),
        sa.Column("industry_profile_id", sa.Uuid()),
        sa.Column("opportunity_id", sa.Uuid()),
        sa.Column("service_type", sa.String(50), nullable=False),
        sa.Column("customer_problem", sa.Text(), nullable=False),
        sa.Column("recommended_scope", sa.Text(), nullable=False),
        sa.Column("expected_value", sa.Text(), nullable=False),
        sa.Column("purchase_probability", sa.Float()),
        sa.Column("quick_win_potential", sa.String(20), nullable=False),
        sa.Column("evidence_references", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        *common(),
        sa.CheckConstraint(
            "confidence BETWEEN 0 AND 1",
            name=op.f("ck_growth_service_recommendations_confidence_range"),
        ),
        sa.CheckConstraint(
            "purchase_probability IS NULL OR purchase_probability BETWEEN 0 AND 1",
            name=op.f("ck_growth_service_recommendations_purchase_probability_range"),
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["prospect_id"], ["growth_prospects.id"]),
        sa.ForeignKeyConstraint(["industry_profile_id"], ["industry_growth_profiles.id"]),
        sa.ForeignKeyConstraint(["opportunity_id"], ["growth_opportunity_analyses.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes(
        "growth_service_recommendations",
        ["organization_id", "prospect_id", "industry_profile_id", "opportunity_id"],
    )

    op.create_table(
        "industry_learning_signals",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("industry_profile_id", sa.Uuid(), nullable=False),
        sa.Column("source_type", sa.String(80), nullable=False),
        sa.Column("source_reference", sa.String(500), nullable=False),
        sa.Column("pattern_type", sa.String(50), nullable=False),
        sa.Column("observation", sa.Text(), nullable=False),
        sa.Column("evidence_references", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        *common(),
        sa.CheckConstraint(
            "confidence BETWEEN 0 AND 1",
            name=op.f("ck_industry_learning_signals_industry_learning_confidence_range"),
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["industry_profile_id"], ["industry_growth_profiles.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes("industry_learning_signals", ["organization_id", "industry_profile_id"])


def downgrade() -> None:
    for table, columns in [
        ("industry_learning_signals", ["industry_profile_id", "organization_id"]),
        (
            "growth_service_recommendations",
            ["opportunity_id", "industry_profile_id", "prospect_id", "organization_id"],
        ),
        ("growth_geo_assessments", ["industry_profile_id", "prospect_id", "organization_id"]),
        ("industry_growth_patterns", ["industry_profile_id", "organization_id"]),
        ("industry_growth_evidence", ["industry_profile_id", "organization_id"]),
        ("industry_growth_profiles", ["organization_id"]),
    ]:
        for column in columns:
            op.drop_index(op.f(f"ix_{table}_{column}"), table_name=table)
        op.drop_table(table)
