from commerce_os.governance.authentication import AuthenticationService
from commerce_os.governance.models import AuditLog, Organization, Permission, Role, User
from commerce_os.governance.rbac import RbacService
from commerce_os.operations.models import Brand
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session


def setup_authority(session: Session) -> tuple[Organization, Brand, User, User]:
    organization = Organization(name="Truth API", slug="truth-api")
    session.add(organization)
    session.flush()
    brand = Brand(organization_id=organization.id, name="Truth Brand", slug="truth-brand")
    session.add(brand)
    session.commit()
    auth = AuthenticationService(session)
    requester = auth.create_user(
        organization_id=organization.id,
        email="requester@example.com",
        display_name="Requester",
        password="correct horse battery staple",
    )
    approver = auth.create_user(
        organization_id=organization.id,
        email="approver@example.com",
        display_name="Approver",
        password="correct horse battery staple",
    )
    role = Role(
        organization_id=organization.id, name="approver", grants_human_approval_authority=True
    )
    permission = Permission(
        key="approval.decide",
        resource="approval",
        action="decide",
        is_human_approval_permission=True,
    )
    session.add_all([role, permission])
    session.commit()
    rbac = RbacService(session)
    rbac.grant_permission(role_id=role.id, permission_id=permission.id, actor_id=requester.id)
    rbac.assign_role(
        user_id=approver.id,
        role_id=role.id,
        organization_id=organization.id,
        project_id=None,
        assigned_by=requester.id,
    )
    return organization, brand, requester, approver


def test_approval_creates_versioned_product_truth_and_enables_activation(
    client: TestClient, db_session: Session
) -> None:
    organization, brand, requester, approver = setup_authority(db_session)
    product_response = client.post(
        "/api/v1/products",
        json={
            "organization_id": str(organization.id),
            "brand_id": str(brand.id),
            "name": "Care Kit",
            "description": "Approved care product",
            "category": "Care",
        },
    )
    assert product_response.status_code == 201
    product = product_response.json()
    approval = client.post(
        f"/api/v1/products/{product['id']}/approval",
        params={"organization_id": str(organization.id)},
        headers={"X-Actor-ID": str(requester.id)},
        json={"reason": "Publish verified product facts"},
    )
    assert approval.status_code == 201
    truth_payload = {
        "organization_id": str(organization.id),
        "product_id": product["id"],
        "approval_id": approval.json()["id"],
        "summary": "A verified care kit.",
        "features": ["Reusable"],
        "specifications": {"material": "cotton"},
        "approved_claims": ["Reusable"],
        "restricted_claims": ["Cures illness"],
        "usage_notes": "Follow care instructions.",
    }
    pending_truth = client.post(
        "/api/v1/product-truth",
        headers={"X-Actor-ID": str(requester.id)},
        json=truth_payload,
    )
    assert pending_truth.status_code == 409
    decision = client.post(
        f"/api/v1/approvals/{approval.json()['id']}/decision",
        headers={"X-Actor-ID": str(approver.id)},
        json={"decision": "approved", "reason": "Evidence reviewed"},
    )
    assert decision.status_code == 200
    truth = client.post(
        "/api/v1/product-truth",
        headers={"X-Actor-ID": str(requester.id)},
        json=truth_payload,
    )
    assert truth.status_code == 201
    assert truth.json()["version"] == 1
    activation = client.patch(
        f"/api/v1/products/{product['id']}",
        params={"organization_id": str(organization.id)},
        json={"status": "active"},
    )
    assert activation.status_code == 200
    assert activation.json()["status"] == "active"
    second_approval = client.post(
        f"/api/v1/products/{product['id']}/approval",
        params={"organization_id": str(organization.id)},
        headers={"X-Actor-ID": str(requester.id)},
        json={"reason": "Publish corrected product facts"},
    ).json()
    client.post(
        f"/api/v1/approvals/{second_approval['id']}/decision",
        headers={"X-Actor-ID": str(approver.id)},
        json={"decision": "approved", "reason": "Correction reviewed"},
    )
    truth_payload.update(
        {"approval_id": second_approval["id"], "summary": "A corrected verified care kit."}
    )
    second_truth = client.post(
        "/api/v1/product-truth",
        headers={"X-Actor-ID": str(requester.id)},
        json=truth_payload,
    )
    assert second_truth.status_code == 201
    assert second_truth.json()["version"] == 2
    knowledge = client.post(
        "/api/v1/product-knowledge",
        json={
            "organization_id": str(organization.id),
            "product_id": product["id"],
            "type": "faq",
            "content": "Is it reusable? Yes.",
            "confidence": 0.9,
            "approval_status": "approved",
        },
    )
    assert knowledge.status_code == 201
    policy = client.post(
        "/api/v1/product-claim-policies",
        json={
            "organization_id": str(organization.id),
            "brand_id": str(brand.id),
            "claim_type": "medical",
            "allowed": False,
            "reason": "Prohibited without review",
            "evidence_required": True,
        },
    )
    assert policy.status_code == 201
    actions = set(db_session.scalars(select(AuditLog.action)))
    assert "product_truth.created" in actions
    for endpoint in ("products", "product-knowledge", "product-claim-policies"):
        result = client.get(f"/api/v1/{endpoint}", params={"organization_id": str(organization.id)})
        assert result.status_code == 200
        assert len(result.json()) == 1
    truth_list = client.get(
        "/api/v1/product-truth", params={"organization_id": str(organization.id)}
    )
    assert [item["version"] for item in truth_list.json()] == [2, 1]
