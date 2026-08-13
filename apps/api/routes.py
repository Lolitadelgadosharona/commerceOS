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
from fastapi import APIRouter, Depends

from apps.api.ai_runtime_routes import router as ai_runtime_router
from apps.api.auth_routes import router as auth_router
from apps.api.authorization import enforce_authorization
from apps.api.channel_execution_routes import router as channel_execution_router
from apps.api.channel_strategy_routes import router as channel_strategy_router
from apps.api.commercial_risk_routes import router as commercial_risk_router
from apps.api.conversation_routes import router as conversation_router
from apps.api.creative_asset_routes import router as creative_asset_router
from apps.api.creative_execution_routes import router as creative_execution_router
from apps.api.creative_generation_routes import router as creative_generation_router
from apps.api.creative_router_routes import router as creative_router_router
from apps.api.creative_strategy_routes import router as creative_strategy_router
from apps.api.crud import CrudRouter
from apps.api.customer_360_routes import router as customer_360_router
from apps.api.customer_need_routes import router as customer_need_router
from apps.api.customer_voice_routes import router as customer_voice_router
from apps.api.discovery_listing_routes import router as discovery_listing_router
from apps.api.economics_intelligence_routes import router as economics_intelligence_router
from apps.api.execution_routes import router as execution_router
from apps.api.executive_routes import router as executive_router
from apps.api.finance_routes import router as finance_router
from apps.api.governance_routes import router as governance_router
from apps.api.intelligence_routes import router as intelligence_router
from apps.api.launch_preparation_routes import router as launch_preparation_router
from apps.api.listing_intelligence_routes import router as listing_intelligence_router
from apps.api.market_connector_routes import router as market_connector_router
from apps.api.market_intelligence_routes import router as market_intelligence_router
from apps.api.marketplace_voice_routes import router as marketplace_voice_router
from apps.api.opportunity_analysis_routes import router as opportunity_analysis_router
from apps.api.opportunity_launch_routes import router as opportunity_launch_router
from apps.api.opportunity_routes import router as opportunity_router
from apps.api.product_intelligence_routes import router as product_intelligence_router
from apps.api.product_truth_routes import router as product_truth_router
from apps.api.reddit_intelligence_routes import router as reddit_intelligence_router
from apps.api.research_analyst_routes import router as research_analyst_router
from apps.api.sales_support_routes import router as sales_support_router
from apps.api.strategic_account_routes import router as strategic_account_router
from apps.api.supplier_intelligence_routes import router as supplier_intelligence_router

api_router = APIRouter(prefix="/api/v1", dependencies=[Depends(enforce_authorization)])
api_router.include_router(ai_runtime_router, tags=["ai-runtime"])
api_router.include_router(auth_router, tags=["authentication"])
api_router.include_router(governance_router)
api_router.include_router(intelligence_router)
api_router.include_router(opportunity_router)
api_router.include_router(product_intelligence_router)
api_router.include_router(product_truth_router)
api_router.include_router(supplier_intelligence_router)
api_router.include_router(listing_intelligence_router)
api_router.include_router(creative_strategy_router)
api_router.include_router(channel_strategy_router, tags=["channel_strategy"])
api_router.include_router(channel_execution_router, tags=["channel_execution"])
api_router.include_router(conversation_router, tags=["conversation_commerce"])
api_router.include_router(sales_support_router, tags=["sales_support_intelligence"])
api_router.include_router(creative_router_router, tags=["creative_router"])
api_router.include_router(finance_router, tags=["finance_intelligence"])
api_router.include_router(executive_router, tags=["executive_dashboard"])
api_router.include_router(strategic_account_router, tags=["strategic_accounts"])
api_router.include_router(execution_router, tags=["commerce_execution"])
api_router.include_router(market_intelligence_router, tags=["market_intelligence"])
api_router.include_router(market_connector_router, tags=["market_connectors"])
api_router.include_router(marketplace_voice_router, tags=["marketplace_customer_voice"])
api_router.include_router(research_analyst_router, tags=["ai_research_analyst"])
api_router.include_router(opportunity_analysis_router, tags=["opportunity_analysis"])
api_router.include_router(opportunity_launch_router, tags=["opportunity_launch_orchestration"])
api_router.include_router(reddit_intelligence_router, tags=["reddit_intelligence"])
api_router.include_router(customer_voice_router, tags=["customer_voice_intelligence"])
api_router.include_router(customer_need_router, tags=["product_opportunity_intelligence"])
api_router.include_router(customer_360_router, tags=["customer_360"])
api_router.include_router(commercial_risk_router, tags=["product_commercial_risk_intelligence"])
api_router.include_router(economics_intelligence_router, tags=["product_economics_intelligence"])
api_router.include_router(launch_preparation_router, tags=["launch_preparation"])
api_router.include_router(discovery_listing_router, tags=["ai_discovery_listing"])
api_router.include_router(creative_asset_router, tags=["creative_assets"])
api_router.include_router(creative_execution_router, tags=["creative_execution"])
api_router.include_router(creative_generation_router, tags=["creative_generation"])


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
