from decimal import ROUND_HALF_UP, Decimal
from typing import TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from commerce_os.build.creative_generation_models import (
    CreativeGenerationJob,
    CreativeGenerationRequest,
    CreativeProviderCapability,
    CreativeQualityReview,
    GenerationRequestStatus,
)
from commerce_os.build.creative_generation_schemas import (
    GenerationJobCreate,
    GenerationRequestCreate,
    ProviderCapabilityCreate,
    QualityReviewCreate,
)
from commerce_os.build.errors import BuildScopeError, BuildStateError
from commerce_os.shared.database import Base
from commerce_os.shared.scope import reference_belongs_to_organization

EntityT = TypeVar("EntityT", bound=Base)
REQUEST_TRANSITIONS = {"draft": {"submitted", "cancelled"}, "submitted": {"cancelled"}}
ASSET_PROVIDER_TYPES = {
    "image": {"image", "editing"},
    "video": {"video", "editing"},
    "ugc": {"video", "editing"},
    "carousel": {"image", "editing"},
    "text": {"editing"},
}


class CreativeGenerationService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_request(self, payload: GenerationRequestCreate) -> CreativeGenerationRequest:
        self._scoped_reference(
            "creative_briefs", payload.creative_brief_id, payload.organization_id, "Creative brief"
        )
        self._scoped_reference(
            "users", payload.requested_by, payload.organization_id, "Requesting user"
        )
        return self._save(
            CreativeGenerationRequest(**payload.model_dump(), status=GenerationRequestStatus.DRAFT)
        )

    def transition_request(
        self, entity_id: UUID, organization_id: UUID, status: str
    ) -> CreativeGenerationRequest:
        request = self._request(entity_id, organization_id)
        if status not in REQUEST_TRANSITIONS.get(str(request.status), set()):
            raise BuildStateError(
                f"Generation request cannot transition from {request.status} to {status}."
            )
        request.status = GenerationRequestStatus(status)
        return self._save(request)

    def create_provider(self, payload: ProviderCapabilityCreate) -> CreativeProviderCapability:
        table = Base.metadata.tables["organizations"]
        exists = self.session.execute(
            select(table.c.id).where(table.c.id == payload.organization_id)
        ).scalar_one_or_none()
        if exists is None:
            raise BuildScopeError("Organization was not found.")
        return self._save(CreativeProviderCapability(**payload.model_dump()))

    def create_job(self, payload: GenerationJobCreate) -> CreativeGenerationJob:
        request = self._request(payload.request_id, payload.organization_id)
        if str(request.status) != "submitted":
            raise BuildStateError("Generation jobs require a submitted request.")
        provider = self.session.get(CreativeProviderCapability, payload.provider)
        if provider is None or provider.organization_id != payload.organization_id:
            raise BuildScopeError("Creative provider was not found in this organization.")
        if not provider.availability or provider.status != "active":
            raise BuildStateError("Creative provider must be active and available.")
        if provider.provider_type not in ASSET_PROVIDER_TYPES[str(request.asset_type)]:
            raise BuildStateError("Creative provider type does not support the request asset type.")
        values = payload.model_dump(exclude={"provider", "estimated_cost"})
        return self._save(
            CreativeGenerationJob(
                **values,
                provider_id=provider.id,
                status="pending",
                output_reference=None,
                estimated_cost=self._money(payload.estimated_cost),
                actual_cost=None,
                latency=None,
            )
        )

    def create_review(self, payload: QualityReviewCreate) -> CreativeQualityReview:
        self._scoped_reference(
            "creative_assets", payload.asset_id, payload.organization_id, "Creative asset"
        )
        return self._save(CreativeQualityReview(**payload.model_dump()))

    def _request(self, entity_id: UUID, organization_id: UUID) -> CreativeGenerationRequest:
        request = self.session.get(CreativeGenerationRequest, entity_id)
        if request is None or request.organization_id != organization_id:
            raise BuildScopeError("Generation request was not found in this organization.")
        return request

    def _scoped_reference(
        self, table: str, entity_id: UUID, organization_id: UUID, label: str
    ) -> None:
        if not reference_belongs_to_organization(
            self.session, table_name=table, reference_id=entity_id, organization_id=organization_id
        ):
            raise BuildScopeError(f"{label} was not found in this organization.")

    @staticmethod
    def _money(value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)

    def _save(self, entity: EntityT) -> EntityT:
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity
