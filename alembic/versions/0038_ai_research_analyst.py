"""AI research analyst foundation.

Revision ID: 0038_ai_research
Revises: 0037_marketplace_voice
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0038_ai_research"
down_revision: str | None = "0037_marketplace_voice"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def common_columns() -> list[sa.Column]:
    return [
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "research_analyses",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("ai_request_id", sa.Uuid(), nullable=False),
        sa.Column("analysis_type", sa.String(60), nullable=False),
        sa.Column("output_classification", sa.String(30), nullable=False),
        sa.Column("output_summary", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("methodology_version", sa.String(80), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("reviewed_by", sa.Uuid(), nullable=True),
        *common_columns(),
        sa.CheckConstraint(
            "confidence BETWEEN 0 AND 1", name=op.f("ck_research_analyses_confidence_range")
        ),
        sa.ForeignKeyConstraint(
            ["ai_request_id"],
            ["ai_requests.id"],
            name=op.f("fk_research_analyses_ai_request_id_ai_requests"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_research_analyses_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by"], ["users.id"], name=op.f("fk_research_analyses_reviewed_by_users")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_research_analyses")),
    )
    for column in ("organization_id", "ai_request_id", "reviewed_by"):
        op.create_index(op.f(f"ix_research_analyses_{column}"), "research_analyses", [column])

    op.create_table(
        "research_evidence_citations",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("analysis_id", sa.Uuid(), nullable=False),
        sa.Column("evidence_type", sa.String(50), nullable=False),
        sa.Column("evidence_id", sa.Uuid(), nullable=False),
        sa.Column("source_reference", sa.String(500), nullable=False),
        sa.Column("citation_note", sa.Text(), nullable=False),
        sa.Column("relevance_score", sa.Float(), nullable=False),
        *common_columns(),
        sa.CheckConstraint(
            "relevance_score BETWEEN 0 AND 1",
            name=op.f("ck_research_evidence_citations_relevance_score_range"),
        ),
        sa.ForeignKeyConstraint(
            ["analysis_id"],
            ["research_analyses.id"],
            ondelete="CASCADE",
            name=op.f("fk_research_evidence_citations_analysis_id_research_analyses"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_research_evidence_citations_organization_id_organizations"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_research_evidence_citations")),
        sa.UniqueConstraint(
            "analysis_id", "evidence_type", "evidence_id", name="uq_research_citation_evidence"
        ),
    )
    for column in ("organization_id", "analysis_id", "evidence_id"):
        op.create_index(
            op.f(f"ix_research_evidence_citations_{column}"),
            "research_evidence_citations",
            [column],
        )

    op.create_table(
        "customer_pain_research",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("analysis_id", sa.Uuid(), nullable=False),
        sa.Column("pain_patterns", sa.JSON(), nullable=False),
        sa.Column("customer_needs", sa.JSON(), nullable=False),
        sa.Column("objections", sa.JSON(), nullable=False),
        sa.Column("motivations", sa.JSON(), nullable=False),
        sa.Column("language_themes", sa.JSON(), nullable=False),
        *common_columns(),
        sa.ForeignKeyConstraint(
            ["analysis_id"],
            ["research_analyses.id"],
            name=op.f("fk_customer_pain_research_analysis_id_research_analyses"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_customer_pain_research_organization_id_organizations"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_customer_pain_research")),
        sa.UniqueConstraint("analysis_id", name=op.f("uq_customer_pain_research_analysis_id")),
    )
    op.create_index(
        op.f("ix_customer_pain_research_organization_id"),
        "customer_pain_research",
        ["organization_id"],
    )
    op.create_index(
        op.f("ix_customer_pain_research_analysis_id"), "customer_pain_research", ["analysis_id"]
    )

    op.create_table(
        "market_insight_research",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("analysis_id", sa.Uuid(), nullable=False),
        sa.Column("market_trends", sa.JSON(), nullable=False),
        sa.Column("emerging_signals", sa.JSON(), nullable=False),
        sa.Column("competitive_observations", sa.JSON(), nullable=False),
        sa.Column("opportunity_indicators", sa.JSON(), nullable=False),
        *common_columns(),
        sa.ForeignKeyConstraint(
            ["analysis_id"],
            ["research_analyses.id"],
            name=op.f("fk_market_insight_research_analysis_id_research_analyses"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_market_insight_research_organization_id_organizations"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_market_insight_research")),
        sa.UniqueConstraint("analysis_id", name=op.f("uq_market_insight_research_analysis_id")),
    )
    op.create_index(
        op.f("ix_market_insight_research_organization_id"),
        "market_insight_research",
        ["organization_id"],
    )
    op.create_index(
        op.f("ix_market_insight_research_analysis_id"), "market_insight_research", ["analysis_id"]
    )

    op.create_table(
        "opportunity_research_briefs",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("analysis_id", sa.Uuid(), nullable=False),
        sa.Column("opportunity_id", sa.Uuid(), nullable=False),
        sa.Column("opportunity_summary", sa.Text(), nullable=False),
        sa.Column("customer_problem", sa.Text(), nullable=False),
        sa.Column("market_context", sa.Text(), nullable=False),
        sa.Column("competition", sa.Text(), nullable=False),
        sa.Column("risks", sa.JSON(), nullable=False),
        sa.Column("economics_references", sa.JSON(), nullable=False),
        sa.Column("missing_information", sa.JSON(), nullable=False),
        *common_columns(),
        sa.ForeignKeyConstraint(
            ["analysis_id"],
            ["research_analyses.id"],
            name=op.f("fk_opportunity_research_briefs_analysis_id_research_analyses"),
        ),
        sa.ForeignKeyConstraint(
            ["opportunity_id"],
            ["market_opportunities.id"],
            name=op.f("fk_opportunity_research_briefs_opportunity_id_market_opportunities"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_opportunity_research_briefs_organization_id_organizations"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_opportunity_research_briefs")),
        sa.UniqueConstraint("analysis_id", name=op.f("uq_opportunity_research_briefs_analysis_id")),
    )
    for column in ("organization_id", "analysis_id", "opportunity_id"):
        op.create_index(
            op.f(f"ix_opportunity_research_briefs_{column}"),
            "opportunity_research_briefs",
            [column],
        )


def downgrade() -> None:
    op.drop_table("opportunity_research_briefs")
    op.drop_table("market_insight_research")
    op.drop_table("customer_pain_research")
    op.drop_table("research_evidence_citations")
    op.drop_table("research_analyses")
