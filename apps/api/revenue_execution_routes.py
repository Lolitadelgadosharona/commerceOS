from typing import Annotated, Any, cast
from uuid import UUID

from commerce_os.growth.revenue_execution_models import DailyGrowthOpportunity
from commerce_os.growth.revenue_execution_schemas import (
    DailyOpportunityCreate,
    DailyOpportunityRead,
    GiftResponseTransition,
    RevenueExecutionDashboard,
)
from commerce_os.growth.revenue_execution_services import RevenueExecutionService
from commerce_os.growth.revenue_models import GrowthGift
from commerce_os.growth.revenue_schemas import GrowthGiftRead
from commerce_os.growth.revenue_services import GrowthRevenueService, scoped_revenue
from commerce_os.shared.database import get_session
from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.growth_revenue_routes import actor_id

router = APIRouter()
SessionDependency = Annotated[Session, Depends(get_session)]


@router.post("/daily-growth-opportunities", response_model=DailyOpportunityRead, status_code=201)
def create_daily_opportunity(
    payload: DailyOpportunityCreate, request: Request, session: SessionDependency
) -> DailyGrowthOpportunity:
    return RevenueExecutionService(session).create_daily_opportunity(payload, actor_id(request))


@router.get("/daily-growth-opportunities", response_model=list[DailyOpportunityRead])
def list_daily_opportunities(
    organization_id: UUID, session: SessionDependency
) -> list[DailyGrowthOpportunity]:
    model = cast(Any, DailyGrowthOpportunity)
    return list(
        session.scalars(
            select(DailyGrowthOpportunity)
            .where(model.organization_id == organization_id)
            .order_by(model.queue_date.desc(), model.created_at.desc())
        )
    )


@router.patch("/growth-gift-pipeline/{gift_id}", response_model=GrowthGiftRead)
def transition_gift_pipeline(
    gift_id: UUID,
    organization_id: UUID,
    payload: GiftResponseTransition,
    request: Request,
    session: SessionDependency,
) -> GrowthGift:
    gift = scoped_revenue(session, GrowthGift, gift_id, organization_id)
    return GrowthRevenueService(session).transition_gift(
        gift,
        payload.status,
        actor_id(request),
        payload.approval_request_id,
        payload.customer_response,
    )


@router.get("/revenue-execution-dashboard", response_model=RevenueExecutionDashboard)
def revenue_dashboard(
    organization_id: UUID, session: SessionDependency
) -> RevenueExecutionDashboard:
    return RevenueExecutionService(session).dashboard(organization_id)
