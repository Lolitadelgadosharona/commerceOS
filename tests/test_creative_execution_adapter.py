from decimal import Decimal

import pytest
from commerce_os.build.creative_asset_models import CreativeAsset
from commerce_os.build.creative_execution_adapter import CreativeExecutionAdapter
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
    organization = Organization(name=f"Execution {slug}", slug=f"execution-{slug}")
    session.add(organization)
    session.flush()
    user = User(
        organization_id=organization.id,
        email=f"execute-{slug}@example.com",
        display_name="Human",
        status="active",
        principal_type="human",
    )
    brand = Brand(
        organization_id=organization.id, name=f"Brand {slug}", slug=f"execution-brand-{slug}"
    )
    session.add_all([user, brand])
    session.flush()
    product = Product(
        organization_id=organization.id,
        brand_id=brand.id,
        name="Product",
        description="Approved",
        category="home",
        status="approved",
    )
    session.add(product)
    session.flush()
    strategy = CreativeStrategy(
        organization_id=organization.id,
        product_id=product.id,
        target_audience="Buyers",
        marketing_objective="Explain",
        core_message="Truth",
        emotional_angle="Trust",
        creative_direction="Evidence",
        status="approved",
    )
    session.add(strategy)
    session.flush()
    brief = CreativeBrief(
        organization_id=organization.id,
        product_id=product.id,
        strategy_id=strategy.id,
        platform="instagram",
        audience="Buyers",
        objective="Plan",
        hook="Proof",
        story_structure="Problem proof",
        key_message="Truth",
        proof_requirements="Approved",
        cta_strategy="Review",
        confidence=0.8,
        proof_points="Approved",
        cta="Review",
        content_format="image",
    )
    asset = CreativeAsset(
        organization_id=organization.id,
        product_id=product.id,
        asset_type="image",
        status="draft",
        source="internal://registry",
        asset_metadata={},
        approval_status="pending",
    )
    session.add_all([brief, asset])
    session.commit()
    return organization, user, brief, asset


def create_job(
    client: TestClient, organization: Organization, user: User, brief: CreativeBrief
) -> tuple[dict, dict]:
    org_id = str(organization.id)
    request = client.post(
        "/api/v1/creative-generation-requests",
        json={
            "organization_id": org_id,
            "creative_brief_id": str(brief.id),
            "asset_type": "image",
            "platform": "instagram",
            "objective": "Provider-neutral execution record",
            "generation_parameters": {"external": False},
            "requested_by": str(user.id),
        },
    ).json()
    client.patch(
        f"/api/v1/creative-generation-requests/{request['id']}",
        json={"organization_id": org_id, "status": "submitted"},
    )
    provider = client.post(
        "/api/v1/creative-providers",
        json={
            "organization_id": org_id,
            "provider_name": "abstract-provider",
            "provider_type": "image",
            "capabilities": ["image_generation"],
            "cost_model": {"currency": "USD"},
            "availability": True,
        },
    ).json()
    job = client.post(
        "/api/v1/creative-generation-jobs",
        json={
            "organization_id": org_id,
            "request_id": request["id"],
            "provider": provider["id"],
            "input_reference": f"brief://{brief.id}",
            "estimated_cost": "1.1250004",
        },
    ).json()
    return provider, job


def test_adapter_contract_is_abstract_and_has_no_implementation() -> None:
    assert CreativeExecutionAdapter.__abstractmethods__ == {
        "execute",
        "validate_output",
        "estimate_cost",
    }
    with pytest.raises(TypeError):
        CreativeExecutionAdapter()


def test_state_machine_records_artifact_cost_and_authority_boundary(
    client: TestClient, db_session: Session
) -> None:
    organization, user, brief, asset = foundation(db_session, "workflow")
    provider, job = create_job(client, organization, user, brief)
    org_id = str(organization.id)
    for status in ("queued", "running", "validating", "succeeded"):
        response = client.patch(
            f"/api/v1/creative-generation-jobs/{job['id']}",
            json={"organization_id": org_id, "status": status},
        )
        assert response.status_code == 200
        job = response.json()
    assert job["started_at"] is not None and job["completed_at"] is not None
    invalid = client.patch(
        f"/api/v1/creative-generation-jobs/{job['id']}",
        json={"organization_id": org_id, "status": "retrying"},
    )
    assert invalid.status_code == 409
    record = client.post(
        "/api/v1/creative-execution-records",
        json={
            "organization_id": org_id,
            "generation_job_id": job["id"],
            "provider": provider["id"],
            "execution_status": "succeeded",
            "input_snapshot": {"brief_id": str(brief.id), "network_call": False},
            "output_reference": "artifact://future-output-1",
            "estimated_cost": "1.1250004",
            "actual_cost": "1.2500004",
            "duration": 2.5,
        },
    )
    assert record.status_code == 201
    assert Decimal(record.json()["actual_cost"]) == Decimal("1.250000")
    artifact = client.post(
        "/api/v1/creative-artifacts",
        json={
            "organization_id": org_id,
            "generation_job_id": job["id"],
            "asset_id": str(asset.id),
            "artifact_type": "image",
            "artifact_reference": "artifact://future-output-1",
            "validation_status": "valid",
            "metadata": {"published": False},
        },
    )
    assert artifact.status_code == 201 and artifact.json()["metadata"]["published"] is False
    cost = client.post(
        "/api/v1/creative-generation-costs",
        json={
            "organization_id": org_id,
            "provider": provider["id"],
            "job": job["id"],
            "estimated_cost": "1.125",
            "actual_cost": "1.25",
            "currency": "USD",
        },
    )
    assert cost.status_code == 201 and cost.json()["timestamp"]
    assert db_session.scalar(select(func.count()).select_from(ApprovalRequest)) == 0
    assert client.post("/api/v1/creative-artifacts/publish", json={}).status_code in {404, 405, 422}


def test_execution_tenant_isolation_and_failed_reason(
    client: TestClient, db_session: Session
) -> None:
    owner, user, brief, _ = foundation(db_session, "owner")
    other, _, _, _ = foundation(db_session, "other")
    _, job = create_job(client, owner, user, brief)
    response = client.patch(
        f"/api/v1/creative-generation-jobs/{job['id']}",
        json={"organization_id": str(other.id), "status": "queued"},
    )
    assert response.status_code == 403
    org_id = str(owner.id)
    client.patch(
        f"/api/v1/creative-generation-jobs/{job['id']}",
        json={"organization_id": org_id, "status": "queued"},
    )
    client.patch(
        f"/api/v1/creative-generation-jobs/{job['id']}",
        json={"organization_id": org_id, "status": "running"},
    )
    missing = client.patch(
        f"/api/v1/creative-generation-jobs/{job['id']}",
        json={"organization_id": org_id, "status": "failed"},
    )
    assert missing.status_code == 409
    failed = client.patch(
        f"/api/v1/creative-generation-jobs/{job['id']}",
        json={
            "organization_id": org_id,
            "status": "failed",
            "failure_reason": "Recorded adapter failure",
        },
    )
    assert (
        failed.status_code == 200 and failed.json()["failure_reason"] == "Recorded adapter failure"
    )
