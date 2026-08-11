from decimal import Decimal

import pytest
from commerce_os.build.creative_asset_schemas import CreativeAssetVersionCreate
from commerce_os.build.creative_asset_services import CreativeAssetService
from commerce_os.build.errors import BuildScopeError
from commerce_os.build.models import Product
from commerce_os.decision.creative_models import CreativeStrategy
from commerce_os.governance.models import ApprovalRequest, Organization
from commerce_os.operations.models import Brand
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session


def creative_foundation(
    session: Session, slug: str
) -> tuple[Organization, Product, CreativeStrategy]:
    organization = Organization(name=f"Creative Asset {slug}", slug=f"creative-asset-{slug}")
    session.add(organization)
    session.flush()
    brand = Brand(organization_id=organization.id, name=f"Brand {slug}", slug=f"asset-brand-{slug}")
    session.add(brand)
    session.flush()
    product = Product(
        organization_id=organization.id,
        brand_id=brand.id,
        name="Creative product",
        description="Approved Build product",
        category="home",
        status="approved",
    )
    session.add(product)
    session.flush()
    strategy = CreativeStrategy(
        organization_id=organization.id,
        product_id=product.id,
        target_audience="Apartment dwellers",
        marketing_objective="Explain verified differentiation",
        core_message="Quiet comfort",
        emotional_angle="Relief",
        creative_direction="Evidence-first demonstration",
        status="approved",
    )
    session.add(strategy)
    session.commit()
    return organization, product, strategy


def test_brief_asset_versions_feedback_and_approval_boundary(
    client: TestClient, db_session: Session
) -> None:
    organization, product, strategy = creative_foundation(db_session, "api")
    base = {"organization_id": str(organization.id), "product_id": str(product.id)}
    brief = client.post(
        "/api/v1/creative-briefs",
        json=base
        | {
            "creative_strategy_id": str(strategy.id),
            "platform": "instagram",
            "audience": "Apartment dwellers",
            "objective": "Prepare a human-reviewed product demonstration",
            "hook": "Hear the difference",
            "story_structure": "Problem, verified proof, product",
            "key_message": "Quiet comfort backed by Product Truth",
            "proof_requirements": "Only approved claims and specifications",
            "cta_strategy": "Invite human review of product details",
            "confidence": 0.8,
        },
    )
    assert brief.status_code == 201
    assert brief.json()["creative_strategy_id"] == str(strategy.id)
    assert brief.json()["product_id"] == str(product.id)
    asset = client.post(
        "/api/v1/creative-assets",
        json=base
        | {
            "asset_type": "image",
            "source": "internal://manual-registry",
            "metadata": {"brief_id": brief.json()["id"], "generated": False},
        },
    )
    assert asset.status_code == 201
    assert asset.json()["status"] == "draft"
    assert asset.json()["approval_status"] == "pending"
    assert asset.json()["metadata"]["generated"] is False
    asset_id = asset.json()["id"]
    for expected, reason in ((1, "Initial registry"), (2, "Alternative crop plan")):
        version = client.post(
            "/api/v1/creative-versions",
            json={
                "organization_id": str(organization.id),
                "asset_id": asset_id,
                "variation_reason": reason,
                "experiment_group": "prelaunch-a",
            },
        )
        assert version.status_code == 201
        assert version.json()["version_number"] == expected
    observation = client.post(
        "/api/v1/creative-performance",
        json={
            "organization_id": str(organization.id),
            "asset_id": asset_id,
            "metric_type": "qualified_feedback_rate",
            "metric_value": "0.1234564",
            "source": "internal://manual-observation",
            "period": "prelaunch-review-1",
            "confidence": 0.7,
        },
    )
    assert observation.status_code == 201
    assert Decimal(observation.json()["metric_value"]) == Decimal("0.123456")
    forbidden_approval = client.post(
        "/api/v1/creative-assets",
        json=base
        | {
            "asset_type": "text",
            "source": "internal://manual",
            "metadata": {},
            "approval_status": "approved",
        },
    )
    assert forbidden_approval.status_code == 422
    assert db_session.scalar(select(func.count()).select_from(ApprovalRequest)) == 0
    for endpoint in (
        "creative-briefs",
        "creative-assets",
        "creative-versions",
        "creative-performance",
    ):
        response = client.get(
            f"/api/v1/{endpoint}", params={"organization_id": str(organization.id)}
        )
        assert response.status_code == 200
        assert response.json()


def test_asset_tenant_isolation_and_no_publish(client: TestClient, db_session: Session) -> None:
    owner, product, _ = creative_foundation(db_session, "owner")
    other, _, _ = creative_foundation(db_session, "other")
    asset = client.post(
        "/api/v1/creative-assets",
        json={
            "organization_id": str(owner.id),
            "product_id": str(product.id),
            "asset_type": "video",
            "source": "internal://registry",
            "metadata": {"binary_present": False},
        },
    )
    assert asset.status_code == 201
    with pytest.raises(BuildScopeError):
        CreativeAssetService(db_session).create_version(
            CreativeAssetVersionCreate(
                organization_id=other.id,
                asset_id=asset.json()["id"],
                variation_reason="Cross-tenant attempt",
                experiment_group="none",
            )
        )
    assert client.post("/api/v1/creative-assets/publish", json={}).status_code in {404, 405, 422}
