"""Opportunity intelligence foundation.

Revision ID: 0004_opportunity_intelligence
Revises: 0003_customer_intelligence
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004_opportunity_intelligence"
down_revision: str | None = "0003_customer_intelligence"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

uuid = sa.Uuid()


def timestamps() -> list[sa.Column]:
    return [
        sa.Column("id", uuid, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
    ]


def score_constraint(column: str, name: str) -> sa.CheckConstraint:
    return sa.CheckConstraint(f"{column} >= 0 AND {column} <= 100", name=name)


def upgrade() -> None:
    op.create_table(
        "market_opportunities",
        *timestamps(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("title", sa.String(250), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(150), nullable=False),
        sa.Column("market", sa.String(150), nullable=False),
        sa.Column("geography", sa.String(150), nullable=False),
        sa.Column("trigger_type", sa.String(50), nullable=False),
        sa.Column("timing_window", sa.String(200), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.CheckConstraint(
            "confidence_score >= 0 AND confidence_score <= 1", name="confidence_range"
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_market_opportunities_organization_id",
        "market_opportunities",
        ["organization_id"],
    )
    op.create_index(
        "ix_market_opportunities_status",
        "market_opportunities",
        ["organization_id", "status", "created_at"],
    )
    op.create_table(
        "opportunity_evidence",
        *timestamps(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("opportunity_id", uuid, nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("source_reference", sa.String(500), nullable=False),
        sa.Column("evidence_summary", sa.Text(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.CheckConstraint(
            "confidence_score >= 0 AND confidence_score <= 1", name="confidence_range"
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["opportunity_id"], ["market_opportunities.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("opportunity_id", "source_type", "source_reference"),
    )
    op.create_index(
        "ix_opportunity_evidence_opportunity_id", "opportunity_evidence", ["opportunity_id"]
    )
    op.create_index(
        "ix_opportunity_evidence_organization_id", "opportunity_evidence", ["organization_id"]
    )
    op.create_table(
        "product_candidates",
        *timestamps(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("opportunity_id", uuid, nullable=False),
        sa.Column("product_name", sa.String(250), nullable=False),
        sa.Column("category", sa.String(150), nullable=False),
        sa.Column("customer_need", sa.Text(), nullable=False),
        sa.Column("estimated_margin", sa.Float(), nullable=False),
        sa.Column("risk_level", sa.String(30), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.CheckConstraint("estimated_margin >= 0 AND estimated_margin <= 1", name="margin_range"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["opportunity_id"], ["market_opportunities.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_product_candidates_opportunity_id", "product_candidates", ["opportunity_id"]
    )
    op.create_index(
        "ix_product_candidates_organization_id", "product_candidates", ["organization_id"]
    )
    op.create_table(
        "opportunity_scores",
        *timestamps(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("opportunity_id", uuid, nullable=False),
        sa.Column("demand_score", sa.Float(), nullable=False),
        sa.Column("pain_score", sa.Float(), nullable=False),
        sa.Column("trend_score", sa.Float(), nullable=False),
        sa.Column("margin_score", sa.Float(), nullable=False),
        sa.Column("competition_score", sa.Float(), nullable=False),
        sa.Column("ip_risk_score", sa.Float(), nullable=False),
        sa.Column("dispute_risk_score", sa.Float(), nullable=False),
        sa.Column("overall_score", sa.Float(), nullable=False),
        sa.Column("formula_version", sa.String(30), nullable=False),
        score_constraint("demand_score", "demand_range"),
        score_constraint("pain_score", "pain_range"),
        score_constraint("trend_score", "trend_range"),
        score_constraint("margin_score", "margin_range"),
        score_constraint("competition_score", "competition_range"),
        score_constraint("ip_risk_score", "ip_risk_range"),
        score_constraint("dispute_risk_score", "dispute_risk_range"),
        score_constraint("overall_score", "overall_range"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["opportunity_id"], ["market_opportunities.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("opportunity_id"),
    )
    op.create_index(
        "ix_opportunity_scores_opportunity_id", "opportunity_scores", ["opportunity_id"]
    )
    op.create_index(
        "ix_opportunity_scores_organization_id", "opportunity_scores", ["organization_id"]
    )
    op.create_table(
        "opportunity_risks",
        *timestamps(),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("opportunity_id", uuid, nullable=False),
        sa.Column("risk_type", sa.String(30), nullable=False),
        sa.Column("severity", sa.String(30), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["opportunity_id"], ["market_opportunities.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_opportunity_risks_opportunity_id", "opportunity_risks", ["opportunity_id"])
    op.create_index(
        "ix_opportunity_risks_organization_id", "opportunity_risks", ["organization_id"]
    )


def downgrade() -> None:
    for table in (
        "opportunity_risks",
        "opportunity_scores",
        "product_candidates",
        "opportunity_evidence",
        "market_opportunities",
    ):
        op.drop_table(table)
