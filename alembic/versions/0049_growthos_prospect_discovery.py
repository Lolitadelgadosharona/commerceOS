"""GrowthOS prospect discovery and Commerce Intelligence bridge.

Revision ID: 0049_growthos_discovery
Revises: 0048_growthos_revenue
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0049_growthos_discovery"
down_revision: str | None = "0048_growthos_revenue"
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
        "prospect_discovery_sources",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("source_type", sa.String(30), nullable=False),
        sa.Column("source_name", sa.String(160), nullable=False),
        sa.Column("capability", sa.String(100), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        *common(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "source_name"),
    )
    indexed("prospect_discovery_sources", ["organization_id"])
    op.create_table(
        "prospect_discovery_runs",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("target_industry", sa.String(160), nullable=False),
        sa.Column("target_location", sa.String(250), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("failure_reason", sa.Text()),
        *common(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["source_id"], ["prospect_discovery_sources.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    indexed("prospect_discovery_runs", ["organization_id", "source_id", "created_by"])
    op.create_table(
        "prospect_candidates",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("discovery_run_id", sa.Uuid(), nullable=False),
        sa.Column("business_name", sa.String(250), nullable=False),
        sa.Column("website", sa.String(500)),
        sa.Column("location", sa.String(250), nullable=False),
        sa.Column("category", sa.String(160), nullable=False),
        sa.Column("source_reference", sa.String(1000), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("duplicate_key", sa.String(64), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        *common(),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="prospect_candidate_conf_range"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["discovery_run_id"], ["prospect_discovery_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "duplicate_key"),
    )
    indexed("prospect_candidates", ["organization_id", "discovery_run_id"])
    op.create_table(
        "prospect_research_evidence",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("candidate_id", sa.Uuid(), nullable=False),
        sa.Column("evidence_type", sa.String(80), nullable=False),
        sa.Column("source_url", sa.String(1000)),
        sa.Column("observation", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        *common(),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="prospect_research_ev_conf_range"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["candidate_id"], ["prospect_candidates.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    indexed("prospect_research_evidence", ["organization_id", "candidate_id"])
    if op.get_context().dialect.name == "postgresql":
        op.execute(
            """
            CREATE FUNCTION prevent_prospect_research_evidence_mutation() RETURNS trigger AS $$
            BEGIN RAISE EXCEPTION 'Prospect research evidence is immutable'; END;
            $$ LANGUAGE plpgsql;
            CREATE TRIGGER prospect_research_evidence_immutable
            BEFORE UPDATE OR DELETE ON prospect_research_evidence
            FOR EACH ROW EXECUTE FUNCTION prevent_prospect_research_evidence_mutation();
            """
        )
    op.create_table(
        "growth_business_research_runs",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("candidate_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("capability_id", sa.Uuid(), nullable=False),
        sa.Column("prompt_version_id", sa.Uuid()),
        sa.Column("ai_request_id", sa.Uuid()),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("failure_reason", sa.Text()),
        sa.Column("methodology_version", sa.String(80), nullable=False),
        *common(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["candidate_id"], ["prospect_candidates.id"]),
        sa.ForeignKeyConstraint(["capability_id"], ["ai_model_capabilities.id"]),
        sa.ForeignKeyConstraint(["prompt_version_id"], ["prompt_versions.id"]),
        sa.ForeignKeyConstraint(["ai_request_id"], ["ai_requests.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    indexed(
        "growth_business_research_runs",
        [
            "organization_id",
            "candidate_id",
            "capability_id",
            "prompt_version_id",
            "ai_request_id",
            "created_by",
        ],
    )
    op.create_table(
        "growth_business_research_results",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("research_run_id", sa.Uuid(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("business_profile", sa.JSON(), nullable=False),
        sa.Column("evidence_summary", sa.JSON(), nullable=False),
        sa.Column("potential_growth_issues", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("missing_information", sa.JSON(), nullable=False),
        sa.Column("risk", sa.JSON(), nullable=False),
        *common(),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="result_conf_range"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["research_run_id"], ["growth_business_research_runs.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("research_run_id"),
    )
    indexed("growth_business_research_results", ["organization_id", "research_run_id"])
    op.create_table(
        "prospect_qualification_assessments",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("candidate_id", sa.Uuid(), nullable=False),
        sa.Column("score", sa.Float()),
        sa.Column("calculation_inputs", sa.JSON(), nullable=False),
        sa.Column("missing_inputs", sa.JSON(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("formula_version", sa.String(80), nullable=False),
        *common(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["candidate_id"], ["prospect_candidates.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("candidate_id"),
    )
    indexed("prospect_qualification_assessments", ["organization_id", "candidate_id"])
    op.create_table(
        "business_demand_signals",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("source_domain", sa.String(40), nullable=False),
        sa.Column("industry", sa.String(160), nullable=False),
        sa.Column("signal_type", sa.String(80), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("evidence_reference", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("source_research_result_id", sa.Uuid(), nullable=False),
        *common(),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="business_demand_conf_range"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["source_research_result_id"], ["growth_business_research_results.id"]
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    indexed("business_demand_signals", ["organization_id", "source_research_result_id"])


def downgrade() -> None:
    for table, columns in [
        ("business_demand_signals", ["source_research_result_id", "organization_id"]),
        ("prospect_qualification_assessments", ["candidate_id", "organization_id"]),
        ("growth_business_research_results", ["research_run_id", "organization_id"]),
        (
            "growth_business_research_runs",
            [
                "created_by",
                "ai_request_id",
                "prompt_version_id",
                "capability_id",
                "candidate_id",
                "organization_id",
            ],
        ),
    ]:
        for column in columns:
            op.drop_index(op.f(f"ix_{table}_{column}"), table_name=table)
        op.drop_table(table)
    if op.get_context().dialect.name == "postgresql":
        op.execute(
            "DROP TRIGGER IF EXISTS prospect_research_evidence_immutable "
            "ON prospect_research_evidence"
        )
        op.execute("DROP FUNCTION IF EXISTS prevent_prospect_research_evidence_mutation()")
    for table, columns in [
        ("prospect_research_evidence", ["candidate_id", "organization_id"]),
        ("prospect_candidates", ["discovery_run_id", "organization_id"]),
        ("prospect_discovery_runs", ["created_by", "source_id", "organization_id"]),
        ("prospect_discovery_sources", ["organization_id"]),
    ]:
        for column in columns:
            op.drop_index(op.f(f"ix_{table}_{column}"), table_name=table)
        op.drop_table(table)
