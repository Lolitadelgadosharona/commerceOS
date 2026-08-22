import hashlib
from typing import Any, TypeVar, cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from commerce_os.ai_runtime.models import AIModelCapability, PromptVersion
from commerce_os.growth.discovery_models import (
    GrowthBusinessResearchResult,
    GrowthBusinessResearchRun,
    ProspectCandidate,
    ProspectDiscoveryRun,
    ProspectDiscoverySource,
    ProspectQualificationAssessment,
    ProspectResearchEvidence,
)
from commerce_os.growth.discovery_schemas import (
    BusinessResearchStart,
    CandidateCreate,
    DiscoveryRunCreate,
    DiscoverySourceCreate,
    QualificationInputs,
    ResearchEvidenceCreate,
)
from commerce_os.growth.errors import GrowthError
from commerce_os.shared.audit import record_audit_event
from commerce_os.shared.database import Base
from commerce_os.shared.models import utc_now

EntityT = TypeVar("EntityT", bound=Base)
DISCOVERY_TRANSITIONS = {
    "draft": {"queued", "cancelled"},
    "queued": {"running", "cancelled"},
    "running": {"completed", "failed"},
    "completed": set(),
    "failed": set(),
    "cancelled": set(),
}
RESEARCH_TRANSITIONS = {
    "queued": {"running", "cancelled"},
    "running": {"completed", "failed"},
    "completed": set(),
    "failed": set(),
    "cancelled": set(),
}
RESEARCH_OUTPUT_SCHEMA = {
    "type": "object",
    "required": [
        "summary",
        "business_profile",
        "evidence_summary",
        "potential_growth_issues",
        "confidence",
        "missing_information",
        "risk",
    ],
    "properties": {
        "summary": {"type": "string"},
        "business_profile": {"type": "object"},
        "evidence_summary": {"type": "array"},
        "potential_growth_issues": {"type": "array"},
        "confidence": {"type": "number"},
        "missing_information": {"type": "array"},
        "risk": {"type": "array"},
    },
}


def scoped_growth_discovery(
    session: Session, model: type[EntityT], entity_id: UUID, organization_id: UUID
) -> EntityT:
    entity = session.get(model, entity_id)
    if entity is None or entity.organization_id != organization_id:  # type: ignore[attr-defined]
        raise GrowthError(
            "GrowthOS discovery record was not found in this organization.", "not_found"
        )
    return entity


class GrowthDiscoveryService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_source(
        self, payload: DiscoverySourceCreate, actor_id: UUID
    ) -> ProspectDiscoverySource:
        self._organization(payload.organization_id)
        values = payload.model_dump(exclude={"metadata"})
        values["source_metadata"] = payload.metadata
        return self._save(
            ProspectDiscoverySource(**values), actor_id, "growthos.discovery_source.created"
        )

    def create_run(self, payload: DiscoveryRunCreate, actor_id: UUID) -> ProspectDiscoveryRun:
        source = scoped_growth_discovery(
            self.session, ProspectDiscoverySource, payload.source_id, payload.organization_id
        )
        if source.status != "active":
            raise GrowthError("Discovery runs require an active source definition.")
        return self._save(
            ProspectDiscoveryRun(
                **payload.model_dump(),
                status="draft",
                started_at=None,
                completed_at=None,
                created_by=actor_id,
                failure_reason=None,
            ),
            actor_id,
            "growthos.discovery_run.created",
        )

    def transition_run(
        self,
        run: ProspectDiscoveryRun,
        status: str,
        actor_id: UUID,
        failure_reason: str | None = None,
    ) -> ProspectDiscoveryRun:
        if status not in DISCOVERY_TRANSITIONS[run.status]:
            raise GrowthError(f"Discovery run cannot transition from {run.status} to {status}.")
        run.status = status
        if status == "running":
            run.started_at = utc_now()
        if status in {"completed", "failed", "cancelled"}:
            run.completed_at = utc_now()
        run.failure_reason = failure_reason if status == "failed" else None
        return self._save(run, actor_id, f"growthos.discovery_run.{status}")

    def create_candidate(self, payload: CandidateCreate, actor_id: UUID) -> ProspectCandidate:
        run = scoped_growth_discovery(
            self.session, ProspectDiscoveryRun, payload.discovery_run_id, payload.organization_id
        )
        if run.status != "running":
            raise GrowthError("Candidates may only be recorded for a running discovery run.")
        duplicate_key = self._duplicate_key(
            payload.business_name, payload.website, payload.location
        )
        existing = self.session.scalar(
            select(ProspectCandidate).where(
                ProspectCandidate.organization_id == payload.organization_id,
                ProspectCandidate.duplicate_key == duplicate_key,
            )
        )
        if existing is not None:
            return existing
        return self._save(
            ProspectCandidate(**payload.model_dump(), duplicate_key=duplicate_key, status="new"),
            actor_id,
            "growthos.prospect_candidate.created",
        )

    def create_evidence(
        self, payload: ResearchEvidenceCreate, actor_id: UUID
    ) -> ProspectResearchEvidence:
        candidate = scoped_growth_discovery(
            self.session, ProspectCandidate, payload.candidate_id, payload.organization_id
        )
        if candidate.status == "new":
            candidate.status = "researching"
            self.session.add(candidate)
        return self._save(
            ProspectResearchEvidence(**payload.model_dump()),
            actor_id,
            "growthos.research_evidence.created",
        )

    def create_research_run(
        self, candidate: ProspectCandidate, payload: BusinessResearchStart, actor_id: UUID
    ) -> GrowthBusinessResearchRun:
        self._scoped(AIModelCapability, payload.capability_id, payload.organization_id)
        if payload.prompt_version_id is not None:
            prompt = self._scoped(PromptVersion, payload.prompt_version_id, payload.organization_id)
            if prompt.status != "approved":
                raise GrowthError("Business research requires an approved prompt version.")
        evidence_count = self.session.scalar(
            select(func.count())
            .select_from(ProspectResearchEvidence)
            .where(
                ProspectResearchEvidence.organization_id == payload.organization_id,
                ProspectResearchEvidence.candidate_id == candidate.id,
            )
        )
        if not evidence_count:
            raise GrowthError("Business research requires traceable candidate evidence.")
        candidate.status = "researching"
        self.session.add(candidate)
        return self._save(
            GrowthBusinessResearchRun(
                organization_id=payload.organization_id,
                candidate_id=candidate.id,
                status="queued",
                capability_id=payload.capability_id,
                prompt_version_id=payload.prompt_version_id,
                ai_request_id=None,
                created_by=actor_id,
                started_at=None,
                completed_at=None,
                failure_reason=None,
                methodology_version="growth-business-research-v1",
            ),
            actor_id,
            "growthos.business_research.queued",
        )

    def evidence(self, run: GrowthBusinessResearchRun) -> list[ProspectResearchEvidence]:
        return list(
            self.session.scalars(
                select(ProspectResearchEvidence).where(
                    ProspectResearchEvidence.organization_id == run.organization_id,
                    ProspectResearchEvidence.candidate_id == run.candidate_id,
                )
            )
        )

    def start_research(
        self, run: GrowthBusinessResearchRun, ai_request_id: UUID, actor_id: UUID
    ) -> GrowthBusinessResearchRun:
        if "running" not in RESEARCH_TRANSITIONS[run.status]:
            raise GrowthError("Only queued business research may start.")
        run.status = "running"
        run.ai_request_id = ai_request_id
        run.started_at = utc_now()
        return self._save(run, actor_id, "growthos.business_research.started", "service")

    def complete_research(
        self, run: GrowthBusinessResearchRun, content: dict[str, Any], actor_id: UUID
    ) -> GrowthBusinessResearchRun:
        if "completed" not in RESEARCH_TRANSITIONS[run.status]:
            raise GrowthError("Only running business research may complete.")
        confidence = float(content["confidence"])
        if not 0 <= confidence <= 1:
            raise GrowthError("Business research confidence must be between 0 and 1.")
        result = GrowthBusinessResearchResult(
            organization_id=run.organization_id,
            research_run_id=run.id,
            summary=str(content["summary"]),
            business_profile=cast(dict[str, Any], content["business_profile"]),
            evidence_summary=cast(list[dict[str, Any]], content["evidence_summary"]),
            potential_growth_issues=[str(x) for x in content["potential_growth_issues"]],
            confidence=confidence,
            missing_information=[str(x) for x in content["missing_information"]],
            risk=[str(x) for x in content["risk"]],
        )
        self.session.add(result)
        self.session.flush()
        run.status = "completed"
        run.completed_at = utc_now()
        return self._save(run, actor_id, "growthos.business_research.completed", "service")

    def fail_research(
        self, run: GrowthBusinessResearchRun, reason: str, actor_id: UUID
    ) -> GrowthBusinessResearchRun:
        if "failed" not in RESEARCH_TRANSITIONS[run.status]:
            raise GrowthError("Only running business research may fail.")
        run.status = "failed"
        run.failure_reason = reason
        run.completed_at = utc_now()
        return self._save(run, actor_id, "growthos.business_research.failed", "service")

    def qualify(
        self, candidate: ProspectCandidate, payload: QualificationInputs, actor_id: UUID
    ) -> ProspectQualificationAssessment:
        supplied = payload.model_dump(exclude={"organization_id"})
        missing = [name for name, value in supplied.items() if value is None]
        score = None
        if not missing:
            score = round(
                cast(float, supplied["pain_signal"]) * 0.35
                + cast(float, supplied["purchase_probability"]) * 0.30
                + cast(float, supplied["accessibility"]) * 0.20
                + cast(float, supplied["quick_win_potential"]) * 0.15,
                2,
            )
            if score >= 70:
                candidate.status = "qualified"
                self.session.add(candidate)
        explanation = (
            "Score withheld because required inputs are missing: " + ", ".join(missing)
            if missing
            else (
                "Weighted deterministic score: pain 35%, purchase 30%, accessibility 20%, "
                "quick win 15%."
            )
        )
        existing = self.session.scalar(
            select(ProspectQualificationAssessment).where(
                ProspectQualificationAssessment.candidate_id == candidate.id
            )
        )
        if existing is not None:
            existing.score = score
            existing.calculation_inputs = supplied
            existing.missing_inputs = missing
            existing.explanation = explanation
            return self._save(existing, actor_id, "growthos.qualification.recalculated")
        return self._save(
            ProspectQualificationAssessment(
                organization_id=payload.organization_id,
                candidate_id=candidate.id,
                score=score,
                calculation_inputs=supplied,
                missing_inputs=missing,
                explanation=explanation,
                formula_version="growthos-qualification-v1",
            ),
            actor_id,
            "growthos.qualification.calculated",
        )

    def _scoped(self, model: type[EntityT], entity_id: UUID, organization_id: UUID) -> EntityT:
        entity = self.session.get(model, entity_id)
        if entity is None or entity.organization_id != organization_id:  # type: ignore[attr-defined]
            raise GrowthError("Referenced record was not found in this organization.", "not_found")
        return entity

    def _organization(self, organization_id: UUID) -> None:
        table = Base.metadata.tables["organizations"]
        if self.session.scalar(select(table.c.id).where(table.c.id == organization_id)) is None:
            raise GrowthError("Organization was not found.", "not_found")

    @staticmethod
    def _duplicate_key(name: str, website: str | None, location: str) -> str:
        normalized = "|".join(
            [
                name.strip().casefold(),
                (website or "").strip().casefold().rstrip("/"),
                location.strip().casefold(),
            ]
        )
        return hashlib.sha256(normalized.encode()).hexdigest()

    def _save(
        self, entity: EntityT, actor_id: UUID, action: str, actor_type: str = "human"
    ) -> EntityT:
        self.session.add(entity)
        try:
            self.session.flush()
        except IntegrityError as exc:
            self.session.rollback()
            raise GrowthError("GrowthOS record conflicts with an existing record.") from exc
        item = cast(Any, entity)
        record_audit_event(
            self.session,
            organization_id=item.organization_id,
            actor_type=actor_type,
            actor_id=actor_id,
            action=action,
            entity_type=item.__tablename__,
            entity_id=cast(UUID, item.id),
            metadata={"result": "success", "external_execution": "none"},
        )
        self.session.commit()
        self.session.refresh(entity)
        return entity
