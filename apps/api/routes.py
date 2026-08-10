from commerce_os.decision.models import VentureOpportunity
from commerce_os.decision.schemas import (
    VentureOpportunityCreate,
    VentureOpportunityRead,
    VentureOpportunityUpdate,
)
from commerce_os.governance.models import Organization, Project
from commerce_os.governance.schemas import (
    OrganizationCreate,
    OrganizationRead,
    OrganizationUpdate,
    ProjectCreate,
    ProjectRead,
    ProjectUpdate,
)
from commerce_os.operations.models import Customer, SalesOpportunity
from commerce_os.operations.schemas import (
    CustomerCreate,
    CustomerRead,
    CustomerUpdate,
    SalesOpportunityCreate,
    SalesOpportunityRead,
    SalesOpportunityUpdate,
)
from fastapi import APIRouter

from apps.api.crud import CrudRouter
from apps.api.governance_routes import router as governance_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(governance_router)


@api_router.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "commerce-os-api", "version": "0.1.0"}


api_router.include_router(
    CrudRouter(
        prefix="/organizations",
        tag="organizations",
        model=Organization,
        create_schema=OrganizationCreate,
        update_schema=OrganizationUpdate,
        read_schema=OrganizationRead,
    ).router
)
api_router.include_router(
    CrudRouter(
        prefix="/projects",
        tag="projects",
        model=Project,
        create_schema=ProjectCreate,
        update_schema=ProjectUpdate,
        read_schema=ProjectRead,
    ).router
)
api_router.include_router(
    CrudRouter(
        prefix="/customers",
        tag="customers",
        model=Customer,
        create_schema=CustomerCreate,
        update_schema=CustomerUpdate,
        read_schema=CustomerRead,
    ).router
)
api_router.include_router(
    CrudRouter(
        prefix="/venture-opportunities",
        tag="venture_opportunities",
        model=VentureOpportunity,
        create_schema=VentureOpportunityCreate,
        update_schema=VentureOpportunityUpdate,
        read_schema=VentureOpportunityRead,
    ).router
)
api_router.include_router(
    CrudRouter(
        prefix="/sales-opportunities",
        tag="sales_opportunities",
        model=SalesOpportunity,
        create_schema=SalesOpportunityCreate,
        update_schema=SalesOpportunityUpdate,
        read_schema=SalesOpportunityRead,
    ).router
)
