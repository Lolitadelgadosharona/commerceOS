"""AI creative production intelligence foundation.

Revision ID: 0046_creative_intelligence
Revises: 0045_ai_opportunity_discovery
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0046_creative_intelligence"
down_revision: str | None = "0045_ai_opportunity_discovery"
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
        "creative_intelligence_runs",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("opportunity_candidate_id", sa.Uuid()),
        sa.Column("product_id", sa.Uuid()),
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
        sa.ForeignKeyConstraint(
            ["opportunity_candidate_id"], ["opportunity_discovery_candidates.id"]
        ),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["capability_id"], ["ai_model_capabilities.id"]),
        sa.ForeignKeyConstraint(["prompt_version_id"], ["prompt_versions.id"]),
        sa.ForeignKeyConstraint(["ai_request_id"], ["ai_requests.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for c in [
        "organization_id",
        "opportunity_candidate_id",
        "product_id",
        "capability_id",
        "prompt_version_id",
        "ai_request_id",
        "created_by",
    ]:
        op.create_index(
            op.f(f"ix_creative_intelligence_runs_{c}"), "creative_intelligence_runs", [c]
        )
    op.create_table(
        "creative_intelligence_evidence",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("creative_run_id", sa.Uuid(), nullable=False),
        sa.Column("evidence_type", sa.String(40), nullable=False),
        sa.Column("evidence_id", sa.Uuid(), nullable=False),
        sa.Column("source_reference", sa.String(500), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        *_common(),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="creative_intel_evidence_conf"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["creative_run_id"], ["creative_intelligence_runs.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("creative_run_id", "evidence_type", "evidence_id"),
    )
    for c in ["organization_id", "creative_run_id", "evidence_id"]:
        op.create_index(
            op.f(f"ix_creative_intelligence_evidence_{c}"), "creative_intelligence_evidence", [c]
        )
    op.create_table(
        "creative_strategy_recommendations",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("creative_run_id", sa.Uuid(), nullable=False),
        sa.Column("target_customer", sa.Text(), nullable=False),
        sa.Column("customer_problem", sa.Text(), nullable=False),
        sa.Column("core_message", sa.Text(), nullable=False),
        sa.Column("value_proposition", sa.Text(), nullable=False),
        sa.Column("emotional_angle", sa.Text(), nullable=False),
        sa.Column("rational_angle", sa.Text(), nullable=False),
        sa.Column("trust_elements", sa.JSON(), nullable=False),
        sa.Column("objections", sa.JSON(), nullable=False),
        sa.Column("channel_recommendations", sa.JSON(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("risks", sa.JSON(), nullable=False),
        sa.Column("estimated_impact", sa.Text()),
        sa.Column("output_type", sa.String(20), nullable=False),
        *_common(),
        sa.CheckConstraint("confidence_score BETWEEN 0 AND 1", name="creative_strategy_rec_conf"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["creative_run_id"], ["creative_intelligence_runs.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("creative_run_id"),
    )
    for c in ["organization_id", "creative_run_id"]:
        op.create_index(
            op.f(f"ix_creative_strategy_recommendations_{c}"),
            "creative_strategy_recommendations",
            [c],
        )
    op.create_table(
        "creative_angles",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("creative_run_id", sa.Uuid(), nullable=False),
        sa.Column("angle_type", sa.String(40), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("evidence_references", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("source", sa.String(100), nullable=False),
        *_common(),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="creative_angle_conf"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["creative_run_id"], ["creative_intelligence_runs.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    for c in ["organization_id", "creative_run_id"]:
        op.create_index(op.f(f"ix_creative_angles_{c}"), "creative_angles", [c])
    op.create_table(
        "creative_brief_recommendations",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("creative_run_id", sa.Uuid(), nullable=False),
        sa.Column("hook", sa.Text(), nullable=False),
        sa.Column("problem", sa.Text(), nullable=False),
        sa.Column("solution", sa.Text(), nullable=False),
        sa.Column("proof", sa.JSON(), nullable=False),
        sa.Column("cta", sa.Text(), nullable=False),
        sa.Column("visual_direction", sa.Text(), nullable=False),
        sa.Column("video_concept", sa.Text(), nullable=False),
        sa.Column("image_concept", sa.Text(), nullable=False),
        sa.Column("ugc_concept", sa.Text(), nullable=False),
        sa.Column("audience", sa.Text(), nullable=False),
        sa.Column("channel", sa.String(40), nullable=False),
        sa.Column("evidence_references", sa.JSON(), nullable=False),
        *_common(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["creative_run_id"], ["creative_intelligence_runs.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("creative_run_id"),
    )
    for c in ["organization_id", "creative_run_id"]:
        op.create_index(
            op.f(f"ix_creative_brief_recommendations_{c}"), "creative_brief_recommendations", [c]
        )


def downgrade() -> None:
    for table, cols in [
        ("creative_brief_recommendations", ["creative_run_id", "organization_id"]),
        ("creative_angles", ["creative_run_id", "organization_id"]),
        ("creative_strategy_recommendations", ["creative_run_id", "organization_id"]),
        ("creative_intelligence_evidence", ["evidence_id", "creative_run_id", "organization_id"]),
        (
            "creative_intelligence_runs",
            [
                "created_by",
                "ai_request_id",
                "prompt_version_id",
                "capability_id",
                "product_id",
                "opportunity_candidate_id",
                "organization_id",
            ],
        ),
    ]:
        for c in cols:
            op.drop_index(op.f(f"ix_{table}_{c}"), table_name=table)
        op.drop_table(table)
