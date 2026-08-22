from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from commerce_os.intelligence.business_signal_models import BusinessDemandSignal
from commerce_os.intelligence.business_signal_schemas import BusinessDemandSignalCreate
from commerce_os.intelligence.errors import IntelligenceScopeError
from commerce_os.shared.audit import record_audit_event
from commerce_os.shared.database import Base


class BusinessDemandSignalService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, payload: BusinessDemandSignalCreate, actor_id: UUID) -> BusinessDemandSignal:
        results = Base.metadata.tables["growth_business_research_results"]
        result_id = self.session.scalar(
            select(results.c.id).where(
                results.c.id == payload.source_research_result_id,
                results.c.organization_id == payload.organization_id,
            )
        )
        if result_id is None:
            raise IntelligenceScopeError(
                "Source business research result was not found in this organization."
            )
        entity = BusinessDemandSignal(**payload.model_dump())
        self.session.add(entity)
        self.session.flush()
        record_audit_event(
            self.session,
            organization_id=entity.organization_id,
            actor_type="service",
            actor_id=actor_id,
            action="intelligence.business_demand_signal.created",
            entity_type=entity.__tablename__,
            entity_id=entity.id,
            metadata={"result": "success", "source_domain": payload.source_domain},
        )
        self.session.commit()
        self.session.refresh(entity)
        return entity
