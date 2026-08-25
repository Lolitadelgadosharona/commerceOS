from datetime import timedelta

import pytest
from commerce_os.governance.authentication import AuthenticationService
from commerce_os.governance.models import (
    AuditLog,
    Organization,
    Permission,
    Role,
    RolePermission,
    User,
    UserRole,
)
from commerce_os.governance.sessions import SessionService
from commerce_os.intelligence.opportunity_models import MarketOpportunity
from commerce_os.shared.models import utc_now
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.main import app
from apps.worker.main import WORKER_PRINCIPAL


@pytest.fixture
def production_auth() -> None:
    app.state.auth_test_bypass = False
    yield
    app.state.auth_test_bypass = True


def authorized_user(
    session: Session, slug: str, permissions: tuple[str, ...]
) -> tuple[Organization, str]:
    organization = Organization(name=f"Auth {slug}", slug=f"auth-{slug}")
    session.add(organization)
    session.commit()
    user = AuthenticationService(session).create_user(
        organization_id=organization.id,
        email=f"{slug}@example.com",
        display_name="Operator",
        password="correct horse battery staple",
    )
    role = Role(
        organization_id=organization.id,
        name=f"role-{slug}",
        description="Test role",
        grants_human_approval_authority=False,
        is_active=True,
    )
    session.add(role)
    session.flush()
    assignment = UserRole(
        user_id=user.id,
        role_id=role.id,
        organization_id=organization.id,
        project_id=None,
        assigned_by=user.id,
        assigned_at=utc_now(),
    )
    session.add(assignment)
    for key in permissions:
        permission = session.scalar(select(Permission).where(Permission.key == key))
        if permission is None:
            permission = Permission(
                key=key,
                resource="api",
                action=key.split(".")[-1],
                description="Universal API access",
                is_human_approval_permission=False,
            )
            session.add(permission)
            session.flush()
        session.add(RolePermission(role_id=role.id, permission_id=permission.id))
    session.commit()
    token, _ = SessionService(session).issue(user)
    return organization, token


def test_universal_authentication_scope_permission_logout_and_audit(
    client: TestClient, db_session: Session, production_auth: None
) -> None:
    organization, token = authorized_user(db_session, "allowed", ("api.read", "api.write"))
    other = Organization(name="Other", slug="auth-other")
    db_session.add(other)
    db_session.commit()
    assert (
        client.get("/api/v1/organizations", params={"organization_id": organization.id}).status_code
        == 401
    )
    headers = {"Authorization": f"Bearer {token}"}
    allowed = client.get(
        "/api/v1/organizations", params={"organization_id": organization.id}, headers=headers
    )
    assert allowed.status_code == 200
    assert (
        client.get(
            "/api/v1/organizations", params={"organization_id": other.id}, headers=headers
        ).status_code
        == 403
    )
    me = client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200 and me.json()["organization_id"] == str(organization.id)
    assert client.post("/api/v1/auth/logout", headers=headers).status_code == 204
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 401
    actions = set(db_session.scalars(select(AuditLog.action)))
    assert "authentication.session_created" in actions and "authentication.logout" in actions


def test_missing_permission_expiration_and_login(
    client: TestClient, db_session: Session, production_auth: None
) -> None:
    organization, read_token = authorized_user(db_session, "readonly", ("api.read",))
    headers = {"Authorization": f"Bearer {read_token}"}
    denied = client.post(
        "/api/v1/projects",
        json={"organization_id": str(organization.id), "name": "Denied", "slug": "denied"},
        headers=headers,
    )
    assert denied.status_code == 403
    login = client.post(
        "/api/v1/auth/login",
        json={
            "organization_id": str(organization.id),
            "email": "readonly@example.com",
            "password": "correct horse battery staple",
        },
    )
    assert login.status_code == 200 and login.json()["token_type"] == "bearer"
    user = db_session.scalar(select(User).where(User.organization_id == organization.id))
    assert user is not None
    expired_token, record = SessionService(db_session).issue(user, timedelta(seconds=-1))
    assert record.expires_at
    assert (
        client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"}
        ).status_code
        == 401
    )


def test_worker_runtime_identity_is_explicit() -> None:
    assert WORKER_PRINCIPAL == "commerce-os-worker"


def test_market_opportunity_workflow_rejects_cross_tenant_access(
    client: TestClient, db_session: Session, production_auth: None
) -> None:
    organization_a, token_a = authorized_user(
        db_session, "opportunity-a", ("api.read", "api.write", "approval.decide")
    )
    organization_b, token_b = authorized_user(
        db_session, "opportunity-b", ("api.read", "api.write")
    )
    actor_b = db_session.scalar(select(User).where(User.organization_id == organization_b.id))
    assert actor_b is not None
    opportunity_b = MarketOpportunity(
        organization_id=organization_b.id,
        title="Organization B opportunity",
        description="Tenant-isolated market evidence.",
        category="test",
        market="consumer",
        geography="US",
        trigger_type="customer_pain",
        timing_window="current",
        status="qualified",
        confidence_score=0.8,
    )
    db_session.add(opportunity_b)
    db_session.commit()
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    in_scope = client.get(
        f"/api/v1/opportunities/{opportunity_b.id}",
        params={"organization_id": organization_b.id},
        headers=headers_b,
    )
    assert in_scope.status_code == 200 and in_scope.json()["id"] == str(opportunity_b.id)
    assert (
        client.get(f"/api/v1/opportunities/{opportunity_b.id}", headers=headers_a).status_code
        == 422
    )
    assert (
        client.get(
            f"/api/v1/opportunities/{opportunity_b.id}",
            params={"organization_id": organization_b.id},
            headers=headers_a,
        ).status_code
        == 403
    )
    assert (
        client.get(
            f"/api/v1/opportunities/{opportunity_b.id}",
            params={"organization_id": organization_a.id},
            headers=headers_a,
        ).status_code
        == 404
    )
    assert (
        client.patch(
            f"/api/v1/opportunities/{opportunity_b.id}",
            params={"organization_id": organization_a.id},
            json={"status": "rejected"},
            headers=headers_a,
        ).status_code
        == 404
    )

    review = client.post(
        f"/api/v1/opportunities/{opportunity_b.id}/request-investment-review",
        json={
            "organization_id": str(organization_b.id),
            "requester_id": str(actor_b.id),
            "reason": "Organization B review",
        },
        headers=headers_b,
    )
    assert review.status_code == 201
    approval_id = review.json()["approval_request_id"]
    queue_id = review.json()["decision_queue_item_id"]

    assert (
        client.post(
            f"/api/v1/opportunities/{opportunity_b.id}/request-investment-review",
            json={
                "organization_id": str(organization_a.id),
                "requester_id": str(organization_a.id),
                "reason": "Cross-tenant review",
            },
            headers=headers_a,
        ).status_code
        == 404
    )
    assert (
        client.post(
            f"/api/v1/approvals/{approval_id}/decision",
            json={"decision": "approved", "reason": "Cross-tenant decision"},
            headers=headers_a,
        ).status_code
        == 403
    )
    assert (
        client.get(
            "/api/v1/decision-queue",
            params={"organization_id": organization_b.id},
            headers=headers_a,
        ).status_code
        == 403
    )
    scoped_queue = client.get(
        "/api/v1/decision-queue",
        params={"organization_id": organization_a.id},
        headers=headers_a,
    )
    assert scoped_queue.status_code == 200 and scoped_queue.json() == []
    assert (
        client.patch(
            f"/api/v1/decision-queue/{queue_id}",
            params={"organization_id": organization_a.id},
            json={"status": "acknowledged"},
            headers=headers_a,
        ).status_code
        == 404
    )
    assert (
        client.get(
            f"/api/v1/opportunities/{opportunity_b.id}/launch-readiness",
            params={"organization_id": organization_a.id},
            headers=headers_a,
        ).status_code
        == 404
    )
    assert (
        client.post(
            f"/api/v1/opportunities/{opportunity_b.id}/activate-approved-project",
            json={
                "organization_id": str(organization_a.id),
                "approval_request_id": approval_id,
                "project_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
                "product_id": "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
            },
            headers=headers_a,
        ).status_code
        == 404
    )
