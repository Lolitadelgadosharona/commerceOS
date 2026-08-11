from uuid import UUID

from commerce_os.build.creative_asset_models import CreativeAsset
from commerce_os.build.creative_generation_models import CreativeGenerationJob
from commerce_os.build.models import Product
from commerce_os.decision.creative_models import CreativeBrief, CreativeStrategy
from commerce_os.governance.models import ApprovalRequest, Organization, User
from commerce_os.operations.models import Brand
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session


def foundation(
    session: Session, slug: str
) -> tuple[Organization, User, CreativeBrief, CreativeAsset]:
    organization = Organization(name=f"Generation {slug}", slug=f"generation-{slug}")
    session.add(organization)
    session.flush()
    user = User(
        organization_id=organization.id,
        email=f"{slug}@example.com",
        display_name="Human requester",
        status="active",
        principal_type="human",
    )
    brand = Brand(
        organization_id=organization.id, name=f"Brand {slug}", slug=f"generation-brand-{slug}"
    )
    session.add_all([user, brand])
    session.flush()
    product = Product(
        organization_id=organization.id,
        brand_id=brand.id,
        name="Creative product",
        description="Approved product",
        category="home",
        status="approved",
    )
    session.add(product)
    session.flush()
    strategy = CreativeStrategy(
        organization_id=organization.id,
        product_id=product.id,
        target_audience="Home owners",
        marketing_objective="Explain value",
        core_message="Verified value",
        emotional_angle="Confidence",
        creative_direction="Evidence first",
        status="approved",
    )
    session.add(strategy)
    session.flush()
    brief = CreativeBrief(
        organization_id=organization.id,
        product_id=product.id,
        strategy_id=strategy.id,
        platform="instagram",
        audience="Home owners",
        objective="Prepare a reviewed concept",
        hook="See the proof",
        story_structure="Problem, proof, solution",
        key_message="Verified value",
        proof_requirements="Approved claims only",
        cta_strategy="Review details",
        confidence=0.8,
        proof_points="Approved claims only",
        cta="Review details",
        content_format="image",
    )
    asset = CreativeAsset(
        organization_id=organization.id,
        product_id=product.id,
        asset_type="image",
        status="draft",
        source="internal://manual",
        asset_metadata={},
        approval_status="pending",
    )
    session.add_all([brief, asset])
    session.commit()
    return organization, user, brief, asset


def test_provider_neutral_request_job_review_and_no_execution(
    client: TestClient, db_session: Session
) -> None:
    organization, user, brief, asset = foundation(db_session, "workflow")
    org_id = str(organization.id)
    request = client.post(
        "/api/v1/creative-generation-requests",
        json={
            "organization_id": org_id,
            "creative_brief_id": str(brief.id),
            "asset_type": "image",
            "platform": "instagram",
            "objective": "Create a future provider-neutral concept",
            "generation_parameters": {"aspect_ratio": "1:1", "external_call": False},
            "requested_by": str(user.id),
        },
    )
    assert request.status_code == 201
    assert request.json()["status"] == "draft"
    provider = client.post(
        "/api/v1/creative-providers",
        json={
            "organization_id": org_id,
            "provider_name": "future-image-provider",
            "provider_type": "image",
            "capabilities": ["concept_image"],
            "cost_model": {"unit": "per_output", "currency": "USD"},
            "availability": True,
        },
    )
    assert provider.status_code == 201
    blocked = client.post(
        "/api/v1/creative-generation-jobs",
        json={
            "organization_id": org_id,
            "request_id": request.json()["id"],
            "provider": provider.json()["id"],
            "input_reference": f"creative-brief://{brief.id}",
            "estimated_cost": "0.1250004",
        },
    )
    assert blocked.status_code == 409
    submitted = client.patch(
        f"/api/v1/creative-generation-requests/{request.json()['id']}",
        json={"organization_id": org_id, "status": "submitted"},
    )
    assert submitted.status_code == 200
    job = client.post(
        "/api/v1/creative-generation-jobs",
        json={
            "organization_id": org_id,
            "request_id": request.json()["id"],
            "provider": provider.json()["id"],
            "input_reference": f"creative-brief://{brief.id}",
            "estimated_cost": "0.1250004",
        },
    )
    assert job.status_code == 201
    assert job.json()["status"] == "pending"
    assert job.json()["output_reference"] is None
    assert str(job.json()["estimated_cost"]) == "0.125000"
    review = client.post(
        "/api/v1/creative-quality-reviews",
        json={
            "organization_id": org_id,
            "asset_id": str(asset.id),
            "review_type": "human_quality",
            "score": 82,
            "issues": ["Proof placement needs review"],
            "recommendation": "Revise before approval",
        },
    )
    assert review.status_code == 201
    assert db_session.scalar(select(func.count()).select_from(ApprovalRequest)) == 0
    stored_job = db_session.get(CreativeGenerationJob, UUID(job.json()["id"]))
    assert stored_job is not None and stored_job.actual_cost is None and stored_job.latency is None
    assert client.post("/api/v1/creative-generation-jobs/execute", json={}).status_code in {
        404,
        405,
        422,
    }
    for endpoint in (
        "creative-generation-requests",
        "creative-providers",
        "creative-generation-jobs",
        "creative-quality-reviews",
    ):
        response = client.get(f"/api/v1/{endpoint}", params={"organization_id": org_id})
        assert response.status_code == 200 and response.json()


def test_generation_tenant_isolation(client: TestClient, db_session: Session) -> None:
    owner, user, brief, _ = foundation(db_session, "owner")
    other, _, _, _ = foundation(db_session, "other")
    response = client.post(
        "/api/v1/creative-generation-requests",
        json={
            "organization_id": str(other.id),
            "creative_brief_id": str(brief.id),
            "asset_type": "image",
            "platform": "web",
            "objective": "Cross tenant",
            "generation_parameters": {},
            "requested_by": str(user.id),
        },
    )
    assert response.status_code == 403
