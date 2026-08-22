from typing import Any, TypeVar, cast
from uuid import UUID

from sqlalchemy.orm import Session

from commerce_os.growth.errors import GrowthError
from commerce_os.growth.industry_intelligence_models import (
    GrowthGEOAssessment,
    GrowthServiceRecommendation,
    IndustryGrowthEvidence,
    IndustryGrowthPattern,
    IndustryGrowthProfile,
    IndustryLearningSignal,
)
from commerce_os.growth.industry_intelligence_schemas import (
    GEOAssessmentCreate,
    IndustryEvidenceCreate,
    IndustryLearningSignalCreate,
    IndustryPatternCreate,
    IndustryProfileCreate,
    ServiceRecommendationCreate,
)
from commerce_os.growth.revenue_models import (
    GrowthOpportunityAnalysis,
    GrowthProspect,
    GrowthProspectEvidence,
)
from commerce_os.growth.revenue_services import scoped_revenue
from commerce_os.shared.audit import record_audit_event
from commerce_os.shared.database import Base

EntityT = TypeVar("EntityT", bound=Base)


class IndustryIntelligenceService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_profile(
        self, payload: IndustryProfileCreate, actor_id: UUID
    ) -> IndustryGrowthProfile:
        self._organization(payload.organization_id)
        return self._save(
            IndustryGrowthProfile(**payload.model_dump(), status="draft"),
            actor_id,
            "growthos.industry_profile.created",
        )

    def create_evidence(
        self, payload: IndustryEvidenceCreate, actor_id: UUID
    ) -> IndustryGrowthEvidence:
        self._scoped(IndustryGrowthProfile, payload.industry_profile_id, payload.organization_id)
        return self._save(
            IndustryGrowthEvidence(**payload.model_dump()),
            actor_id,
            "growthos.industry_evidence.appended",
        )

    def create_pattern(
        self, payload: IndustryPatternCreate, actor_id: UUID
    ) -> IndustryGrowthPattern:
        self._scoped(IndustryGrowthProfile, payload.industry_profile_id, payload.organization_id)
        self._industry_evidence(
            payload.evidence_references, payload.industry_profile_id, payload.organization_id
        )
        values = payload.model_dump()
        values["evidence_references"] = [str(item) for item in payload.evidence_references]
        return self._save(
            IndustryGrowthPattern(**values, status="draft"),
            actor_id,
            "growthos.industry_pattern.created",
        )

    def create_geo_assessment(
        self, payload: GEOAssessmentCreate, actor_id: UUID
    ) -> GrowthGEOAssessment:
        scoped_revenue(self.session, GrowthProspect, payload.prospect_id, payload.organization_id)
        if payload.industry_profile_id is not None:
            self._scoped(
                IndustryGrowthProfile, payload.industry_profile_id, payload.organization_id
            )
        self._prospect_evidence(
            payload.evidence_references, payload.prospect_id, payload.organization_id
        )
        values = payload.model_dump()
        values["evidence_references"] = [str(item) for item in payload.evidence_references]
        return self._save(
            GrowthGEOAssessment(**values), actor_id, "growthos.geo_assessment.created"
        )

    def create_service_recommendation(
        self, payload: ServiceRecommendationCreate, actor_id: UUID
    ) -> GrowthServiceRecommendation:
        scoped_revenue(self.session, GrowthProspect, payload.prospect_id, payload.organization_id)
        if payload.industry_profile_id is not None:
            self._scoped(
                IndustryGrowthProfile, payload.industry_profile_id, payload.organization_id
            )
        if payload.opportunity_id is not None:
            opportunity = scoped_revenue(
                self.session,
                GrowthOpportunityAnalysis,
                payload.opportunity_id,
                payload.organization_id,
            )
            if opportunity.prospect_id != payload.prospect_id:
                raise GrowthError("Service opportunity must belong to the selected prospect.")
        self._prospect_evidence(
            payload.evidence_references, payload.prospect_id, payload.organization_id
        )
        values = payload.model_dump()
        values["evidence_references"] = [str(item) for item in payload.evidence_references]
        return self._save(
            GrowthServiceRecommendation(**values, status="draft"),
            actor_id,
            "growthos.service_recommendation.created",
        )

    def create_learning_signal(
        self, payload: IndustryLearningSignalCreate, actor_id: UUID
    ) -> IndustryLearningSignal:
        self._scoped(IndustryGrowthProfile, payload.industry_profile_id, payload.organization_id)
        self._industry_evidence(
            payload.evidence_references, payload.industry_profile_id, payload.organization_id
        )
        values = payload.model_dump()
        values["evidence_references"] = [str(item) for item in payload.evidence_references]
        return self._save(
            IndustryLearningSignal(**values, status="draft"),
            actor_id,
            "growthos.industry_learning_signal.created",
        )

    def _industry_evidence(self, ids: list[UUID], profile_id: UUID, organization_id: UUID) -> None:
        for evidence_id in ids:
            evidence = self._scoped(IndustryGrowthEvidence, evidence_id, organization_id)
            if evidence.industry_profile_id != profile_id:
                raise GrowthError("Industry evidence must belong to the selected profile.")

    def _prospect_evidence(self, ids: list[UUID], prospect_id: UUID, organization_id: UUID) -> None:
        for evidence_id in ids:
            evidence = scoped_revenue(
                self.session, GrowthProspectEvidence, evidence_id, organization_id
            )
            if evidence.prospect_id != prospect_id:
                raise GrowthError("Growth evidence must belong to the selected prospect.")

    def _organization(self, organization_id: UUID) -> None:
        table = Base.metadata.tables["organizations"]
        if (
            self.session.execute(table.select().where(table.c.id == organization_id)).first()
            is None
        ):
            raise GrowthError("Organization was not found.", "not_found")

    def _scoped(self, model: type[EntityT], entity_id: UUID, organization_id: UUID) -> EntityT:
        entity = self.session.get(model, entity_id)
        if entity is None or entity.organization_id != organization_id:  # type: ignore[attr-defined]
            raise GrowthError(
                "Industry intelligence record was not found in this organization.", "not_found"
            )
        return entity

    def _save(self, entity: EntityT, actor_id: UUID, action: str) -> EntityT:
        self.session.add(entity)
        self.session.flush()
        item = cast(Any, entity)
        record_audit_event(
            self.session,
            organization_id=item.organization_id,
            actor_type="human",
            actor_id=actor_id,
            action=action,
            entity_type=item.__tablename__,
            entity_id=cast(UUID, item.id),
            metadata={"result": "success", "external_execution": "none"},
        )
        self.session.commit()
        self.session.refresh(entity)
        return entity
