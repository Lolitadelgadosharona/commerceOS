"""Discovery automation layer.

Revision ID: 0062_discovery_automation
Revises: 0061_prospect_acquisition
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0062_discovery_automation"
down_revision: str | None = "0061_prospect_acquisition"
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
        "discovery_automation_plans",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("industry", sa.String(160), nullable=False),
        sa.Column("geography", sa.String(250), nullable=False),
        sa.Column("query_criteria", sa.JSON(), nullable=False),
        sa.Column("cadence", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("next_run_at", sa.DateTime(timezone=True)),
        sa.Column("last_run_at", sa.DateTime(timezone=True)),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        *common(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["source_id"], ["prospect_discovery_sources.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "name"),
    )
    indexes("discovery_automation_plans", ["organization_id", "source_id", "created_by"])

    with op.batch_alter_table("prospect_discovery_runs") as batch:
        batch.add_column(sa.Column("automation_plan_id", sa.Uuid()))
        batch.add_column(
            sa.Column("query_criteria", sa.JSON(), nullable=False, server_default="{}")
        )
        batch.add_column(
            sa.Column("result_count", sa.Integer(), nullable=False, server_default="0")
        )
        batch.create_foreign_key(
            op.f("fk_prospect_discovery_runs_automation_plan_id_discovery_automation_plans"),
            "discovery_automation_plans",
            ["automation_plan_id"],
            ["id"],
        )
        batch.create_index(
            op.f("ix_prospect_discovery_runs_automation_plan_id"), ["automation_plan_id"]
        )
    with op.batch_alter_table("prospect_discovery_runs") as batch:
        batch.alter_column("query_criteria", server_default=None)
        batch.alter_column("result_count", server_default=None)

    op.create_table(
        "google_business_discovery_results",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("discovery_run_id", sa.Uuid(), nullable=False),
        sa.Column("candidate_id", sa.Uuid(), nullable=False),
        sa.Column("external_reference", sa.String(1000), nullable=False),
        sa.Column("business_name", sa.String(250), nullable=False),
        sa.Column("category", sa.String(160), nullable=False),
        sa.Column("location", sa.String(250), nullable=False),
        sa.Column("rating", sa.Float()),
        sa.Column("review_count", sa.Integer()),
        sa.Column("website", sa.String(500)),
        sa.Column("public_profile", sa.JSON(), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        *common(),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="gb_result_conf"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["discovery_run_id"], ["prospect_discovery_runs.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["candidate_id"], ["prospect_candidates.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("discovery_run_id", "external_reference"),
    )
    indexes(
        "google_business_discovery_results", ["organization_id", "discovery_run_id", "candidate_id"]
    )

    op.create_table(
        "prospect_memory_events",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("candidate_id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("change_type", sa.String(40), nullable=False),
        sa.Column("source_reference", sa.String(1000), nullable=False),
        sa.Column("previous_state", sa.JSON(), nullable=False),
        sa.Column("observed_state", sa.JSON(), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        *common(),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name="prospect_memory_conf"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["candidate_id"], ["prospect_candidates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_id"], ["prospect_discovery_sources.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes("prospect_memory_events", ["organization_id", "candidate_id", "source_id"])


def downgrade() -> None:
    for table in ["prospect_memory_events", "google_business_discovery_results"]:
        for column in (
            ["source_id", "candidate_id", "organization_id"]
            if table == "prospect_memory_events"
            else ["candidate_id", "discovery_run_id", "organization_id"]
        ):
            op.drop_index(op.f(f"ix_{table}_{column}"), table_name=table)
        op.drop_table(table)
    with op.batch_alter_table("prospect_discovery_runs") as batch:
        batch.drop_index(op.f("ix_prospect_discovery_runs_automation_plan_id"))
        batch.drop_constraint(
            op.f("fk_prospect_discovery_runs_automation_plan_id_discovery_automation_plans"),
            type_="foreignkey",
        )
        batch.drop_column("result_count")
        batch.drop_column("query_criteria")
        batch.drop_column("automation_plan_id")
    for column in ["created_by", "source_id", "organization_id"]:
        op.drop_index(
            op.f(f"ix_discovery_automation_plans_{column}"), table_name="discovery_automation_plans"
        )
    op.drop_table("discovery_automation_plans")
