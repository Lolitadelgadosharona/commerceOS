from decimal import ROUND_HALF_UP, Decimal
from typing import Any, TypeVar, cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from commerce_os.ai_runtime.errors import AIRuntimeScopeError, AIRuntimeValidationError
from commerce_os.ai_runtime.models import (
    AICostObservation,
    AIModelCapability,
    AIOutputClassification,
    AIProvider,
    AIRequest,
    AIRequestStatus,
    PromptEvaluation,
    PromptPurpose,
    PromptTemplate,
    PromptVersion,
)
from commerce_os.ai_runtime.schemas import (
    AIRequestCreate,
    AIRequestTransition,
    CapabilityCreate,
    CostObservationCreate,
    PromptEvaluationCreate,
    PromptPurposeCreate,
    PromptTemplateCreate,
    PromptVersionCreate,
    ProviderCreate,
)
from commerce_os.governance.audit import AuditService
from commerce_os.governance.models import ApprovalRequest, ApprovalStatus
from commerce_os.shared.database import Base
from commerce_os.shared.scope import reference_belongs_to_organization

EntityT = TypeVar("EntityT", bound=Base)
REQUEST_TRANSITIONS = {
    "draft": {"submitted", "cancelled"},
    "submitted": {"approved_if_required", "ready", "cancelled"},
    "approved_if_required": {"ready", "cancelled"},
    "ready": {"completed", "failed", "cancelled"},
    "completed": set(),
    "failed": set(),
    "cancelled": set(),
}


class AIRuntimeService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_provider(self, payload: ProviderCreate, actor_id: UUID) -> AIProvider:
        self._organization(payload.organization_id)
        return self._save_audited(
            AIProvider(**payload.model_dump()), actor_id, "ai.provider.created"
        )

    def create_capability(self, payload: CapabilityCreate, actor_id: UUID) -> AIModelCapability:
        provider = self._scoped(
            AIProvider, payload.provider_id, payload.organization_id, "Provider"
        )
        if provider.availability_state == "disabled" and payload.available:
            raise AIRuntimeValidationError("A disabled provider cannot expose an available model.")
        return self._save_audited(
            AIModelCapability(**payload.model_dump()), actor_id, "ai.capability.created"
        )

    def create_request(self, payload: AIRequestCreate, actor_id: UUID) -> AIRequest:
        self._reference("users", actor_id, payload.organization_id, "Requester")
        if payload.capability_id is not None:
            self._scoped(
                AIModelCapability, payload.capability_id, payload.organization_id, "Capability"
            )
        if payload.approval_request_id is not None:
            self._scoped(
                ApprovalRequest, payload.approval_request_id, payload.organization_id, "Approval"
            )
        entity = AIRequest(
            **payload.model_dump(),
            requester_id=actor_id,
            status=AIRequestStatus.DRAFT,
            output_classification=None,
            output_metadata={},
            failure_reason=None,
        )
        return self._save_audited(entity, actor_id, "ai.request.created")

    def transition_request(
        self, request_id: UUID, payload: AIRequestTransition, actor_id: UUID
    ) -> AIRequest:
        entity = self._scoped(AIRequest, request_id, payload.organization_id, "AI request")
        if payload.status not in REQUEST_TRANSITIONS[str(entity.status)]:
            raise AIRuntimeValidationError(
                f"AI request cannot transition from {entity.status} to {payload.status}."
            )
        if payload.status == "approved_if_required":
            approval = self._approved_request(entity)
            if approval is None:
                raise AIRuntimeValidationError("An approved Governance request is required.")
        if (
            payload.status == "ready"
            and entity.approval_request_id is not None
            and self._approved_request(entity) is None
        ):
            raise AIRuntimeValidationError("Governance approval is required before ready state.")
        if payload.status == "ready":
            if entity.capability_id is None:
                raise AIRuntimeValidationError("Ready AI requests require a selected capability.")
            capability = self._scoped(
                AIModelCapability, entity.capability_id, entity.organization_id, "Capability"
            )
            provider = self._scoped(
                AIProvider, capability.provider_id, entity.organization_id, "Provider"
            )
            if not capability.available or provider.availability_state != "available":
                raise AIRuntimeValidationError("Selected provider capability is unavailable.")
        if payload.status == "completed" and payload.output_classification is None:
            raise AIRuntimeValidationError(
                "Completed AI requests require an allowed output classification."
            )
        entity.status = AIRequestStatus(payload.status)
        entity.output_classification = (
            AIOutputClassification(payload.output_classification)
            if payload.output_classification is not None
            else None
        )
        entity.output_metadata = payload.output_metadata
        entity.failure_reason = payload.failure_reason
        return self._save_audited(entity, actor_id, f"ai.request.{payload.status}")

    def create_purpose(self, payload: PromptPurposeCreate, actor_id: UUID) -> PromptPurpose:
        self._organization(payload.organization_id)
        return self._save_audited(
            PromptPurpose(**payload.model_dump()), actor_id, "ai.prompt_purpose.created"
        )

    def create_template(self, payload: PromptTemplateCreate, actor_id: UUID) -> PromptTemplate:
        self._scoped(PromptPurpose, payload.purpose_id, payload.organization_id, "Prompt purpose")
        return self._save_audited(
            PromptTemplate(**payload.model_dump(), owner_id=actor_id),
            actor_id,
            "ai.prompt_template.created",
        )

    def create_version(self, payload: PromptVersionCreate, actor_id: UUID) -> PromptVersion:
        self._scoped(
            PromptTemplate, payload.template_id, payload.organization_id, "Prompt template"
        )
        current = self.session.scalar(
            select(func.max(PromptVersion.version_number)).where(
                PromptVersion.template_id == payload.template_id
            )
        )
        return self._save_audited(
            PromptVersion(
                **payload.model_dump(), version_number=(current or 0) + 1, created_by=actor_id
            ),
            actor_id,
            "ai.prompt_version.created",
        )

    def evaluate_prompt(self, payload: PromptEvaluationCreate, actor_id: UUID) -> PromptEvaluation:
        self._scoped(
            PromptVersion, payload.prompt_version_id, payload.organization_id, "Prompt version"
        )
        return self._save_audited(
            PromptEvaluation(**payload.model_dump(), evaluator_id=actor_id),
            actor_id,
            "ai.prompt_evaluated",
        )

    def observe_cost(self, payload: CostObservationCreate, actor_id: UUID) -> AICostObservation:
        provider = self._scoped(
            AIProvider, payload.provider_id, payload.organization_id, "Provider"
        )
        capability = self._scoped(
            AIModelCapability, payload.capability_id, payload.organization_id, "Capability"
        )
        if capability.provider_id != provider.id:
            raise AIRuntimeValidationError("Capability does not belong to the selected provider.")
        if payload.project_id is not None:
            self._reference("projects", payload.project_id, payload.organization_id, "Project")
        if payload.related_request_id is not None:
            self._scoped(
                AIRequest, payload.related_request_id, payload.organization_id, "AI request"
            )
        values = payload.model_dump()
        values["usage_quantity"] = self._decimal(payload.usage_quantity)
        values["estimated_cost"] = self._decimal(payload.estimated_cost)
        return self._save_audited(
            AICostObservation(**values), actor_id, "ai.cost_observation.created"
        )

    def _approved_request(self, entity: AIRequest) -> ApprovalRequest | None:
        if entity.approval_request_id is None:
            return None
        approval = self.session.get(ApprovalRequest, entity.approval_request_id)
        if (
            approval is None
            or approval.organization_id != entity.organization_id
            or approval.status != ApprovalStatus.APPROVED
        ):
            return None
        return approval

    def _scoped(
        self, model: type[EntityT], entity_id: UUID, organization_id: UUID, label: str
    ) -> EntityT:
        entity = self.session.get(model, entity_id)
        if entity is None or entity.organization_id != organization_id:  # type: ignore[attr-defined]
            raise AIRuntimeScopeError(f"{label} was not found in this organization.")
        return entity

    def _reference(self, table: str, entity_id: UUID, organization_id: UUID, label: str) -> None:
        if not reference_belongs_to_organization(
            self.session,
            table_name=table,
            reference_id=entity_id,
            organization_id=organization_id,
        ):
            raise AIRuntimeScopeError(f"{label} was not found in this organization.")

    def _organization(self, organization_id: UUID) -> None:
        organizations = Base.metadata.tables["organizations"]
        exists = self.session.scalar(
            select(organizations.c.id).where(organizations.c.id == organization_id)
        )
        if exists is None:
            raise AIRuntimeScopeError("Organization was not found.")

    @staticmethod
    def _decimal(value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)

    def _save_audited(self, entity: EntityT, actor_id: UUID, action: str) -> EntityT:
        self.session.add(entity)
        self.session.flush()
        AuditService(self.session).record(
            organization_id=entity.organization_id,  # type: ignore[attr-defined]
            actor_type="human",
            actor_id=actor_id,
            action=action,
            entity_type=entity.__tablename__,
            entity_id=cast_entity_id(entity),
            metadata={"result": "success"},
        )
        self.session.commit()
        self.session.refresh(entity)
        return entity


def cast_entity_id(entity: Any) -> UUID:
    return cast(UUID, entity.id)
