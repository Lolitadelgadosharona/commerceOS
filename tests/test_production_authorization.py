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
