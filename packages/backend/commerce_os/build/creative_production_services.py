from typing import Any, TypeVar, cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from commerce_os.ai_runtime.models import AIRequest
from commerce_os.build.creative_asset_models import CreativeAsset
from commerce_os.build.creative_generation_models import CreativeQualityReview
from commerce_os.build.creative_production_models import (
    CreativeProductionAIProvenance,
    CreativeProductionRequest,
    CreativeProductionWork,
)
from commerce_os.build.creative_production_schemas import (
    CreativeAIProvenanceCreate,
    CreativeProductionRequestCreate,
    CreativeProductionWorkCreate,
    CreativeQualityReviewCreate,
    ProductionArtifactCreate,
)
from commerce_os.build.errors import BuildScopeError, BuildStateError
from commerce_os.shared.audit import record_audit_event
from commerce_os.shared.database import Base

EntityT = TypeVar("EntityT", bound=Base)
REQUEST_TRANSITIONS = {
    "draft": {"submitted", "cancelled"},
    "submitted": {"review", "cancelled"},
    "review": {"approved", "cancelled"},
    "approved": set(),
    "cancelled": set(),
}
ALLOWED_AI_OUTPUTS = {"analysis", "draft", "candidate", "classification"}


def scoped_production(
    session: Session, model: type[EntityT], entity_id: UUID, organization_id: UUID
) -> EntityT:
    entity = session.get(model, entity_id)
    if entity is None or entity.organization_id != organization_id:  # type: ignore[attr-defined]
        raise BuildScopeError("Creative production record was not found in this organization.")
    return entity


class CreativeProductionService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_request(
        self, payload: CreativeProductionRequestCreate, actor_id: UUID
    ) -> CreativeProductionRequest:
        self._reference("projects", payload.project_id, payload.organization_id, "Project")
        self._reference(
            "creative_briefs", payload.creative_brief_id, payload.organization_id, "Creative brief"
        )
        if payload.approval_request_id is not None:
            self._reference(
                "approval_requests",
                payload.approval_request_id,
                payload.organization_id,
                "Approval request",
            )
        return self._save_audited(
            CreativeProductionRequest(
                **payload.model_dump(),
                requested_by=actor_id,
                status="draft",
                approval_state="pending",
            ),
            actor_id,
            "creative.production_request.created",
        )

    def transition_request(
        self,
        request: CreativeProductionRequest,
        status: str,
        actor_id: UUID,
        approval_request_id: UUID | None = None,
    ) -> CreativeProductionRequest:
        if status not in REQUEST_TRANSITIONS[request.status]:
            raise BuildStateError(
                f"Production request cannot transition from {request.status} to {status}."
            )
        if approval_request_id is not None:
            request.approval_request_id = approval_request_id
        if status == "approved":
            if not self._has_approved_governance_request(request):
                raise BuildStateError("Governance approval is required before approval.")
            request.approval_state = "approved"
        elif status == "cancelled":
            request.approval_state = "cancelled"
        request.status = status
        return self._save_audited(request, actor_id, f"creative.production_request.{status}")

    def create_work(
        self, payload: CreativeProductionWorkCreate, actor_id: UUID
    ) -> CreativeProductionWork:
        request = scoped_production(
            self.session,
            CreativeProductionRequest,
            payload.production_request_id,
            payload.organization_id,
        )
        if request.status == "cancelled":
            raise BuildStateError("Cancelled production requests cannot accept work items.")
        self._reject_execution_metadata(payload.content_metadata)
        return self._save_audited(
            CreativeProductionWork(**payload.model_dump(), status="draft"),
            actor_id,
            "creative.production_work.created",
        )

    def link_ai_provenance(
        self, payload: CreativeAIProvenanceCreate, actor_id: UUID
    ) -> CreativeProductionAIProvenance:
        request = scoped_production(
            self.session,
            CreativeProductionRequest,
            payload.production_request_id,
            payload.organization_id,
        )
        work = scoped_production(
            self.session,
            CreativeProductionWork,
            payload.production_work_id,
            payload.organization_id,
        )
        ai_request = scoped_production(
            self.session, AIRequest, payload.ai_request_id, payload.organization_id
        )
        if work.production_request_id != request.id:
            raise BuildScopeError("Work item does not belong to the production request.")
        if payload.output_classification not in ALLOWED_AI_OUTPUTS:
            raise BuildStateError("AI output classification has execution authority.")
        if (
            ai_request.output_classification is not None
            and str(ai_request.output_classification) != payload.output_classification
        ):
            raise BuildStateError("AI provenance classification must match the AI request output.")
        self._reject_execution_metadata(payload.output_metadata)
        return self._save_audited(
            CreativeProductionAIProvenance(**payload.model_dump()),
            actor_id,
            "creative.ai_provenance.linked",
        )

    def create_artifact(self, payload: ProductionArtifactCreate, actor_id: UUID) -> CreativeAsset:
        request = scoped_production(
            self.session,
            CreativeProductionRequest,
            payload.production_request_id,
            payload.organization_id,
        )
        self._reference("products", payload.product_id, payload.organization_id, "Product")
        if request.status not in {"review", "approved"}:
            raise BuildStateError(
                "Artifacts require a production request in review or approved state."
            )
        self._reject_execution_metadata(payload.metadata)
        values = payload.model_dump(exclude={"metadata"})
        return self._save_audited(
            CreativeAsset(
                **values,
                asset_metadata=payload.metadata,
                status="draft",
                approval_status="pending",
                review_status="unreviewed",
                quality_score=None,
            ),
            actor_id,
            "creative.production_artifact.created",
        )

    def review_quality(
        self, payload: CreativeQualityReviewCreate, actor_id: UUID
    ) -> CreativeQualityReview:
        asset = scoped_production(
            self.session, CreativeAsset, payload.asset_id, payload.organization_id
        )
        scores = [
            payload.brand_consistency_score,
            payload.claim_safety_score,
            payload.product_accuracy_score,
            payload.channel_suitability_score,
            payload.customer_relevance_score,
        ]
        overall = round(sum(scores) / len(scores), 2)
        asset.quality_score = overall
        asset.review_status = "in_review"
        review = CreativeQualityReview(
            **payload.model_dump(),
            review_type="production_quality_gate",
            score=overall,
            review_status="completed",
            reviewed_by=actor_id,
        )
        self.session.add(asset)
        return self._save_audited(review, actor_id, "creative.quality_review.completed")

    def transition_artifact(
        self, asset: CreativeAsset, review_status: str, actor_id: UUID
    ) -> CreativeAsset:
        if asset.production_request_id is None:
            raise BuildStateError("Only production artifacts use the production review lifecycle.")
        request = scoped_production(
            self.session,
            CreativeProductionRequest,
            asset.production_request_id,
            asset.organization_id,
        )
        if review_status in {"approved", "ready_for_distribution"}:
            if request.status != "approved" or request.approval_state != "approved":
                raise BuildStateError("Governance-approved production is required.")
            if asset.quality_score is None:
                raise BuildStateError("A completed quality review is required.")
            asset.approval_status = "approved"
        if review_status == "ready_for_distribution" and asset.review_status != "approved":
            raise BuildStateError("Artifact must be approved before distribution readiness.")
        asset.review_status = review_status
        return self._save_audited(asset, actor_id, f"creative.production_artifact.{review_status}")

    def _has_approved_governance_request(self, request: CreativeProductionRequest) -> bool:
        if request.approval_request_id is None:
            return False
        approvals = Base.metadata.tables["approval_requests"]
        approval = self.session.execute(
            select(
                approvals.c.status,
                approvals.c.object_type,
                approvals.c.object_id,
                approvals.c.requested_action,
            ).where(
                approvals.c.id == request.approval_request_id,
                approvals.c.organization_id == request.organization_id,
            )
        ).one_or_none()
        return bool(
            approval
            and approval.status == "approved"
            and approval.object_type == "creative_production_request"
            and approval.object_id == request.id
            and approval.requested_action == "approve_creative_production"
        )

    def _reference(
        self, table_name: str, reference_id: UUID, organization_id: UUID, label: str
    ) -> None:
        table = Base.metadata.tables[table_name]
        found = self.session.scalar(
            select(table.c.id).where(
                table.c.id == reference_id, table.c.organization_id == organization_id
            )
        )
        if found is None:
            raise BuildScopeError(f"{label} was not found in this organization.")

    @classmethod
    def _reject_execution_metadata(cls, value: Any) -> None:
        forbidden = {"publish", "spend", "payment", "approval", "execute", "provider_call"}
        if isinstance(value, dict):
            for key, item in value.items():
                if str(key).lower().replace("-", "_") in forbidden:
                    raise BuildStateError("Creative metadata cannot grant execution authority.")
                cls._reject_execution_metadata(item)
        elif isinstance(value, list):
            for item in value:
                cls._reject_execution_metadata(item)

    def _save_audited(self, entity: EntityT, actor_id: UUID, action: str) -> EntityT:
        self.session.add(entity)
        self.session.flush()
        record_audit_event(
            self.session,
            organization_id=entity.organization_id,  # type: ignore[attr-defined]
            actor_type="human",
            actor_id=actor_id,
            action=action,
            entity_type=entity.__tablename__,
            entity_id=cast(UUID, entity.id),  # type: ignore[attr-defined]
            metadata={"result": "success", "execution": "none"},
        )
        self.session.commit()
        self.session.refresh(entity)
        return entity
