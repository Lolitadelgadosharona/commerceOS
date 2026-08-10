from uuid import UUID

import pytest
from commerce_os.build.models import Product
from commerce_os.governance.models import (
    ApprovalRequest,
    ApprovalStatus,
    Organization,
    Project,
    User,
)
from commerce_os.operations.errors import OperationsError
from commerce_os.operations.execution_schemas import ProductLaunchCreate
from commerce_os.operations.execution_services import LaunchExecutionService
from commerce_os.operations.models import Brand
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def foundation(session: Session, slug: str):
    organization = Organization(name=f"Execution {slug}", slug=slug)
    session.add(organization)
    session.flush()
    project = Project(
        organization_id=organization.id, name="Launch Project", slug=f"{slug}-project"
    )
    brand = Brand(organization_id=organization.id, name="Launch Brand", slug=f"{slug}-brand")
    requester = User(
        organization_id=organization.id,
        email=f"{slug}@example.com",
        display_name="Requester",
        status="active",
        principal_type="human",
    )
    session.add_all([project, brand, requester])
    session.flush()
    product = Product(
        organization_id=organization.id,
        brand_id=brand.id,
        name="Launch Product",
        description="Approved product",
        category="Test",
        status="approved",
    )
    session.add(product)
    session.commit()
    return organization, project, product, requester


def approved_request(
    session: Session, organization: Organization, project: Project, requester: User, launch_id
) -> ApprovalRequest:
    approval = ApprovalRequest(
        organization_id=organization.id,
        project_id=project.id,
        requester_id=requester.id,
        object_type="product_launch",
        object_id=launch_id,
        requested_action="approve_launch",
        reason="Human-approved launch authorization.",
        status=ApprovalStatus.APPROVED,
        approver_id=requester.id,
    )
    session.add(approval)
    session.commit()
    return approval


def test_launch_lifecycle_approval_and_tenant_boundaries(db_session: Session) -> None:
    organization, project, product, requester = foundation(db_session, "launch")
    other, _, _, _ = foundation(db_session, "launch-other")
    service = LaunchExecutionService(db_session)
    launch = service.create_launch(
        ProductLaunchCreate(
            organization_id=organization.id,
            project_id=project.id,
            product_id=product.id,
            market="US",
            priority="high",
        )
    )
    assert launch.status == "draft"
    with pytest.raises(OperationsError):
        service.transition_launch(launch, "approved", None)
    approval = approved_request(db_session, organization, project, requester, launch.id)
    assert service.transition_launch(launch, "approved", approval.id).status == "approved"
    assert service.transition_launch(launch, "in_progress", None).status == "in_progress"
    with pytest.raises(OperationsError):
        service.create_launch(
            ProductLaunchCreate(
                organization_id=other.id,
                project_id=project.id,
                product_id=product.id,
                market="US",
                priority="low",
            )
        )


def test_execution_api_ordering_tasks_blockers_and_boundaries(
    client: TestClient, db_session: Session
) -> None:
    organization, project, product, requester = foundation(db_session, "launch-api")
    base = {"organization_id": str(organization.id)}
    launch = client.post(
        "/api/v1/product-launches",
        json=base
        | {
            "project_id": str(project.id),
            "product_id": str(product.id),
            "market": "North America",
            "priority": "critical",
        },
    )
    assert launch.status_code == 201
    launch_id = launch.json()["id"]
    approval = approved_request(db_session, organization, project, requester, UUID(launch_id))
    response = client.patch(
        f"/api/v1/product-launches/{launch_id}",
        params=base,
        json={"status": "approved", "approval_request_id": str(approval.id)},
    )
    assert response.json()["status"] == "approved"
    client.patch(
        f"/api/v1/product-launches/{launch_id}", params=base, json={"status": "in_progress"}
    )
    for sequence, name in ((2, "supplier_ready"), (1, "product_approval")):
        response = client.post(
            "/api/v1/launch-milestones",
            json=base
            | {
                "launch_id": launch_id,
                "name": name,
                "sequence": sequence,
            },
        )
        assert response.status_code == 201
    milestones = client.get("/api/v1/launch-milestones", params=base).json()
    assert [item["sequence"] for item in milestones] == [1, 2]
    task = client.post(
        "/api/v1/execution-tasks",
        json=base
        | {
            "launch_id": launch_id,
            "title": "Prepare a draft checklist",
            "description": "AI ownership is a label only; no execution occurs.",
            "owner_type": "ai",
            "priority": "medium",
        },
    )
    assert task.status_code == 201
    assert task.json()["owner_type"] == "ai"
    assert task.json()["status"] == "todo"
    plan = client.post(
        "/api/v1/action-plans",
        json=base
        | {
            "plan_date": "2026-08-10",
            "related_launch_id": launch_id,
            "priority": "high",
            "summary": "Human-reviewed daily launch actions.",
            "generated_from": "manual",
        },
    )
    assert plan.status_code == 201
    blocker = client.post(
        "/api/v1/execution-blockers",
        json=base
        | {
            "launch_id": launch_id,
            "reason": "Supplier evidence missing.",
            "severity": "high",
            "impact": "Launch cannot safely proceed.",
        },
    )
    assert blocker.status_code == 201
    refreshed = client.get("/api/v1/product-launches", params=base).json()[0]
    assert refreshed["status"] == "blocked"
    assert client.post("/api/v1/execution-tasks/execute", json={}).status_code in {404, 405, 422}
    assert client.post("/api/v1/publish", json={}).status_code == 404
    for endpoint in (
        "product-launches",
        "launch-milestones",
        "execution-tasks",
        "action-plans",
        "execution-blockers",
    ):
        assert client.get(f"/api/v1/{endpoint}", params=base).status_code == 200
