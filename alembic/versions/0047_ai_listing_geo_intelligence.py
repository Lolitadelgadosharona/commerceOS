"""AI listing and GEO content intelligence foundation.

Revision ID: 0047_ai_listing_geo_intel
Revises: 0046_creative_intelligence
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0047_ai_listing_geo_intel"
down_revision: str | None = "0046_creative_intelligence"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _common() -> list[sa.Column]:
    return [
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "listing_intelligence_runs",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid()),
        sa.Column("opportunity_candidate_id", sa.Uuid()),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("template_type", sa.String(60), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("capability_id", sa.Uuid(), nullable=False),
        sa.Column("prompt_version_id", sa.Uuid()),
        sa.Column("ai_request_id", sa.Uuid()),
        sa.Column("methodology_version", sa.String(80), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("failure_reason", sa.Text()),
        *_common(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(
            ["opportunity_candidate_id"], ["opportunity_discovery_candidates.id"]
        ),
        sa.ForeignKeyConstraint(["capability_id"], ["ai_model_capabilities.id"]),
        sa.ForeignKeyConstraint(["prompt_version_id"], ["prompt_versions.id"]),
        sa.ForeignKeyConstraint(["ai_request_id"], ["ai_requests.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for c in [
        "organization_id",
        "product_id",
        "opportunity_candidate_id",
        "capability_id",
        "prompt_version_id",
        "ai_request_id",
        "created_by",
    ]:
        op.create_index(op.f(f"ix_listing_intelligence_runs_{c}"), "listing_intelligence_runs", [c])
    op.create_table(
        "listing_intelligence_evidence",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("listing_run_id", sa.Uuid(), nullable=False),
        sa.Column("evidence_type", sa.String(40), nullable=False),
        sa.Column("evidence_id", sa.Uuid(), nullable=False),
        sa.Column("source_reference", sa.String(500), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        *_common(),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="listing_intel_evidence_conf"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["listing_run_id"], ["listing_intelligence_runs.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("listing_run_id", "evidence_type", "evidence_id"),
    )
    for c in ["organization_id", "listing_run_id", "evidence_id"]:
        op.create_index(
            op.f(f"ix_listing_intelligence_evidence_{c}"), "listing_intelligence_evidence", [c]
        )
    op.create_table(
        "listing_strategy_recommendations",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("listing_run_id", sa.Uuid(), nullable=False),
        sa.Column("customer_segment", sa.Text(), nullable=False),
        sa.Column("primary_problem", sa.Text(), nullable=False),
        sa.Column("positioning", sa.Text(), nullable=False),
        sa.Column("unique_value", sa.Text(), nullable=False),
        sa.Column("benefits", sa.JSON(), nullable=False),
        sa.Column("feature_translation", sa.JSON(), nullable=False),
        sa.Column("trust_elements", sa.JSON(), nullable=False),
        sa.Column("objections", sa.JSON(), nullable=False),
        sa.Column("competitive_difference", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("evidence_refs", sa.JSON(), nullable=False),
        *_common(),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="listing_strategy_rec_conf"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["listing_run_id"], ["listing_intelligence_runs.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("listing_run_id"),
    )
    for c in ["organization_id", "listing_run_id"]:
        op.create_index(
            op.f(f"ix_listing_strategy_recommendations_{c}"),
            "listing_strategy_recommendations",
            [c],
        )
    op.create_table(
        "geo_content_recommendations",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("listing_run_id", sa.Uuid(), nullable=False),
        sa.Column("entity_description", sa.Text(), nullable=False),
        sa.Column("important_attributes", sa.JSON(), nullable=False),
        sa.Column("customer_questions", sa.JSON(), nullable=False),
        sa.Column("answer_strategy", sa.Text(), nullable=False),
        sa.Column("comparison_topics", sa.JSON(), nullable=False),
        sa.Column("expert_topics", sa.JSON(), nullable=False),
        sa.Column("citation_targets", sa.JSON(), nullable=False),
        sa.Column("missing_information", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        *_common(),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="geo_content_rec_conf"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["listing_run_id"], ["listing_intelligence_runs.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("listing_run_id"),
    )
    for c in ["organization_id", "listing_run_id"]:
        op.create_index(
            op.f(f"ix_geo_content_recommendations_{c}"), "geo_content_recommendations", [c]
        )
    op.create_table(
        "faq_recommendations",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("listing_run_id", sa.Uuid(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("customer_intent", sa.String(40), nullable=False),
        sa.Column("answer_outline", sa.Text(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("risk", sa.Text(), nullable=False),
        *_common(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["listing_run_id"], ["listing_intelligence_runs.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    for c in ["organization_id", "listing_run_id"]:
        op.create_index(op.f(f"ix_faq_recommendations_{c}"), "faq_recommendations", [c])


def downgrade() -> None:
    for table, cols in [
        ("faq_recommendations", ["listing_run_id", "organization_id"]),
        ("geo_content_recommendations", ["listing_run_id", "organization_id"]),
        ("listing_strategy_recommendations", ["listing_run_id", "organization_id"]),
        ("listing_intelligence_evidence", ["evidence_id", "listing_run_id", "organization_id"]),
        (
            "listing_intelligence_runs",
            [
                "created_by",
                "ai_request_id",
                "prompt_version_id",
                "capability_id",
                "opportunity_candidate_id",
                "product_id",
                "organization_id",
            ],
        ),
    ]:
        for c in cols:
            op.drop_index(op.f(f"ix_{table}_{c}"), table_name=table)
        op.drop_table(table)
