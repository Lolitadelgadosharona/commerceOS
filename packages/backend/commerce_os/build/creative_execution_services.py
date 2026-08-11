from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import TypeVar
from uuid import UUID

from sqlalchemy.orm import Session

from commerce_os.build.creative_asset_models import CreativeAsset
from commerce_os.build.creative_execution_models import (
    CreativeArtifact,
    CreativeExecutionRecord,
    CreativeGenerationCostObservation,
)
from commerce_os.build.creative_execution_schemas import (
    CreativeArtifactCreate,
    ExecutionRecordCreate,
    GenerationCostCreate,
)
from commerce_os.build.creative_generation_models import (
    CreativeGenerationJob,
)
from commerce_os.build.errors import BuildScopeError, BuildStateError
from commerce_os.shared.database import Base

EntityT = TypeVar("EntityT", bound=Base)
JOB_TRANSITIONS = {
    "pending": {"queued", "cancelled"},
    "queued": {"running", "cancelled"},
    "running": {"validating", "failed", "retrying", "cancelled"},
    "validating": {"succeeded", "failed", "retrying"},
    "retrying": {"queued", "failed", "cancelled"},
    "succeeded": set(),
    "failed": set(),
    "cancelled": set(),
}


class CreativeExecutionService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def transition_job(
        self, job_id: UUID, organization_id: UUID, status: str, failure_reason: str | None
    ) -> CreativeGenerationJob:
        job = self._job(job_id, organization_id)
        if status not in JOB_TRANSITIONS.get(job.status, set()):
            raise BuildStateError(
                f"Generation job cannot transition from {job.status} to {status}."
            )
        if status == "failed" and not failure_reason:
            raise BuildStateError("A failed generation job requires a failure reason.")
        now = datetime.now(UTC)
        if status == "running" and job.started_at is None:
            job.started_at = now
        if status in {"succeeded", "failed", "cancelled"}:
            job.completed_at = now
        if status == "retrying":
            job.retry_count += 1
        job.failure_reason = failure_reason if status == "failed" else None
        job.status = status
        return self._save(job)

    def create_record(self, payload: ExecutionRecordCreate) -> CreativeExecutionRecord:
        job = self._job(payload.generation_job_id, payload.organization_id)
        if payload.provider != job.provider_id:
            raise BuildScopeError("Execution provider does not match the generation job.")
        if payload.execution_status != job.status:
            raise BuildStateError("Execution record status must match the generation job state.")
        if payload.execution_status == "succeeded" and payload.output_reference is None:
            raise BuildStateError("Successful execution records require an output reference.")
        values = payload.model_dump(exclude={"provider", "estimated_cost", "actual_cost"})
        return self._save(
            CreativeExecutionRecord(
                **values,
                provider_id=job.provider_id,
                estimated_cost=self._money(payload.estimated_cost),
                actual_cost=self._money(payload.actual_cost)
                if payload.actual_cost is not None
                else None,
            )
        )

    def create_artifact(self, payload: CreativeArtifactCreate) -> CreativeArtifact:
        job = self._job(payload.generation_job_id, payload.organization_id)
        if job.status != "succeeded":
            raise BuildStateError("Creative artifacts require a succeeded generation job.")
        asset = self.session.get(CreativeAsset, payload.asset_id)
        if asset is None or asset.organization_id != payload.organization_id:
            raise BuildScopeError("Creative asset was not found in this organization.")
        values = payload.model_dump(exclude={"metadata"})
        return self._save(CreativeArtifact(**values, artifact_metadata=payload.metadata))

    def create_cost(self, payload: GenerationCostCreate) -> CreativeGenerationCostObservation:
        job = self._job(payload.job, payload.organization_id)
        if payload.provider != job.provider_id:
            raise BuildScopeError("Cost provider does not match the generation job.")
        return self._save(
            CreativeGenerationCostObservation(
                organization_id=payload.organization_id,
                provider_id=payload.provider,
                job_id=payload.job,
                estimated_cost=self._money(payload.estimated_cost),
                actual_cost=self._money(payload.actual_cost),
                currency=payload.currency,
            )
        )

    def _job(self, job_id: UUID, organization_id: UUID) -> CreativeGenerationJob:
        job = self.session.get(CreativeGenerationJob, job_id)
        if job is None or job.organization_id != organization_id:
            raise BuildScopeError("Generation job was not found in this organization.")
        return job

    @staticmethod
    def _money(value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)

    def _save(self, entity: EntityT) -> EntityT:
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity
