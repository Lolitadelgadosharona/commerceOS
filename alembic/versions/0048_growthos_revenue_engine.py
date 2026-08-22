"""GrowthOS revenue engine foundation.

Revision ID: 0048_growthos_revenue
Revises: 0047_ai_listing_geo_intel
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0048_growthos_revenue"
down_revision: str | None = "0047_ai_listing_geo_intel"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def common() -> list[sa.Column]:
    return [
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
    ]


def indexed(table: str, columns: list[str]) -> None:
    for column in columns:
        op.create_index(op.f(f"ix_{table}_{column}"), table, [column])


def upgrade() -> None:
    op.create_table(
        "growth_prospects",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("business_name", sa.String(250), nullable=False),
        sa.Column("website", sa.String(500)),
        sa.Column("email", sa.String(320)),
        sa.Column("social_links", sa.JSON(), nullable=False),
        sa.Column("location", sa.String(250)),
        sa.Column("industry", sa.String(120), nullable=False),
        sa.Column("business_type", sa.String(120), nullable=False),
        sa.Column("source", sa.String(120), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        *common(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "website", "business_name"),
    )
    indexed("growth_prospects", ["organization_id"])
    op.create_table(
        "growth_prospect_evidence",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("prospect_id", sa.Uuid(), nullable=False),
        sa.Column("evidence_type", sa.String(80), nullable=False),
        sa.Column("source_url", sa.String(1000)),
        sa.Column("observation", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        *common(),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="growth_evidence_confidence_range"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["prospect_id"], ["growth_prospects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    indexed("growth_prospect_evidence", ["organization_id", "prospect_id"])
    if op.get_context().dialect.name == "postgresql":
        op.execute(
            """
            CREATE FUNCTION prevent_growth_prospect_evidence_update() RETURNS trigger AS $$
            BEGIN RAISE EXCEPTION 'Growth prospect evidence is immutable'; END;
            $$ LANGUAGE plpgsql;
            CREATE TRIGGER growth_prospect_evidence_immutable
            BEFORE UPDATE ON growth_prospect_evidence
            FOR EACH ROW EXECUTE FUNCTION prevent_growth_prospect_evidence_update();
            """
        )
    op.create_table(
        "growth_opportunity_analyses",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("prospect_id", sa.Uuid(), nullable=False),
        sa.Column("opportunity_type", sa.String(50), nullable=False),
        sa.Column("problem_statement", sa.Text(), nullable=False),
        sa.Column("evidence_reference", sa.JSON(), nullable=False),
        sa.Column("customer_impact", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("recommended_offer", sa.Text(), nullable=False),
        sa.Column("risks", sa.JSON(), nullable=False),
        sa.Column("missing_information", sa.JSON(), nullable=False),
        sa.Column("ai_request_id", sa.Uuid()),
        *common(),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="growth_opp_conf_range"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["prospect_id"], ["growth_prospects.id"]),
        sa.ForeignKeyConstraint(["ai_request_id"], ["ai_requests.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    indexed("growth_opportunity_analyses", ["organization_id", "prospect_id", "ai_request_id"])
    op.create_table(
        "growth_gifts",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("prospect_id", sa.Uuid(), nullable=False),
        sa.Column("opportunity_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(250), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("before_state", sa.Text(), nullable=False),
        sa.Column("after_state", sa.Text(), nullable=False),
        sa.Column("asset_reference", sa.String(500)),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("approval_request_id", sa.Uuid()),
        *common(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["prospect_id"], ["growth_prospects.id"]),
        sa.ForeignKeyConstraint(["opportunity_id"], ["growth_opportunity_analyses.id"]),
        sa.ForeignKeyConstraint(["approval_request_id"], ["approval_requests.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    indexed(
        "growth_gifts", ["organization_id", "prospect_id", "opportunity_id", "approval_request_id"]
    )
    op.create_table(
        "growth_outreach_drafts",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("prospect_id", sa.Uuid(), nullable=False),
        sa.Column("growth_gift_id", sa.Uuid(), nullable=False),
        sa.Column("channel", sa.String(30), nullable=False),
        sa.Column("subject", sa.String(300)),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("tone", sa.String(80), nullable=False),
        sa.Column("evidence_used", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("ai_request_id", sa.Uuid(), nullable=False),
        sa.Column("approval_request_id", sa.Uuid()),
        *common(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["prospect_id"], ["growth_prospects.id"]),
        sa.ForeignKeyConstraint(["growth_gift_id"], ["growth_gifts.id"]),
        sa.ForeignKeyConstraint(["ai_request_id"], ["ai_requests.id"]),
        sa.ForeignKeyConstraint(["approval_request_id"], ["approval_requests.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    indexed(
        "growth_outreach_drafts",
        [
            "organization_id",
            "prospect_id",
            "growth_gift_id",
            "ai_request_id",
            "approval_request_id",
        ],
    )
    op.create_table(
        "sales_conversation_analyses",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("prospect_id", sa.Uuid(), nullable=False),
        sa.Column("conversation_reference", sa.String(500), nullable=False),
        sa.Column("intent", sa.String(40), nullable=False),
        sa.Column("sentiment", sa.String(40), nullable=False),
        sa.Column("objection", sa.Text()),
        sa.Column("buying_stage", sa.String(80), nullable=False),
        sa.Column("recommended_action", sa.Text(), nullable=False),
        sa.Column("suggested_reply", sa.Text(), nullable=False),
        sa.Column("ai_request_id", sa.Uuid(), nullable=False),
        *common(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["prospect_id"], ["growth_prospects.id"]),
        sa.ForeignKeyConstraint(["ai_request_id"], ["ai_requests.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    indexed("sales_conversation_analyses", ["organization_id", "prospect_id", "ai_request_id"])
    op.create_table(
        "ai_model_policies",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("task_type", sa.String(100), nullable=False),
        sa.Column("preferred_model", sa.String(200), nullable=False),
        sa.Column("fallback_model", sa.String(200)),
        sa.Column("quality_requirement", sa.String(50), nullable=False),
        *common(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "task_type"),
    )
    indexed("ai_model_policies", ["organization_id"])


def downgrade() -> None:
    if op.get_context().dialect.name == "postgresql":
        op.execute(
            "DROP TRIGGER IF EXISTS growth_prospect_evidence_immutable ON growth_prospect_evidence"
        )
        op.execute("DROP FUNCTION IF EXISTS prevent_growth_prospect_evidence_update()")
    for table, columns in [
        ("ai_model_policies", ["organization_id"]),
        ("sales_conversation_analyses", ["ai_request_id", "prospect_id", "organization_id"]),
        (
            "growth_outreach_drafts",
            [
                "approval_request_id",
                "ai_request_id",
                "growth_gift_id",
                "prospect_id",
                "organization_id",
            ],
        ),
        (
            "growth_gifts",
            ["approval_request_id", "opportunity_id", "prospect_id", "organization_id"],
        ),
        ("growth_opportunity_analyses", ["ai_request_id", "prospect_id", "organization_id"]),
        ("growth_prospect_evidence", ["prospect_id", "organization_id"]),
        ("growth_prospects", ["organization_id"]),
    ]:
        for column in columns:
            op.drop_index(op.f(f"ix_{table}_{column}"), table_name=table)
        op.drop_table(table)
