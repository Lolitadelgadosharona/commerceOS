import hashlib
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any, TypeVar, cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from commerce_os.ai_runtime.models import AIModelCapability, PromptVersion
from commerce_os.growth.discovery_models import (
    BusinessProfileEvidenceSnapshot,
    DiscoveryAutomationPlan,
    GoogleBusinessDiscoveryResult,
    GrowthBusinessResearchResult,
    GrowthBusinessResearchRun,
    InstagramEvidenceSnapshot,
    ProspectCandidate,
    ProspectDiscoveryRun,
    ProspectDiscoverySource,
    ProspectMemoryEvent,
    ProspectQualificationAssessment,
    ProspectResearchEvidence,
    WebsiteEvidenceSnapshot,
)
from commerce_os.growth.discovery_schemas import (
    AutomationPlanCreate,
    BusinessProfileEvidenceCreate,
    BusinessResearchStart,
    CandidateCreate,
    DiscoveryRunCreate,
    DiscoverySourceCreate,
    GoogleBusinessResultCreate,
    InstagramEvidenceCreate,
    ManualProspectImport,
    OperatorRevenueDashboard,
    ProspectMemoryEventCreate,
    ProspectPipelineRead,
    QualificationInputs,
    RankedProspectRead,
    ResearchEvidenceCreate,
    WebsiteEvidenceCreate,
)
from commerce_os.growth.errors import GrowthError
from commerce_os.shared.audit import record_audit_event
from commerce_os.shared.database import Base
from commerce_os.shared.events import BusinessEventEnvelope, EventActor
from commerce_os.shared.models import utc_now
from commerce_os.shared.outbox import add_to_outbox

EntityT = TypeVar("EntityT", bound=Base)
DISCOVERY_TRANSITIONS = {
    "draft": {"queued", "running", "cancelled"},
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

    def import_manual_prospect(
        self, payload: ManualProspectImport, actor_id: UUID
    ) -> ProspectCandidate:
        """Compose the existing source/run/candidate/evidence workflow for founder import."""
        source = self.session.scalar(
            select(ProspectDiscoverySource)
            .where(
                ProspectDiscoverySource.organization_id == payload.organization_id,
                ProspectDiscoverySource.source_type == "manual",
                ProspectDiscoverySource.status == "active",
            )
            .order_by(ProspectDiscoverySource.created_at)
            .limit(1)
        )
        if source is None:
            source = self.create_source(
                DiscoverySourceCreate(
                    organization_id=payload.organization_id,
                    source_type="manual",
                    source_name="Founder controlled import",
                    capability="prospect_evidence_import",
                    metadata={"external_execution": False},
                    adapter_key="manual",
                    collection_mode="controlled_import",
                ),
                actor_id,
            )
        run = self.create_run(
            DiscoveryRunCreate(
                organization_id=payload.organization_id,
                source_id=source.id,
                query=payload.business_name,
                target_industry=payload.category,
                target_location=payload.location,
                query_criteria={"mode": "founder_controlled_import"},
            ),
            actor_id,
        )
        run = self.transition_run(run, "running", actor_id)
        candidate = self.create_candidate(
            CandidateCreate(
                organization_id=payload.organization_id,
                discovery_run_id=run.id,
                business_name=payload.business_name,
                website=payload.website,
                location=payload.location,
                category=payload.category,
                source_reference=payload.source_reference,
                confidence=payload.confidence,
            ),
            actor_id,
        )
        self.create_evidence(
            ResearchEvidenceCreate(
                organization_id=payload.organization_id,
                candidate_id=candidate.id,
                evidence_type=payload.evidence_type,
                source_url=payload.source_reference,
                observation=payload.observation,
                confidence=payload.confidence,
                collected_at=payload.collected_at,
            ),
            actor_id,
        )
        qualification = QualificationInputs(
            organization_id=payload.organization_id,
            pain_signal=payload.pain_signal,
            purchase_probability=payload.purchase_probability,
            accessibility=payload.accessibility,
            quick_win_potential=payload.quick_win_potential,
        )
        if any(
            value is not None
            for value in qualification.model_dump(exclude={"organization_id"}).values()
        ):
            self.qualify(candidate, qualification, actor_id)
        self.transition_run(run, "completed", actor_id)
        self.session.refresh(candidate)
        return candidate

    def create_run(self, payload: DiscoveryRunCreate, actor_id: UUID) -> ProspectDiscoveryRun:
        source = scoped_growth_discovery(
            self.session, ProspectDiscoverySource, payload.source_id, payload.organization_id
        )
        if source.status != "active":
            raise GrowthError("Discovery runs require an active source definition.")
        if payload.automation_plan_id is not None:
            plan = scoped_growth_discovery(
                self.session,
                DiscoveryAutomationPlan,
                payload.automation_plan_id,
                payload.organization_id,
            )
            if plan.source_id != source.id:
                raise GrowthError("Automation plan source must match the discovery run source.")
        return self._save(
            ProspectDiscoveryRun(
                **payload.model_dump(),
                status="draft",
                started_at=None,
                completed_at=None,
                created_by=actor_id,
                failure_reason=None,
                result_count=0,
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
        if status == "completed":
            run.result_count = int(
                self.session.scalar(
                    select(func.count())
                    .select_from(GoogleBusinessDiscoveryResult)
                    .where(GoogleBusinessDiscoveryResult.discovery_run_id == run.id)
                )
                or 0
            )
        run.failure_reason = failure_reason if status == "failed" else None
        return self._save(run, actor_id, f"growthos.discovery_run.{status}")

    def create_automation_plan(
        self, payload: AutomationPlanCreate, actor_id: UUID
    ) -> DiscoveryAutomationPlan:
        source = scoped_growth_discovery(
            self.session, ProspectDiscoverySource, payload.source_id, payload.organization_id
        )
        if source.status != "active" or source.collection_mode != "controlled_connector":
            raise GrowthError("Automation plans require an active controlled connector source.")
        return self._save(
            DiscoveryAutomationPlan(
                **payload.model_dump(), status="active", last_run_at=None, created_by=actor_id
            ),
            actor_id,
            "growthos.discovery_automation.created",
        )

    def start_automation_run(
        self, plan: DiscoveryAutomationPlan, actor_id: UUID
    ) -> ProspectDiscoveryRun:
        if plan.status != "active":
            raise GrowthError("Only active discovery automation plans may start a run.")
        run = self.create_run(
            DiscoveryRunCreate(
                organization_id=plan.organization_id,
                source_id=plan.source_id,
                query=f"{plan.industry} businesses in {plan.geography}",
                target_industry=plan.industry,
                target_location=plan.geography,
                automation_plan_id=plan.id,
                query_criteria=plan.query_criteria,
            ),
            actor_id,
        )
        run = self.transition_run(run, "running", actor_id)
        plan.last_run_at = run.started_at
        plan.next_run_at = (
            run.started_at + timedelta(days=1) if run.started_at is not None else None
        )
        self.session.add(plan)
        self.session.commit()
        return run

    def record_google_business_result(
        self, payload: GoogleBusinessResultCreate, actor_id: UUID
    ) -> GoogleBusinessDiscoveryResult:
        run = scoped_growth_discovery(
            self.session,
            ProspectDiscoveryRun,
            payload.discovery_run_id,
            payload.organization_id,
        )
        source = scoped_growth_discovery(
            self.session, ProspectDiscoverySource, run.source_id, payload.organization_id
        )
        if run.status != "running":
            raise GrowthError("Google Business results require a running discovery run.")
        if source.source_type != "google_business_profile":
            raise GrowthError("Google Business results require a Google Business source.")
        candidate = self.create_candidate(
            CandidateCreate(
                organization_id=payload.organization_id,
                discovery_run_id=run.id,
                business_name=payload.business_name,
                website=payload.website,
                location=payload.location,
                category=payload.category,
                source_reference=payload.external_reference,
                confidence=payload.confidence,
            ),
            actor_id,
        )
        return self._save(
            GoogleBusinessDiscoveryResult(**payload.model_dump(), candidate_id=candidate.id),
            actor_id,
            "growthos.google_business_result.recorded",
        )

    def record_memory_event(
        self, payload: ProspectMemoryEventCreate, actor_id: UUID
    ) -> ProspectMemoryEvent:
        scoped_growth_discovery(
            self.session, ProspectCandidate, payload.candidate_id, payload.organization_id
        )
        scoped_growth_discovery(
            self.session, ProspectDiscoverySource, payload.source_id, payload.organization_id
        )
        if payload.previous_state == payload.observed_state:
            raise GrowthError("Prospect memory requires an observed change.")
        return self._save(
            ProspectMemoryEvent(**payload.model_dump()),
            actor_id,
            "growthos.prospect_memory.recorded",
        )

    def ranked_prospects(self, organization_id: UUID) -> list[RankedProspectRead]:
        self._organization(organization_id)
        rows = list(
            self.session.execute(
                select(ProspectCandidate, ProspectQualificationAssessment)
                .join(
                    ProspectQualificationAssessment,
                    ProspectQualificationAssessment.candidate_id == ProspectCandidate.id,
                )
                .where(ProspectCandidate.organization_id == organization_id)
                .order_by(
                    ProspectQualificationAssessment.score.desc().nullslast(),
                    ProspectCandidate.created_at,
                )
            )
        )
        return [
            RankedProspectRead(
                candidate_id=candidate.id,
                business_name=candidate.business_name,
                location=candidate.location,
                score=assessment.score,
                growth_pain=assessment.calculation_inputs.get("pain_signal"),
                purchase_probability=assessment.calculation_inputs.get("purchase_probability"),
                accessibility=assessment.calculation_inputs.get("accessibility"),
                quick_win=assessment.calculation_inputs.get("quick_win_potential"),
                missing_inputs=assessment.missing_inputs,
            )
            for candidate, assessment in rows
        ]

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

    def collect_website_evidence(
        self, payload: WebsiteEvidenceCreate, actor_id: UUID
    ) -> WebsiteEvidenceSnapshot:
        self._evidence_context(
            payload.candidate_id, payload.source_id, payload.organization_id, {"website", "manual"}
        )
        return self._save(
            WebsiteEvidenceSnapshot(**payload.model_dump()),
            actor_id,
            "growthos.website_evidence.collected",
        )

    def collect_business_profile_evidence(
        self, payload: BusinessProfileEvidenceCreate, actor_id: UUID
    ) -> BusinessProfileEvidenceSnapshot:
        self._evidence_context(
            payload.candidate_id,
            payload.source_id,
            payload.organization_id,
            {"google_business_profile", "reviews", "manual"},
        )
        return self._save(
            BusinessProfileEvidenceSnapshot(**payload.model_dump()),
            actor_id,
            "growthos.business_profile_evidence.collected",
        )

    def collect_instagram_evidence(
        self, payload: InstagramEvidenceCreate, actor_id: UUID
    ) -> InstagramEvidenceSnapshot:
        self._evidence_context(
            payload.candidate_id,
            payload.source_id,
            payload.organization_id,
            {"instagram", "manual"},
        )
        return self._save(
            InstagramEvidenceSnapshot(**payload.model_dump()),
            actor_id,
            "growthos.instagram_evidence.collected",
        )

    def pipeline(self, candidate_id: UUID, organization_id: UUID) -> ProspectPipelineRead:
        candidate = scoped_growth_discovery(
            self.session, ProspectCandidate, candidate_id, organization_id
        )
        tables = Base.metadata.tables
        evidence_count = sum(
            int(
                self.session.scalar(
                    select(func.count())
                    .select_from(tables[name])
                    .where(
                        tables[name].c.organization_id == organization_id,
                        tables[name].c.candidate_id == candidate_id,
                    )
                )
                or 0
            )
            for name in [
                "prospect_research_evidence",
                "website_evidence_snapshots",
                "business_profile_evidence_snapshots",
                "instagram_evidence_snapshots",
            ]
        )
        prospects = tables["growth_prospects"]
        prospect_id = self.session.scalar(
            select(prospects.c.id).where(
                prospects.c.organization_id == organization_id,
                prospects.c.source_candidate_id == candidate_id,
            )
        )
        profile_id = None
        opportunity_ids: list[UUID] = []
        gift_ids: list[UUID] = []
        draft_ids: list[UUID] = []
        if prospect_id is not None:
            profiles = tables["business_growth_profiles"]
            profile_id = self.session.scalar(
                select(profiles.c.id).where(profiles.c.prospect_id == prospect_id)
            )
            opportunity_ids = self._ids("growth_opportunity_analyses", prospect_id)
            gift_ids = self._ids("growth_gifts", prospect_id)
            draft_ids = self._ids("growth_outreach_drafts", prospect_id)
        next_step = "collect_evidence"
        if evidence_count and candidate.status != "qualified":
            next_step = "qualify_prospect"
        if candidate.status == "qualified" and prospect_id is None:
            next_step = "activate_prospect"
        if prospect_id is not None and profile_id is None:
            next_step = "create_growth_profile"
        if profile_id is not None and not opportunity_ids:
            next_step = "create_growth_opportunity"
        if opportunity_ids and not gift_ids:
            next_step = "prepare_growth_gift"
        if gift_ids and not draft_ids:
            next_step = "prepare_outreach_draft"
        if draft_ids:
            next_step = "human_review"
        return ProspectPipelineRead(
            organization_id=organization_id,
            candidate_id=candidate_id,
            candidate_status=candidate.status,
            evidence_count=evidence_count,
            growth_prospect_id=prospect_id,
            growth_profile_id=profile_id,
            opportunity_ids=opportunity_ids,
            growth_gift_ids=gift_ids,
            outreach_draft_ids=draft_ids,
            next_step=next_step,
        )

    def operator_dashboard(self, organization_id: UUID) -> OperatorRevenueDashboard:
        self._organization(organization_id)
        tables = Base.metadata.tables
        day_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)

        def count(name: str, *criteria: Any) -> int:
            table = tables[name]
            return int(
                self.session.scalar(
                    select(func.count())
                    .select_from(table)
                    .where(table.c.organization_id == organization_id, *criteria)
                )
                or 0
            )

        candidates = tables["prospect_candidates"]
        prospects = tables["growth_prospects"]
        gifts = tables["growth_gifts"]
        drafts = tables["growth_outreach_drafts"]
        analyses = tables["sales_conversation_analyses"]
        experiments = tables["revenue_experiments"]
        costs = tables["ai_cost_observations"]
        cost_rows = list(
            self.session.execute(
                select(costs.c.estimated_cost, costs.c.currency).where(
                    costs.c.organization_id == organization_id,
                    costs.c.created_at >= day_start,
                    costs.c.created_at < day_end,
                )
            )
        )
        currencies = {row.currency for row in cost_rows}
        ai_currency = next(iter(currencies)) if len(currencies) == 1 else None
        ai_cost = (
            sum((Decimal(row.estimated_cost) for row in cost_rows), Decimal("0"))
            if ai_currency is not None
            else Decimal("0")
        )
        return OperatorRevenueDashboard(
            organization_id=organization_id,
            day=day_start.date().isoformat(),
            daily_prospects_discovered=count(
                "prospect_candidates",
                candidates.c.created_at >= day_start,
                candidates.c.created_at < day_end,
            ),
            qualified_prospects=count(
                "growth_prospects",
                prospects.c.status.in_(["qualified", "contacted", "replied", "customer"]),
            ),
            growth_opportunities=count("growth_opportunity_analyses"),
            gifts_ready=count(
                "growth_gifts", gifts.c.status.in_(["approved", "ready_for_delivery", "sent"])
            ),
            outreach_drafts_ready=count(
                "growth_outreach_drafts", drafts.c.status.in_(["human_review", "approved"])
            ),
            replies=count("sales_conversation_analyses"),
            positive_conversations=count(
                "sales_conversation_analyses", analyses.c.buying_signal.in_(["positive", "strong"])
            ),
            revenue_experiments=count(
                "revenue_experiments", experiments.c.status.in_(["draft", "active", "paused"])
            ),
            estimated_ai_cost=float(ai_cost),
            ai_cost_currency=ai_currency,
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
        run = GrowthBusinessResearchRun(
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
        )
        self.session.add(run)
        self.session.flush()
        add_to_outbox(
            self.session,
            BusinessEventEnvelope(
                event_type="growth.business_research_requested",
                actor=EventActor(actor_type="human", actor_id=str(actor_id)),
                source="growth",
                idempotency_key=f"growth-business-research:{run.id}",
                correlation_id=run.id,
                organization_id=payload.organization_id,
                payload={"run_id": str(run.id)},
            ),
        )
        return self._save(
            run,
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

    def _evidence_context(
        self,
        candidate_id: UUID,
        source_id: UUID,
        organization_id: UUID,
        allowed_types: set[str],
    ) -> None:
        candidate = scoped_growth_discovery(
            self.session, ProspectCandidate, candidate_id, organization_id
        )
        source = scoped_growth_discovery(
            self.session, ProspectDiscoverySource, source_id, organization_id
        )
        if source.source_type not in allowed_types:
            raise GrowthError("Evidence source type is not valid for this collector.")
        if source.collection_mode not in {
            "human_review",
            "controlled_import",
            "controlled_connector",
        }:
            raise GrowthError("Discovery source does not use a controlled collection mode.")
        if candidate.status == "new":
            candidate.status = "researching"
            self.session.add(candidate)

    def _ids(self, table_name: str, prospect_id: UUID) -> list[UUID]:
        table = Base.metadata.tables[table_name]
        return list(
            self.session.scalars(
                select(table.c.id)
                .where(table.c.prospect_id == prospect_id)
                .order_by(table.c.created_at)
            )
        )

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
