from datetime import timedelta
from typing import Annotated, Any, TypeVar, cast
from uuid import UUID

from commerce_os.decision.strategic_account_models import (
    CustomerExpansionOpportunity,
    CustomerNextBestAction,
    StrategicAccountScore,
)
from commerce_os.governance.executive_models import DecisionQueueItem
from commerce_os.intelligence.replenishment_models import ReplenishmentAssessment
from commerce_os.operations.strategic_account_models import (
    AccountStakeholder,
    StrategicAccountProfile,
)
from commerce_os.shared.database import Base, get_session
from commerce_os.shared.scope import reference_belongs_to_organization
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.errors import ApiError
from apps.api.strategic_account_schemas import (
    ExpansionCreate,
    ExpansionRead,
    ExpansionUpdate,
    NextBestActionCreate,
    NextBestActionRead,
    ReplenishmentCreate,
    ReplenishmentRead,
    StakeholderCreate,
    StakeholderRead,
    StrategicAccountCreate,
    StrategicAccountRead,
    StrategicAccountUpdate,
    StrategicScoreCreate,
    StrategicScoreRead,
)

router = APIRouter()
SessionDependency = Annotated[Session, Depends(get_session)]
ModelT = TypeVar("ModelT", bound=Base)


def scoped(session: Session, model: type[ModelT], item_id: UUID, organization_id: UUID) -> ModelT:
    item = session.get(model, item_id)
    if item is None or cast(Any, item).organization_id != organization_id:
        raise ApiError(404, "not_found", "Resource was not found in this organization.")
    return item


def account(session: Session, item_id: UUID, organization_id: UUID) -> StrategicAccountProfile:
    return scoped(session, StrategicAccountProfile, item_id, organization_id)


def save(session: Session, item: ModelT) -> ModelT:
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.post("/strategic-accounts", response_model=StrategicAccountRead, status_code=201)
def create_account(
    payload: StrategicAccountCreate, session: SessionDependency
) -> StrategicAccountProfile:
    if not reference_belongs_to_organization(
        session,
        table_name="customers",
        reference_id=payload.customer_id,
        organization_id=payload.organization_id,
    ):
        raise ApiError(404, "not_found", "Customer was not found in this organization.")
    if payload.project_id and not reference_belongs_to_organization(
        session,
        table_name="projects",
        reference_id=payload.project_id,
        organization_id=payload.organization_id,
    ):
        raise ApiError(404, "not_found", "Project was not found in this organization.")
    return save(session, StrategicAccountProfile(**payload.model_dump()))


@router.get("/strategic-accounts", response_model=list[StrategicAccountRead])
def list_accounts(
    organization_id: UUID, session: SessionDependency
) -> list[StrategicAccountProfile]:
    return list(
        session.scalars(
            select(StrategicAccountProfile).where(
                StrategicAccountProfile.organization_id == organization_id
            )
        )
    )


@router.patch("/strategic-accounts/{item_id}", response_model=StrategicAccountRead)
def update_account(
    item_id: UUID,
    organization_id: UUID,
    payload: StrategicAccountUpdate,
    session: SessionDependency,
) -> StrategicAccountProfile:
    item = account(session, item_id, organization_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    return save(session, item)


@router.post("/account-stakeholders", response_model=StakeholderRead, status_code=201)
def create_stakeholder(
    payload: StakeholderCreate, session: SessionDependency
) -> AccountStakeholder:
    account(session, payload.strategic_account_id, payload.organization_id)
    return save(session, AccountStakeholder(**payload.model_dump()))


@router.get("/account-stakeholders", response_model=list[StakeholderRead])
def list_stakeholders(
    organization_id: UUID, session: SessionDependency
) -> list[AccountStakeholder]:
    return list(
        session.scalars(
            select(AccountStakeholder).where(AccountStakeholder.organization_id == organization_id)
        )
    )


@router.post("/replenishment-assessments", response_model=ReplenishmentRead, status_code=201)
def create_replenishment(
    payload: ReplenishmentCreate, session: SessionDependency
) -> ReplenishmentAssessment:
    account(session, payload.strategic_account_id, payload.organization_id)
    start = (
        payload.last_purchase_date + timedelta(days=payload.expected_replenishment_cycle_days)
        if payload.last_purchase_date and payload.expected_replenishment_cycle_days
        else None
    )
    end = (
        start + timedelta(days=max(1, payload.expected_replenishment_cycle_days // 5))
        if start and payload.expected_replenishment_cycle_days
        else None
    )
    has_evidence = bool(
        payload.historical_purchase_references
        or payload.conversation_evidence
        or payload.behavior_indicators
    )
    probability = (
        round(min(1.0, (payload.purchase_frequency_indicator or 0) / 100 * payload.confidence), 4)
        if has_evidence and payload.purchase_frequency_indicator is not None
        else None
    )
    values = payload.model_dump() | {
        "estimated_next_purchase_start": start,
        "estimated_next_purchase_end": end,
        "replenishment_probability": probability,
        "assessment_version": "replenishment-v1.0",
    }
    return save(session, ReplenishmentAssessment(**values))


@router.get("/replenishment-assessments", response_model=list[ReplenishmentRead])
def list_replenishment(
    organization_id: UUID, session: SessionDependency
) -> list[ReplenishmentAssessment]:
    return list(
        session.scalars(
            select(ReplenishmentAssessment).where(
                ReplenishmentAssessment.organization_id == organization_id
            )
        )
    )


@router.post("/customer-expansion-opportunities", response_model=ExpansionRead, status_code=201)
def create_expansion(
    payload: ExpansionCreate, session: SessionDependency
) -> CustomerExpansionOpportunity:
    account(session, payload.strategic_account_id, payload.organization_id)
    return save(session, CustomerExpansionOpportunity(**payload.model_dump()))


@router.get("/customer-expansion-opportunities", response_model=list[ExpansionRead])
def list_expansion(
    organization_id: UUID, session: SessionDependency
) -> list[CustomerExpansionOpportunity]:
    return list(
        session.scalars(
            select(CustomerExpansionOpportunity).where(
                CustomerExpansionOpportunity.organization_id == organization_id
            )
        )
    )


@router.patch("/customer-expansion-opportunities/{item_id}", response_model=ExpansionRead)
def update_expansion(
    item_id: UUID, organization_id: UUID, payload: ExpansionUpdate, session: SessionDependency
) -> CustomerExpansionOpportunity:
    item = scoped(session, CustomerExpansionOpportunity, item_id, organization_id)
    item.status = payload.status
    return save(session, item)


@router.post("/customer-next-best-actions", response_model=NextBestActionRead, status_code=201)
def create_action(
    payload: NextBestActionCreate, session: SessionDependency
) -> CustomerNextBestAction:
    if not reference_belongs_to_organization(
        session,
        table_name="customers",
        reference_id=payload.customer_id,
        organization_id=payload.organization_id,
    ):
        raise ApiError(404, "not_found", "Customer was not found in this organization.")
    if payload.strategic_account_id:
        account(session, payload.strategic_account_id, payload.organization_id)
    item = CustomerNextBestAction(
        **payload.model_dump(), formula_or_rule_version="next-best-action-v1.0"
    )
    if (
        payload.human_review_required
        and payload.priority in {"high", "critical"}
        and payload.recommendation_type != "no_action"
    ):
        queue = DecisionQueueItem(
            organization_id=payload.organization_id,
            title="Strategic account requires review",
            domain="decision",
            reason=payload.reason,
            priority=payload.priority,
            required_action="review",
            status="pending",
        )
        session.add(queue)
        session.flush()
        item.decision_queue_item_id = queue.id
    return save(session, item)


@router.get("/customer-next-best-actions", response_model=list[NextBestActionRead])
def list_actions(organization_id: UUID, session: SessionDependency) -> list[CustomerNextBestAction]:
    return list(
        session.scalars(
            select(CustomerNextBestAction).where(
                CustomerNextBestAction.organization_id == organization_id
            )
        )
    )


WEIGHTS = {
    "contribution_margin": 0.14,
    "repeat_probability": 0.14,
    "purchase_frequency": 0.10,
    "ltv": 0.10,
    "b2b_potential": 0.08,
    "expansion_potential": 0.10,
    "referral_potential": 0.06,
    "relationship_strength": 0.10,
    "strategic_importance": 0.08,
    "payment_risk": -0.04,
    "refund_risk": -0.025,
    "dispute_risk": -0.025,
    "operational_burden": -0.04,
}


@router.post("/strategic-account-scores", response_model=StrategicScoreRead, status_code=201)
def create_score(
    payload: StrategicScoreCreate, session: SessionDependency
) -> StrategicAccountScore:
    account(session, payload.strategic_account_id, payload.organization_id)
    unknown = set(payload.input_values) - set(WEIGHTS)
    if unknown:
        raise ApiError(422, "invalid_input", f"Unknown score inputs: {sorted(unknown)}")
    supplied = {key: value for key, value in payload.input_values.items() if value is not None}
    if any(value < 0 or value > 100 for value in supplied.values()):
        raise ApiError(422, "invalid_input", "Score inputs must be between 0 and 100.")
    coverage = len(supplied) / len(WEIGHTS)
    score = round(max(0, min(100, sum(value * WEIGHTS[key] for key, value in supplied.items()))), 2)
    return save(
        session,
        StrategicAccountScore(
            organization_id=payload.organization_id,
            strategic_account_id=payload.strategic_account_id,
            input_values=payload.input_values,
            weights=WEIGHTS,
            formula_version="strategic-account-v1.0",
            score=score,
            confidence=round(coverage, 4),
            evidence_coverage=round(coverage, 4),
        ),
    )
