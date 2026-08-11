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

from apps.api.channel_strategy_routes import router as channel_strategy_router
from apps.api.conversation_routes import router as conversation_router
from apps.api.creative_router_routes import router as creative_router_router
from apps.api.creative_strategy_routes import router as creative_strategy_router
from apps.api.crud import CrudRouter
from apps.api.customer_voice_routes import router as customer_voice_router
from apps.api.execution_routes import router as execution_router
from apps.api.executive_routes import router as executive_router
from apps.api.finance_routes import router as finance_router
from apps.api.governance_routes import router as governance_router
from apps.api.intelligence_routes import router as intelligence_router
from apps.api.listing_intelligence_routes import router as listing_intelligence_router
from apps.api.market_connector_routes import router as market_connector_router
from apps.api.market_intelligence_routes import router as market_intelligence_router
from apps.api.opportunity_analysis_routes import router as opportunity_analysis_router
from apps.api.opportunity_routes import router as opportunity_router
from apps.api.product_intelligence_routes import router as product_intelligence_router
from apps.api.product_truth_routes import router as product_truth_router
from apps.api.reddit_intelligence_routes import router as reddit_intelligence_router
from apps.api.sales_support_routes import router as sales_support_router
from apps.api.supplier_intelligence_routes import router as supplier_intelligence_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(governance_router)
api_router.include_router(intelligence_router)
api_router.include_router(opportunity_router)
api_router.include_router(product_intelligence_router)
api_router.include_router(product_truth_router)
api_router.include_router(supplier_intelligence_router)
api_router.include_router(listing_intelligence_router)
api_router.include_router(creative_strategy_router)
api_router.include_router(channel_strategy_router, tags=["channel_strategy"])
api_router.include_router(conversation_router, tags=["conversation_commerce"])
api_router.include_router(sales_support_router, tags=["sales_support_intelligence"])
api_router.include_router(creative_router_router, tags=["creative_router"])
api_router.include_router(finance_router, tags=["finance_intelligence"])
api_router.include_router(executive_router, tags=["executive_dashboard"])
api_router.include_router(execution_router, tags=["commerce_execution"])
api_router.include_router(market_intelligence_router, tags=["market_intelligence"])
api_router.include_router(market_connector_router, tags=["market_connectors"])
api_router.include_router(opportunity_analysis_router, tags=["opportunity_analysis"])
api_router.include_router(reddit_intelligence_router, tags=["reddit_intelligence"])
api_router.include_router(customer_voice_router, tags=["customer_voice_intelligence"])


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
