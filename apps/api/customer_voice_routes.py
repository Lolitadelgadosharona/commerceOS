from typing import Annotated, Any, TypeVar, cast
from uuid import UUID

from commerce_os.intelligence.voice_models import (
    CustomerLanguageInsight,
    CustomerPainCluster,
    PainClusterMembership,
    PurchaseIntentSignal,
)
from commerce_os.intelligence.voice_schemas import (
    CustomerLanguageCreate,
    CustomerLanguageRead,
    PainClusterCreate,
    PainClusterRead,
    PainClusterUpdate,
    PainMembershipCreate,
    PainMembershipRead,
    PurchaseIntentCreate,
    PurchaseIntentRead,
)
from commerce_os.intelligence.voice_services import CustomerVoiceService, scoped_voice
from commerce_os.shared.database import Base, get_session
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

router = APIRouter()
SessionDependency = Annotated[Session, Depends(get_session)]
ModelT = TypeVar("ModelT", bound=Base)


def _list(session: Session, model: type[ModelT], organization_id: UUID) -> list[ModelT]:
    mapped = cast(Any, model)
    return list(
        session.scalars(
            select(model)
            .where(mapped.organization_id == organization_id)
            .order_by(mapped.created_at.desc())
        )
    )


@router.post("/pain-clusters", response_model=PainClusterRead, status_code=201)
def create_cluster(payload: PainClusterCreate, session: SessionDependency) -> CustomerPainCluster:
    return CustomerVoiceService(session).create_cluster(payload)


@router.get("/pain-clusters", response_model=list[PainClusterRead])
def list_clusters(organization_id: UUID, session: SessionDependency) -> list[CustomerPainCluster]:
    return _list(session, CustomerPainCluster, organization_id)


@router.patch("/pain-clusters/{cluster_id}", response_model=PainClusterRead)
def transition_cluster(
    cluster_id: UUID,
    organization_id: UUID,
    payload: PainClusterUpdate,
    session: SessionDependency,
) -> CustomerPainCluster:
    cluster = scoped_voice(session, CustomerPainCluster, cluster_id, organization_id)
    return CustomerVoiceService(session).transition_cluster(cluster, payload.status)


@router.post(
    "/pain-clusters/{cluster_id}/members",
    response_model=PainMembershipRead,
    status_code=201,
)
def add_member(
    cluster_id: UUID, payload: PainMembershipCreate, session: SessionDependency
) -> PainClusterMembership:
    return CustomerVoiceService(session).add_membership(cluster_id, payload)


@router.post("/customer-language", response_model=CustomerLanguageRead, status_code=201)
def create_language(
    payload: CustomerLanguageCreate, session: SessionDependency
) -> CustomerLanguageInsight:
    return CustomerVoiceService(session).create_language(payload)


@router.get("/customer-language", response_model=list[CustomerLanguageRead])
def list_language(
    organization_id: UUID, session: SessionDependency
) -> list[CustomerLanguageInsight]:
    return _list(session, CustomerLanguageInsight, organization_id)


@router.post("/purchase-intent-signals", response_model=PurchaseIntentRead, status_code=201)
def create_intent(
    payload: PurchaseIntentCreate, session: SessionDependency
) -> PurchaseIntentSignal:
    return CustomerVoiceService(session).create_intent(payload)


@router.get("/purchase-intent-signals", response_model=list[PurchaseIntentRead])
def list_intents(organization_id: UUID, session: SessionDependency) -> list[PurchaseIntentSignal]:
    return _list(session, PurchaseIntentSignal, organization_id)
