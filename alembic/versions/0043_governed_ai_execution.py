"""Governed AI provider execution runtime.

Revision ID: 0043_governed_ai_execution
Revises: 0042_closed_loop_learning
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0043_governed_ai_execution"
down_revision: str | None = "0042_closed_loop_learning"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("ai_providers", sa.Column("base_url", sa.String(500)))
    op.add_column("ai_providers", sa.Column("credential_reference", sa.String(200)))
    op.add_column(
        "ai_providers",
        sa.Column("timeout_seconds", sa.Integer(), nullable=False, server_default="30"),
    )
    op.add_column(
        "ai_providers",
        sa.Column("runtime_configuration", sa.JSON(), nullable=False, server_default="{}"),
    )
    op.add_column("ai_requests", sa.Column("prompt_version_id", sa.Uuid()))
    op.add_column("ai_requests", sa.Column("task_type", sa.String(100)))
    op.add_column("ai_requests", sa.Column("system_instructions", sa.Text()))
    op.add_column("ai_requests", sa.Column("input_content", sa.Text()))
    op.add_column("ai_requests", sa.Column("expected_output_schema", sa.JSON()))
    op.add_column(
        "ai_requests",
        sa.Column("runtime_configuration", sa.JSON(), nullable=False, server_default="{}"),
    )
    op.add_column(
        "ai_requests",
        sa.Column("provenance_context", sa.JSON(), nullable=False, server_default="{}"),
    )
    op.add_column("ai_requests", sa.Column("selected_provider_identity", sa.String(150)))
    op.add_column("ai_requests", sa.Column("selected_model_identity", sa.String(200)))
    op.add_column("ai_requests", sa.Column("provider_request_id", sa.String(300)))
    op.add_column("ai_requests", sa.Column("response_content", sa.JSON()))
    op.add_column("ai_requests", sa.Column("structured_output_valid", sa.Boolean()))
    op.add_column("ai_requests", sa.Column("input_tokens", sa.Integer()))
    op.add_column("ai_requests", sa.Column("output_tokens", sa.Integer()))
    op.add_column("ai_requests", sa.Column("total_tokens", sa.Integer()))
    op.add_column("ai_requests", sa.Column("latency_ms", sa.Integer()))
    op.add_column(
        "ai_requests", sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0")
    )
    op.add_column("ai_requests", sa.Column("failure_category", sa.String(50)))
    op.add_column("ai_requests", sa.Column("submitted_at", sa.DateTime(timezone=True)))
    op.add_column("ai_requests", sa.Column("started_at", sa.DateTime(timezone=True)))
    op.add_column("ai_requests", sa.Column("completed_at", sa.DateTime(timezone=True)))
    with op.batch_alter_table("ai_requests") as batch_op:
        batch_op.create_foreign_key(
            op.f("fk_ai_requests_prompt_version_id_prompt_versions"),
            "prompt_versions",
            ["prompt_version_id"],
            ["id"],
        )
    op.create_index(op.f("ix_ai_requests_prompt_version_id"), "ai_requests", ["prompt_version_id"])
    op.add_column("ai_cost_observations", sa.Column("provider_reported_cost", sa.Numeric(19, 6)))
    op.add_column(
        "ai_cost_observations",
        sa.Column("cost_basis", sa.String(30), nullable=False, server_default="estimated"),
    )
    op.add_column("ai_cost_observations", sa.Column("input_tokens", sa.Integer()))
    op.add_column("ai_cost_observations", sa.Column("output_tokens", sa.Integer()))
    op.add_column("ai_cost_observations", sa.Column("total_tokens", sa.Integer()))


def downgrade() -> None:
    for column in [
        "total_tokens",
        "output_tokens",
        "input_tokens",
        "cost_basis",
        "provider_reported_cost",
    ]:
        op.drop_column("ai_cost_observations", column)
    op.drop_index(op.f("ix_ai_requests_prompt_version_id"), table_name="ai_requests")
    with op.batch_alter_table("ai_requests") as batch_op:
        batch_op.drop_constraint(
            op.f("fk_ai_requests_prompt_version_id_prompt_versions"), type_="foreignkey"
        )
    for column in [
        "completed_at",
        "started_at",
        "submitted_at",
        "failure_category",
        "retry_count",
        "latency_ms",
        "total_tokens",
        "output_tokens",
        "input_tokens",
        "structured_output_valid",
        "response_content",
        "provider_request_id",
        "selected_model_identity",
        "selected_provider_identity",
        "provenance_context",
        "runtime_configuration",
        "expected_output_schema",
        "input_content",
        "system_instructions",
        "task_type",
        "prompt_version_id",
    ]:
        op.drop_column("ai_requests", column)
    for column in ["runtime_configuration", "timeout_seconds", "credential_reference", "base_url"]:
        op.drop_column("ai_providers", column)
