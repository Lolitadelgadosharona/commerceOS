"""Creative AI production foundation.

Revision ID: 0039_creative_production
Revises: 0038_ai_research
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0039_creative_production"
down_revision: str | None = "0038_ai_research"
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
        "creative_production_requests",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("creative_brief_id", sa.Uuid(), nullable=False),
        sa.Column("format", sa.String(30), nullable=False),
        sa.Column("channel", sa.String(50), nullable=False),
        sa.Column("audience", sa.Text(), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("requested_by", sa.Uuid(), nullable=False),
        sa.Column("approval_state", sa.String(20), nullable=False),
        sa.Column("approval_request_id", sa.Uuid(), nullable=True),
        *common_columns(),
        sa.ForeignKeyConstraint(
            ["approval_request_id"],
            ["approval_requests.id"],
            name=op.f("fk_creative_production_requests_approval_request_id_approval_requests"),
        ),
        sa.ForeignKeyConstraint(
            ["creative_brief_id"],
            ["creative_briefs.id"],
            name=op.f("fk_creative_production_requests_creative_brief_id_creative_briefs"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_creative_production_requests_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name=op.f("fk_creative_production_requests_project_id_projects"),
        ),
        sa.ForeignKeyConstraint(
            ["requested_by"],
            ["users.id"],
            name=op.f("fk_creative_production_requests_requested_by_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_creative_production_requests")),
    )
    for column in (
        "organization_id",
        "project_id",
        "creative_brief_id",
        "requested_by",
        "approval_request_id",
    ):
        op.create_index(
            op.f(f"ix_creative_production_requests_{column}"),
            "creative_production_requests",
            [column],
        )

    op.create_table(
        "creative_production_work",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("production_request_id", sa.Uuid(), nullable=False),
        sa.Column("work_type", sa.String(30), nullable=False),
        sa.Column("title", sa.String(250), nullable=False),
        sa.Column("content_metadata", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        *common_columns(),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_creative_production_work_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["production_request_id"],
            ["creative_production_requests.id"],
            ondelete="CASCADE",
            name=op.f(
                "fk_creative_production_work_production_request_id_creative_production_requests"
            ),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_creative_production_work")),
    )
    op.create_index(
        op.f("ix_creative_production_work_organization_id"),
        "creative_production_work",
        ["organization_id"],
    )
    op.create_index(
        op.f("ix_creative_production_work_production_request_id"),
        "creative_production_work",
        ["production_request_id"],
    )

    op.create_table(
        "creative_production_ai_provenance",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("production_request_id", sa.Uuid(), nullable=False),
        sa.Column("production_work_id", sa.Uuid(), nullable=False),
        sa.Column("ai_request_id", sa.Uuid(), nullable=False),
        sa.Column("output_classification", sa.String(30), nullable=False),
        sa.Column("output_metadata", sa.JSON(), nullable=False),
        sa.Column("provenance_note", sa.Text(), nullable=False),
        *common_columns(),
        sa.ForeignKeyConstraint(
            ["ai_request_id"],
            ["ai_requests.id"],
            name=op.f("fk_creative_production_ai_provenance_ai_request_id_ai_requests"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_creative_production_ai_provenance_organization_id_organizations"),
        ),
        sa.ForeignKeyConstraint(
            ["production_request_id"],
            ["creative_production_requests.id"],
            ondelete="CASCADE",
            name=op.f(
                "fk_creative_production_ai_provenance_production_request_id_creative_production_requests"
            ),
        ),
        sa.ForeignKeyConstraint(
            ["production_work_id"],
            ["creative_production_work.id"],
            ondelete="CASCADE",
            name=op.f(
                "fk_creative_production_ai_provenance_production_work_id_creative_production_work"
            ),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_creative_production_ai_provenance")),
        sa.UniqueConstraint(
            "production_work_id",
            "ai_request_id",
            name=op.f("uq_creative_production_ai_provenance_production_work_id"),
        ),
    )
    for column in (
        "organization_id",
        "production_request_id",
        "production_work_id",
        "ai_request_id",
    ):
        op.create_index(
            op.f(f"ix_creative_production_ai_provenance_{column}"),
            "creative_production_ai_provenance",
            [column],
        )

    with op.batch_alter_table("creative_assets") as batch:
        batch.add_column(sa.Column("production_request_id", sa.Uuid(), nullable=True))
        batch.add_column(
            sa.Column("review_status", sa.String(30), server_default="unreviewed", nullable=False)
        )
        batch.add_column(sa.Column("quality_score", sa.Float(), nullable=True))
        batch.create_foreign_key(
            op.f("fk_creative_assets_production_request_id_creative_production_requests"),
            "creative_production_requests",
            ["production_request_id"],
            ["id"],
        )
        batch.create_index(
            op.f("ix_creative_assets_production_request_id"), ["production_request_id"]
        )

    with op.batch_alter_table("creative_quality_reviews") as batch:
        for name in (
            "brand_consistency_score",
            "claim_safety_score",
            "product_accuracy_score",
            "channel_suitability_score",
            "customer_relevance_score",
        ):
            batch.add_column(sa.Column(name, sa.Float(), nullable=True))
        batch.add_column(
            sa.Column("review_status", sa.String(30), server_default="draft", nullable=False)
        )
        batch.add_column(sa.Column("reviewed_by", sa.Uuid(), nullable=True))
        batch.create_foreign_key(
            op.f("fk_creative_quality_reviews_reviewed_by_users"), "users", ["reviewed_by"], ["id"]
        )
        batch.create_index(op.f("ix_creative_quality_reviews_reviewed_by"), ["reviewed_by"])


def downgrade() -> None:
    with op.batch_alter_table("creative_quality_reviews") as batch:
        batch.drop_index(op.f("ix_creative_quality_reviews_reviewed_by"))
        batch.drop_constraint(
            op.f("fk_creative_quality_reviews_reviewed_by_users"), type_="foreignkey"
        )
        batch.drop_column("reviewed_by")
        batch.drop_column("review_status")
        batch.drop_column("customer_relevance_score")
        batch.drop_column("channel_suitability_score")
        batch.drop_column("product_accuracy_score")
        batch.drop_column("claim_safety_score")
        batch.drop_column("brand_consistency_score")
    with op.batch_alter_table("creative_assets") as batch:
        batch.drop_index(op.f("ix_creative_assets_production_request_id"))
        batch.drop_constraint(
            op.f("fk_creative_assets_production_request_id_creative_production_requests"),
            type_="foreignkey",
        )
        batch.drop_column("quality_score")
        batch.drop_column("review_status")
        batch.drop_column("production_request_id")
    op.drop_table("creative_production_ai_provenance")
    op.drop_table("creative_production_work")
    op.drop_table("creative_production_requests")
