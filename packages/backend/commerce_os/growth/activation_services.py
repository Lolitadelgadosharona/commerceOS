from decimal import Decimal
from typing import Any, TypeVar, cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from commerce_os.growth.activation_models import (
    ExperimentFeedbackSignal,
    OfferExperiment,
    OfferExperimentOutcome,
    OutreachTrackingEvent,
    ProspectExperimentLink,
    RevenueExperiment,
)
from commerce_os.growth.activation_schemas import (
    FeedbackSignalCreate,
    FunnelMetric,
    OfferExperimentCreate,
    OfferMetric,
    OfferOutcomeCreate,
    OutreachEventCreate,
    ProspectAssignmentCreate,
    ProspectPromotionCreate,
    RevenueExperimentCreate,
    RevenueExperimentDashboard,
)
from commerce_os.growth.discovery_models import (
    GrowthBusinessResearchRun,
    ProspectCandidate,
    ProspectQualificationAssessment,
    ProspectResearchEvidence,
)
from commerce_os.growth.errors import GrowthError
from commerce_os.growth.industry_intelligence_models import (
    IndustryGrowthProfile,
    IndustryLearningSignal,
)
from commerce_os.growth.revenue_models import (
    GrowthOutreachDraft,
    GrowthProspect,
    GrowthProspectEvidence,
)
from commerce_os.shared.audit import record_audit_event
from commerce_os.shared.database import Base

EntityT = TypeVar("EntityT", bound=Base)
EXPERIMENT_TRANSITIONS = {
    "draft": {"active", "archived"},
    "active": {"paused", "completed", "archived"},
    "paused": {"active", "completed", "archived"},
    "completed": {"archived"},
    "archived": set(),
}
EVENT_RESULTS = {
    "draft_created": "pending",
    "approved": "pending",
    "sent_manually": "contacted",
    "reply_received": "replied",
    "follow_up_needed": "replied",
    "converted": "converted",
}


def scoped_activation(
    session: Session, model: type[EntityT], entity_id: UUID, organization_id: UUID
) -> EntityT:
    entity = session.get(model, entity_id)
    if entity is None or entity.organization_id != organization_id:  # type: ignore[attr-defined]
        raise GrowthError(
            "Revenue activation record was not found in this organization.", "not_found"
        )
    return entity


class RevenueActivationService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def promote_candidate(
        self, candidate: ProspectCandidate, payload: ProspectPromotionCreate, actor_id: UUID
    ) -> GrowthProspect:
        existing = self.session.scalar(
            select(GrowthProspect).where(
                GrowthProspect.organization_id == payload.organization_id,
                GrowthProspect.source_candidate_id == candidate.id,
            )
        )
        if existing is not None:
            return existing
        if candidate.status == "researching":
            completed_research = self.session.scalar(
                select(GrowthBusinessResearchRun)
                .where(
                    GrowthBusinessResearchRun.organization_id == payload.organization_id,
                    GrowthBusinessResearchRun.candidate_id == candidate.id,
                    GrowthBusinessResearchRun.status == "completed",
                )
                .order_by(GrowthBusinessResearchRun.created_at.desc())
            )
            latest_qualification = self.session.scalar(
                select(ProspectQualificationAssessment)
                .where(
                    ProspectQualificationAssessment.organization_id == payload.organization_id,
                    ProspectQualificationAssessment.candidate_id == candidate.id,
                )
                .order_by(ProspectQualificationAssessment.created_at.desc())
            )
            if (
                completed_research is not None
                and latest_qualification is not None
                and latest_qualification.score is not None
                and latest_qualification.score >= 70
            ):
                candidate.status = "qualified"
                self.session.add(candidate)
        if candidate.status != "qualified":
            raise GrowthError("Only qualified discovery candidates may enter revenue activation.")
        prospect = GrowthProspect(
            organization_id=payload.organization_id,
            business_name=candidate.business_name,
            website=candidate.website,
            email=payload.email,
            social_links=payload.social_links,
            location=candidate.location,
            industry=candidate.category,
            business_type=candidate.category,
            source="prospect_discovery",
            status="qualified",
            source_candidate_id=candidate.id,
        )
        self.session.add(prospect)
        self.session.flush()
        candidate_evidence = list(
            self.session.scalars(
                select(ProspectResearchEvidence).where(
                    ProspectResearchEvidence.organization_id == payload.organization_id,
                    ProspectResearchEvidence.candidate_id == candidate.id,
                )
            )
        )
        for evidence in candidate_evidence:
            self.session.add(
                GrowthProspectEvidence(
                    organization_id=payload.organization_id,
                    prospect_id=prospect.id,
                    evidence_type=evidence.evidence_type,
                    source_url=evidence.source_url,
                    observation=evidence.observation,
                    confidence=evidence.confidence,
                    collected_at=evidence.collected_at,
                )
            )
        return self._save(prospect, actor_id, "growthos.candidate.promoted")

    def create_experiment(
        self, payload: RevenueExperimentCreate, actor_id: UUID
    ) -> RevenueExperiment:
        self._organization(payload.organization_id)
        if payload.industry_profile_id is not None:
            scoped_activation(
                self.session,
                IndustryGrowthProfile,
                payload.industry_profile_id,
                payload.organization_id,
            )
        return self._save(
            RevenueExperiment(**payload.model_dump(), status="draft", created_by=actor_id),
            actor_id,
            "growthos.revenue_experiment.created",
        )

    def create_offer_experiment(
        self, payload: OfferExperimentCreate, actor_id: UUID
    ) -> OfferExperiment:
        experiment = scoped_activation(
            self.session, RevenueExperiment, payload.revenue_experiment_id, payload.organization_id
        )
        if experiment.status in {"completed", "archived"}:
            raise GrowthError("Terminal revenue experiments cannot accept offer variants.")
        return self._save(
            OfferExperiment(**payload.model_dump(), status="draft"),
            actor_id,
            "growthos.offer_experiment.created",
        )

    def record_offer_outcome(
        self, payload: OfferOutcomeCreate, actor_id: UUID
    ) -> OfferExperimentOutcome:
        scoped_activation(
            self.session, OfferExperiment, payload.offer_experiment_id, payload.organization_id
        )
        scoped_activation(
            self.session, GrowthProspect, payload.prospect_id, payload.organization_id
        )
        if payload.positive_reply and not payload.replied:
            raise GrowthError("A positive reply requires a recorded reply.")
        if payload.converted and not payload.replied:
            raise GrowthError("A conversion requires a recorded customer reply.")
        if payload.revenue_observation_id is not None:
            table = Base.metadata.tables["revenue_observations"]
            row = self.session.execute(
                table.select().where(
                    table.c.id == payload.revenue_observation_id,
                    table.c.organization_id == payload.organization_id,
                )
            ).first()
            if row is None:
                raise GrowthError(
                    "Revenue outcome must reference Finance truth in this organization."
                )
        return self._save(
            OfferExperimentOutcome(**payload.model_dump()),
            actor_id,
            "growthos.offer_outcome.recorded",
        )

    def create_feedback_signal(
        self, payload: FeedbackSignalCreate, actor_id: UUID
    ) -> ExperimentFeedbackSignal:
        scoped_activation(
            self.session, RevenueExperiment, payload.revenue_experiment_id, payload.organization_id
        )
        if payload.offer_experiment_id is not None:
            offer = scoped_activation(
                self.session, OfferExperiment, payload.offer_experiment_id, payload.organization_id
            )
            if offer.revenue_experiment_id != payload.revenue_experiment_id:
                raise GrowthError("Feedback offer must belong to the selected revenue experiment.")
        if payload.industry_learning_signal_id is not None:
            scoped_activation(
                self.session,
                IndustryLearningSignal,
                payload.industry_learning_signal_id,
                payload.organization_id,
            )
        return self._save(
            ExperimentFeedbackSignal(**payload.model_dump()),
            actor_id,
            "growthos.experiment_feedback.created",
        )

    def transition_experiment(
        self, entity: RevenueExperiment, status: str, actor_id: UUID
    ) -> RevenueExperiment:
        if status not in EXPERIMENT_TRANSITIONS[entity.status]:
            raise GrowthError(
                f"Revenue experiment cannot transition from {entity.status} to {status}."
            )
        entity.status = status
        return self._save(entity, actor_id, f"growthos.revenue_experiment.{status}")

    def assign_prospect(
        self, payload: ProspectAssignmentCreate, actor_id: UUID
    ) -> ProspectExperimentLink:
        experiment = scoped_activation(
            self.session, RevenueExperiment, payload.experiment_id, payload.organization_id
        )
        prospect = scoped_activation(
            self.session, GrowthProspect, payload.prospect_id, payload.organization_id
        )
        if experiment.status in {"completed", "archived"}:
            raise GrowthError("Terminal revenue experiments cannot accept prospects.")
        if prospect.status not in {"qualified", "contacted", "replied", "customer"}:
            raise GrowthError("Revenue experiments require a qualified prospect.")
        existing = self.session.scalar(
            select(ProspectExperimentLink).where(
                ProspectExperimentLink.organization_id == payload.organization_id,
                ProspectExperimentLink.experiment_id == payload.experiment_id,
                ProspectExperimentLink.prospect_id == payload.prospect_id,
            )
        )
        if existing is not None:
            return existing
        return self._save(
            ProspectExperimentLink(**payload.model_dump(), result_status="pending"),
            actor_id,
            "growthos.experiment_prospect.assigned",
        )

    def record_event(self, payload: OutreachEventCreate, actor_id: UUID) -> OutreachTrackingEvent:
        link = scoped_activation(
            self.session,
            ProspectExperimentLink,
            payload.prospect_experiment_link_id,
            payload.organization_id,
        )
        draft = None
        if payload.outreach_draft_id is not None:
            draft = scoped_activation(
                self.session,
                GrowthOutreachDraft,
                payload.outreach_draft_id,
                payload.organization_id,
            )
            if draft.prospect_id != link.prospect_id:
                raise GrowthError("Outreach event draft must belong to the assigned prospect.")
        if payload.event_type in {"approved", "sent_manually"} and draft is None:
            raise GrowthError("Approval and manual-send events require an outreach draft.")
        if payload.event_type == "approved" and draft is not None and draft.status != "approved":
            raise GrowthError("Approval event requires a Governance-approved outreach draft.")
        if (
            payload.event_type == "sent_manually"
            and draft is not None
            and (draft.status != "sent" or draft.approval_request_id is None)
        ):
            raise GrowthError("Manual send may only be recorded after human approval.")
        values = payload.model_dump(exclude={"metadata"})
        event = OutreachTrackingEvent(
            **values, recorded_by=actor_id, event_metadata=payload.metadata
        )
        result_status = EVENT_RESULTS[payload.event_type]
        if payload.event_type == "reply_received":
            outcome = payload.metadata.get("outcome")
            if outcome in {"positive", "negative"}:
                result_status = outcome
        link.result_status = result_status
        self.session.add(link)
        return self._save(event, actor_id, f"growthos.outreach_event.{payload.event_type}")

    def experiment_dashboard(
        self, experiment_id: UUID, organization_id: UUID
    ) -> RevenueExperimentDashboard:
        scoped_activation(self.session, RevenueExperiment, experiment_id, organization_id)
        links = list(
            self.session.scalars(
                select(ProspectExperimentLink).where(
                    ProspectExperimentLink.organization_id == organization_id,
                    ProspectExperimentLink.experiment_id == experiment_id,
                )
            )
        )
        prospect_ids = [item.prospect_id for item in links]
        prospects = (
            list(
                self.session.scalars(
                    select(GrowthProspect).where(GrowthProspect.id.in_(prospect_ids))
                )
            )
            if prospect_ids
            else []
        )
        gifts_table = Base.metadata.tables["growth_gifts"]
        drafts_table = Base.metadata.tables["growth_outreach_drafts"]
        gifts_ready = self._distinct_count(
            gifts_table,
            gifts_table.c.prospect_id,
            gifts_table.c.organization_id == organization_id,
            gifts_table.c.prospect_id.in_(prospect_ids),
            gifts_table.c.status.in_(
                [
                    "approved",
                    "ready_for_delivery",
                    "delivered",
                    "sent",
                    "customer_response",
                    "converted",
                ]
            ),
        )
        outreach_approved = self._distinct_count(
            drafts_table,
            drafts_table.c.prospect_id,
            drafts_table.c.organization_id == organization_id,
            drafts_table.c.prospect_id.in_(prospect_ids),
            drafts_table.c.status.in_(["approved", "sent"]),
        )
        events = (
            list(
                self.session.scalars(
                    select(OutreachTrackingEvent).where(
                        OutreachTrackingEvent.organization_id == organization_id,
                        OutreachTrackingEvent.prospect_experiment_link_id.in_(
                            [item.id for item in links]
                        ),
                    )
                )
            )
            if links
            else []
        )
        sent = len(
            {
                item.prospect_experiment_link_id
                for item in events
                if item.event_type == "sent_manually"
            }
        )
        replies = len(
            {
                item.prospect_experiment_link_id
                for item in events
                if item.event_type == "reply_received"
            }
        )
        outcomes = list(
            self.session.scalars(
                select(OfferExperimentOutcome)
                .join(
                    OfferExperiment,
                    OfferExperiment.id == OfferExperimentOutcome.offer_experiment_id,
                )
                .where(
                    OfferExperimentOutcome.organization_id == organization_id,
                    OfferExperiment.revenue_experiment_id == experiment_id,
                )
            )
        )
        positive = len({item.prospect_id for item in outcomes if item.positive_reply})
        customers = len({item.id for item in prospects if item.status == "customer"})
        stage_values = [
            ("prospects", len(prospects)),
            (
                "qualified",
                len(
                    [
                        item
                        for item in prospects
                        if item.status in {"qualified", "contacted", "replied", "customer"}
                    ]
                ),
            ),
            ("gift_ready", gifts_ready),
            ("outreach_approved", outreach_approved),
            ("outreach_sent", sent),
            ("replies", replies),
            ("positive_replies", positive),
            ("customers", customers),
        ]
        funnel = [
            FunnelMetric(
                name=name,
                count=value,
                conversion_rate=None
                if index == 0 or stage_values[index - 1][1] == 0
                else round(value / stage_values[index - 1][1], 4),
            )
            for index, (name, value) in enumerate(stage_values)
        ]
        revenue_by_id, currency = self._revenue_values(
            organization_id,
            [item.revenue_observation_id for item in outcomes if item.revenue_observation_id],
        )
        offers = list(
            self.session.scalars(
                select(OfferExperiment).where(
                    OfferExperiment.organization_id == organization_id,
                    OfferExperiment.revenue_experiment_id == experiment_id,
                )
            )
        )
        offer_metrics = []
        for offer in offers:
            offer_outcomes = [item for item in outcomes if item.offer_experiment_id == offer.id]
            assigned = len(offer_outcomes)
            offer_revenue = sum(
                (
                    revenue_by_id.get(item.revenue_observation_id, Decimal("0"))
                    for item in offer_outcomes
                    if item.revenue_observation_id is not None
                ),
                Decimal("0"),
            )
            offer_metrics.append(
                OfferMetric(
                    offer_experiment_id=offer.id,
                    offer_type=offer.offer_type,
                    assigned=assigned,
                    response_rate=None
                    if assigned == 0
                    else round(sum(item.replied for item in offer_outcomes) / assigned, 4),
                    conversion_rate=None
                    if assigned == 0
                    else round(sum(item.converted for item in offer_outcomes) / assigned, 4),
                    revenue=offer_revenue,
                    currency=currency,
                )
            )
        ai_cost, ai_currency = self._ai_cost(experiment_id, organization_id)
        return RevenueExperimentDashboard(
            organization_id=organization_id,
            experiment_id=experiment_id,
            funnel=funnel,
            offers=offer_metrics,
            revenue=sum(revenue_by_id.values(), Decimal("0")),
            currency=currency,
            estimated_ai_cost=ai_cost,
            ai_cost_currency=ai_currency,
        )

    def _distinct_count(self, table: Any, column: Any, *criteria: Any) -> int:
        return int(
            self.session.scalar(
                select(func.count(func.distinct(column))).select_from(table).where(*criteria)
            )
            or 0
        )

    def _revenue_values(
        self, organization_id: UUID, observation_ids: list[UUID]
    ) -> tuple[dict[UUID, Decimal], str | None]:
        if not observation_ids:
            return {}, None
        table = Base.metadata.tables["revenue_observations"]
        rows = list(
            self.session.execute(
                select(table.c.id, table.c.amount, table.c.currency).where(
                    table.c.organization_id == organization_id,
                    table.c.id.in_(observation_ids),
                )
            )
        )
        currencies = {row.currency for row in rows}
        if len(currencies) != 1:
            return {}, None
        return {row.id: Decimal(row.amount) for row in rows}, next(iter(currencies))

    def _ai_cost(self, experiment_id: UUID, organization_id: UUID) -> tuple[Decimal, str | None]:
        requests = Base.metadata.tables["ai_requests"]
        costs = Base.metadata.tables["ai_cost_observations"]
        rows = list(
            self.session.execute(
                select(costs.c.estimated_cost, costs.c.currency)
                .select_from(costs.join(requests, costs.c.related_request_id == requests.c.id))
                .where(
                    costs.c.organization_id == organization_id,
                    requests.c.context_type == "revenue_experiment",
                    requests.c.context_reference == str(experiment_id),
                )
            )
        )
        currencies = {row.currency for row in rows}
        if not rows:
            return Decimal("0"), None
        if len(currencies) != 1:
            return Decimal("0"), None
        return sum((Decimal(row.estimated_cost) for row in rows), Decimal("0")), next(
            iter(currencies)
        )

    def _organization(self, organization_id: UUID) -> None:
        table = Base.metadata.tables["organizations"]
        if self.session.scalar(select(table.c.id).where(table.c.id == organization_id)) is None:
            raise GrowthError("Organization was not found.", "not_found")

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
