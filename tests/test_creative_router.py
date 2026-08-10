import pytest
from commerce_os.build.models import Product
from commerce_os.decision.creative_models import CreativeStrategyStatus
from commerce_os.decision.creative_router_models import AssetStrategyStatus
from commerce_os.decision.creative_router_schemas import (
    AssetStrategyCreate,
    EconomicAssessmentCreate,
    ModelProviderCreate,
    PatternCreate,
    RoutingDecisionCreate,
)
from commerce_os.decision.creative_router_services import CreativeRouterService
from commerce_os.decision.creative_schemas import CreativeStrategyCreate
from commerce_os.decision.creative_services import CreativeStrategyService
from commerce_os.decision.errors import DecisionStateError
from commerce_os.governance.models import Organization
from commerce_os.operations.models import Brand
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def foundation(session: Session, slug: str):
    organization = Organization(name=f"Creative Router {slug}", slug=slug)
    session.add(organization)
    session.flush()
    brand = Brand(organization_id=organization.id, name="Brand", slug=f"{slug}-brand")
    session.add(brand)
    session.flush()
    product = Product(
        organization_id=organization.id,
        brand_id=brand.id,
        name="Care Kit",
        description="Care product",
        category="Care",
        status="approved",
    )
    session.add(product)
    session.commit()
    creative = CreativeStrategyService(session).create(
        CreativeStrategyCreate(
            organization_id=organization.id,
            product_id=product.id,
            target_audience="Care-focused households",
            marketing_objective="Increase qualified interest",
            core_message="Evidence-led care",
            emotional_angle="Confidence",
            creative_direction="Demonstrate verified use",
        )
    )
    CreativeStrategyService(session).transition(creative, CreativeStrategyStatus.APPROVED)
    return organization, product, creative


def test_strategy_routing_economics_registry_and_tenant_isolation(db_session: Session) -> None:
    organization, product, creative = foundation(db_session, "creative-router")
    other, _, _ = foundation(db_session, "creative-router-other")
    service = CreativeRouterService(db_session)
    asset = service.create_asset_strategy(
        AssetStrategyCreate(
            organization_id=organization.id,
            product_id=product.id,
            creative_strategy_id=creative.id,
            audience="Care-focused households",
            objective="Explain verified use",
            recommended_format="comparison",
            creative_angle="Proof before promise",
            confidence=0.8,
        )
    )
    with pytest.raises(DecisionStateError):
        service.transition_asset_strategy(asset, AssetStrategyStatus.APPROVED)
    service.transition_asset_strategy(asset, AssetStrategyStatus.RECOMMENDED)
    service.transition_asset_strategy(asset, AssetStrategyStatus.APPROVED)
    quality = service.create_provider(
        ModelProviderCreate(
            organization_id=organization.id,
            provider_name="Future Image Quality",
            capability_type="image",
            quality_score=95,
            cost_score=50,
            speed_score=60,
            availability=True,
        )
    )
    balanced = service.create_provider(
        ModelProviderCreate(
            organization_id=organization.id,
            provider_name="Future Image Balanced",
            capability_type="image",
            quality_score=80,
            cost_score=90,
            speed_score=90,
            availability=True,
        )
    )
    foreign = service.create_provider(
        ModelProviderCreate(
            organization_id=other.id,
            provider_name="Foreign Provider",
            capability_type="image",
            quality_score=100,
            cost_score=100,
            speed_score=100,
            availability=True,
        )
    )
    decision = service.route(
        RoutingDecisionCreate(
            organization_id=organization.id,
            asset_strategy_id=asset.id,
            capability_required="image",
            candidate_provider_ids=[quality.id, balanced.id, foreign.id],
            platform_suitability={quality.id: 80, balanced.id: 90},
            historical_performance={},
            reason="Deterministic weighted fit; no model invocation.",
            confidence=0.75,
        )
    )
    assert decision.selected_provider_id == balanced.id
    assert decision.factor_snapshot["historical_performance"] is None
    assessment = service.assess_economics(
        EconomicAssessmentCreate(
            organization_id=organization.id,
            creative_strategy_id=creative.id,
            estimated_production_cost=20,
            expected_impact=100,
            test_value=10,
            confidence=0.8,
        )
    )
    assert assessment.profitability_score == 76.92
    pattern = service.create_pattern(
        PatternCreate(
            organization_id=organization.id,
            name="Proof before promise",
            pattern_type="proof_structure",
            description="Lead with verified evidence before a benefit statement.",
            source_reference="internal:test-observation",
            performance_notes="No external creative copied.",
        )
    )
    assert pattern.pattern_type == "proof_structure"


def test_creative_router_api_and_format_validation(client: TestClient, db_session: Session) -> None:
    organization, product, creative = foundation(db_session, "creative-router-api")
    base = {"organization_id": str(organization.id)}
    asset_payload = base | {
        "product_id": str(product.id),
        "creative_strategy_id": str(creative.id),
        "audience": "Care-focused households",
        "objective": "Explain use",
        "recommended_format": "educational",
        "creative_angle": "Evidence-led demonstration",
        "confidence": 0.8,
    }
    asset = client.post("/api/v1/creative-asset-strategies", json=asset_payload)
    assert asset.status_code == 201
    assert (
        client.post(
            "/api/v1/creative-asset-strategies",
            json=asset_payload | {"recommended_format": "unsupported"},
        ).status_code
        == 422
    )
    provider = client.post(
        "/api/v1/creative-model-providers",
        json=base
        | {
            "provider_name": "Future Video Provider",
            "capability_type": "video",
            "quality_score": 80,
            "cost_score": 70,
            "speed_score": 90,
            "availability": True,
        },
    )
    assert provider.status_code == 201
    routing = client.post(
        "/api/v1/creative-routing-decisions",
        json=base
        | {
            "asset_strategy_id": asset.json()["id"],
            "capability_required": "video",
            "candidate_provider_ids": [provider.json()["id"]],
            "reason": "Advisory route only.",
            "confidence": 0.7,
        },
    )
    assert routing.status_code == 201
    assert (
        client.post(
            "/api/v1/creative-economic-assessments",
            json=base
            | {
                "creative_strategy_id": str(creative.id),
                "estimated_production_cost": 10,
                "expected_impact": 30,
                "test_value": 5,
                "confidence": 0.5,
            },
        ).status_code
        == 201
    )
    assert (
        client.post(
            "/api/v1/creative-patterns",
            json=base
            | {
                "name": "Question hook",
                "pattern_type": "hook_pattern",
                "description": "Begin with a relevant customer question.",
                "source_reference": "internal:principle",
            },
        ).status_code
        == 201
    )
    for endpoint in (
        "creative-asset-strategies",
        "creative-model-providers",
        "creative-routing-decisions",
        "creative-economic-assessments",
        "creative-patterns",
    ):
        assert client.get(f"/api/v1/{endpoint}", params=base).status_code == 200
