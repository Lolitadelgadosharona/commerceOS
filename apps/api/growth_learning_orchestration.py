from datetime import UTC, datetime
from uuid import UUID

from commerce_os.growth.conversation_learning_models import GrowthSalesLearningSignal
from commerce_os.growth.conversation_learning_schemas import SalesLearningSignalCreate
from commerce_os.growth.conversation_learning_services import (
    GrowthConversationLearningService,
)
from commerce_os.learning.schemas import LearningObservationCreate
from commerce_os.learning.services import ClosedLoopLearningService
from sqlalchemy.orm import Session


def create_growth_sales_learning_signal(
    session: Session, payload: SalesLearningSignalCreate, actor_id: UUID
) -> GrowthSalesLearningSignal:
    growth_service = GrowthConversationLearningService(session)
    growth_service.validate_learning_signal(payload)
    observation = ClosedLoopLearningService(session).create_observation(
        LearningObservationCreate(
            organization_id=payload.organization_id,
            source_type="growth_conversation_analysis",
            source_record_id=payload.analysis_id,
            observation_type=payload.signal_type,
            observed_at=datetime.now(UTC),
            evidence_reference=f"sales_conversation_analysis:{payload.analysis_id}",
            confidence=payload.confidence,
            metadata={
                "insight": payload.insight,
                "authority": "advisory_only",
                "source_truth_modified": False,
            },
        ),
        actor_id,
    )
    return growth_service.create_learning_signal(payload, observation.id, actor_id)
