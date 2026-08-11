from datetime import UTC, datetime
from uuid import UUID, uuid4

from commerce_os.build.creative_asset_models import CreativeAsset, CreativeAssetVersion
from commerce_os.build.models import Product, ProductTruth
from commerce_os.finance.models import RevenueObservation
from commerce_os.governance.models import (
    ApprovalRequest,
    ApprovalStatus,
    Organization,
    Project,
    User,
)
from commerce_os.operations.models import Brand
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session


def foundation(
    session: Session, slug: str
) -> tuple[Organization, Project, User, CreativeAsset, CreativeAssetVersion]:
    organization = Organization(name=f"Channel {slug}", slug=f"channel-{slug}")
    session.add(organization)
    session.flush()
    project = Project(
        organization_id=organization.id, name="Channel project", slug=f"channel-project-{slug}"
    )
    user = User(
        organization_id=organization.id,
        email=f"channel-{slug}@example.com",
        display_name="Growth operator",
        status="active",
        principal_type="human",
    )
    brand = Brand(
        organization_id=organization.id, name=f"Brand {slug}", slug=f"channel-brand-{slug}"
    )
    session.add_all([project, user, brand])
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
    asset = CreativeAsset(
        organization_id=organization.id,
        product_id=product.id,
        asset_type="image",
        status="draft",
        source="internal://registry",
        asset_metadata={},
        approval_status="pending",
    )
    session.add(asset)
    session.flush()
    version = CreativeAssetVersion(
        organization_id=organization.id,
        asset_id=asset.id,
        version_number=1,
        variation_reason="Channel test",
        experiment_group="a",
    )
    session.add(version)
    session.commit()
    return organization, project, user, asset, version


def approval(
    session: Session,
    organization: Organization,
    project: Project,
    user: User,
    object_type: str,
    object_id: UUID,
    action: str,
) -> ApprovalRequest:
    item = ApprovalRequest(
        organization_id=organization.id,
        project_id=project.id,
        requester_id=user.id,
        object_type=object_type,
        object_id=object_id,
        requested_action=action,
        reason="Human authorization",
        status=ApprovalStatus.APPROVED,
        approver_id=user.id,
    )
    session.add(item)
    session.commit()
    return item


def test_channel_plan_experiment_distribution_performance_and_authority(
    client: TestClient, db_session: Session
) -> None:
    organization, project, user, asset, version = foundation(db_session, "workflow")
    base = {"organization_id": str(organization.id)}
    plan = client.post(
        "/api/v1/channel-execution-plans",
        json=base
        | {
            "project_id": str(project.id),
            "channel": "pinterest",
            "creative_asset_id": str(asset.id),
            "objective": "Plan an evidence-led test",
            "target_audience": "Home owners",
            "execution_type": "experiment",
            "created_by": str(user.id),
        },
    )
    assert plan.status_code == 201 and plan.json()["status"] == "draft"
    plan_id = plan.json()["id"]
    assert client.get(f"/api/v1/channel-execution-plans/{plan_id}", params=base).status_code == 200
    assert (
        client.patch(
            f"/api/v1/channel-execution-plans/{plan_id}", json=base | {"status": "ready"}
        ).status_code
        == 200
    )
    blocked_plan = client.patch(
        f"/api/v1/channel-execution-plans/{plan_id}", json=base | {"status": "approved"}
    )
    assert blocked_plan.status_code == 409
    plan_approval = approval(
        db_session,
        organization,
        project,
        user,
        "channel_execution_plan",
        UUID(plan_id),
        "approve_channel_execution",
    )
    assert (
        client.patch(
            f"/api/v1/channel-execution-plans/{plan_id}",
            json=base | {"status": "approved", "approval_request_id": str(plan_approval.id)},
        ).status_code
        == 200
    )
    experiment = client.post(
        "/api/v1/channel-experiments",
        json=base
        | {
            "channel_execution_plan_id": plan_id,
            "hypothesis": "Problem hooks outperform feature hooks",
            "creative_variant_ids": [str(version.id)],
            "success_metrics": ["ctr", "engagement", "contribution_profit"],
            "test_notes": "Design only",
        },
    )
    assert experiment.status_code == 201
    distribution = client.post(
        "/api/v1/distribution-records",
        json=base
        | {
            "creative_asset_id": str(asset.id),
            "channel": "pinterest",
            "scheduled_time": datetime.now(UTC).isoformat(),
        },
    )
    assert distribution.status_code == 201
    distribution_id = distribution.json()["id"]
    client.patch(
        f"/api/v1/distribution-records/{distribution_id}",
        json=base | {"distribution_status": "ready"},
    )
    blocked = client.patch(
        f"/api/v1/distribution-records/{distribution_id}",
        json=base | {"distribution_status": "approved"},
    )
    assert blocked.status_code == 409
    publish_approval = approval(
        db_session,
        organization,
        project,
        user,
        "distribution_record",
        UUID(distribution_id),
        "approve_distribution",
    )
    approved = client.patch(
        f"/api/v1/distribution-records/{distribution_id}",
        json=base
        | {"distribution_status": "approved", "approval_request_id": str(publish_approval.id)},
    )
    assert approved.status_code == 200
    published = client.patch(
        f"/api/v1/distribution-records/{distribution_id}",
        json=base
        | {
            "distribution_status": "published",
            "published_reference": "planned://future-channel-reference",
            "actual_time": datetime.now(UTC).isoformat(),
        },
    )
    assert published.status_code == 200 and published.json()["distribution_status"] == "published"
    finance_before = db_session.scalar(select(func.count()).select_from(RevenueObservation))
    truth_before = db_session.scalar(select(func.count()).select_from(ProductTruth))
    performance = client.post(
        "/api/v1/channel-performance",
        json=base
        | {
            "channel": "pinterest",
            "creative_asset_id": str(asset.id),
            "experiment_id": experiment.json()["id"],
            "metric_name": "outbound_clicks",
            "metric_value": "12.1234564",
            "source": "manual://observation",
            "observed_at": datetime.now(UTC).isoformat(),
        },
    )
    assert performance.status_code == 201 and performance.json()["metric_value"] == "12.123456"
    assert db_session.scalar(select(func.count()).select_from(RevenueObservation)) == finance_before
    assert db_session.scalar(select(func.count()).select_from(ProductTruth)) == truth_before


def test_invalid_asset_and_tenant_isolation(client: TestClient, db_session: Session) -> None:
    owner, project, user, asset, _ = foundation(db_session, "owner")
    other, _, _, _, _ = foundation(db_session, "other")
    invalid = client.post(
        "/api/v1/channel-execution-plans",
        json={
            "organization_id": str(owner.id),
            "project_id": str(project.id),
            "channel": "meta",
            "creative_asset_id": str(uuid4()),
            "objective": "Invalid",
            "target_audience": "Audience",
            "execution_type": "organic",
            "created_by": str(user.id),
        },
    )
    assert invalid.status_code == 404
    cross_tenant = client.post(
        "/api/v1/distribution-records",
        json={
            "organization_id": str(other.id),
            "creative_asset_id": str(asset.id),
            "channel": "meta",
        },
    )
    assert cross_tenant.status_code == 404
