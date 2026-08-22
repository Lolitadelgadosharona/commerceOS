from typing import Any, TypeVar, cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from commerce_os.growth.activation_models import (
    OutreachTrackingEvent,
    ProspectExperimentLink,
    RevenueExperiment,
)
from commerce_os.growth.activation_schemas import (
    OutreachEventCreate,
    ProspectAssignmentCreate,
    ProspectPromotionCreate,
    RevenueExperimentCreate,
)
from commerce_os.growth.discovery_models import ProspectCandidate
from commerce_os.growth.errors import GrowthError
from commerce_os.growth.revenue_models import GrowthOutreachDraft, GrowthProspect
from commerce_os.shared.audit import record_audit_event
from commerce_os.shared.database import Base

EntityT = TypeVar("EntityT", bound=Base)
EXPERIMENT_TRANSITIONS = {
    "draft": {"active", "archived"},
    "active": {"completed", "archived"},
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
        if candidate.status != "qualified":
            raise GrowthError("Only qualified discovery candidates may enter revenue activation.")
        return self._save(
            GrowthProspect(
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
            ),
            actor_id,
            "growthos.candidate.promoted",
        )

    def create_experiment(
        self, payload: RevenueExperimentCreate, actor_id: UUID
    ) -> RevenueExperiment:
        self._organization(payload.organization_id)
        return self._save(
            RevenueExperiment(**payload.model_dump(), status="draft", created_by=actor_id),
            actor_id,
            "growthos.revenue_experiment.created",
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
