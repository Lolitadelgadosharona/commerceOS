from uuid import UUID

from sqlalchemy.orm import Session

from commerce_os.decision.customer_value_models import CustomerValueAssessment
from commerce_os.decision.customer_value_schemas import CustomerValueCreate
from commerce_os.decision.errors import DecisionScopeError
from commerce_os.shared.audit import record_audit_event
from commerce_os.shared.scope import reference_belongs_to_organization


class CustomerValueService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self, payload: CustomerValueCreate, actor_id: UUID | None = None
    ) -> CustomerValueAssessment:
        if not reference_belongs_to_organization(
            self.session,
            table_name="customers",
            reference_id=payload.customer_id,
            organization_id=payload.organization_id,
        ):
            raise DecisionScopeError("Customer was not found in this organization.")
        score = round(
            max(
                0.0,
                min(
                    100.0,
                    payload.revenue_indicator * 0.2
                    + payload.margin_indicator * 0.2
                    + payload.repeat_probability * 100 * 0.25
                    + payload.strategic_potential * 0.2
                    - payload.risk_indicator * 0.15,
                ),
            ),
            2,
        )
        values = payload.model_dump(exclude={"contribution_potential"})
        entity = CustomerValueAssessment(
            **values,
            contribution_potential=payload.contribution_potential
            if payload.contribution_potential is not None
            else score,
            score=score,
            formula_version="customer-value-v1.1-advisory",
        )
        self.session.add(entity)
        self.session.flush()
        record_audit_event(
            self.session,
            organization_id=payload.organization_id,
            actor_type="human" if actor_id else "system",
            actor_id=actor_id,
            action="decision.customer_value_assessment.created",
            entity_type="customer_value_assessments",
            entity_id=entity.id,
            metadata={"result": "success", "authority": "advisory_only"},
        )
        self.session.commit()
        self.session.refresh(entity)
        return entity
