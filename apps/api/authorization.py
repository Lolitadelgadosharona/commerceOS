from typing import Annotated, Any
from uuid import UUID

from commerce_os.governance.models import PrincipalType
from commerce_os.governance.rbac import RbacService
from commerce_os.governance.sessions import SessionService
from commerce_os.shared.database import get_session
from fastapi import Depends, Request
from sqlalchemy.orm import Session

from apps.api.errors import ApiError

PUBLIC_PATHS = {
    "/api/v1/health",
    "/api/v1/auth/login",
    "/api/v1/shopify/webhooks",
    "/docs",
    "/openapi.json",
}


async def enforce_authorization(
    request: Request, session: Annotated[Session, Depends(get_session)]
) -> None:
    if request.url.path in PUBLIC_PATHS or getattr(request.app.state, "auth_test_bypass", False):
        return
    header = request.headers.get("authorization", "")
    if not header.startswith("Bearer "):
        raise ApiError(401, "unauthenticated", "Bearer authentication required.")
    verified = SessionService(session).verify(header[7:])
    if verified is None:
        raise ApiError(401, "invalid_session", "Session is invalid, expired, or revoked.")
    user, auth_session = verified
    request.state.actor = user
    request.state.auth_session = auth_session
    requested_org = await organization_scope(request)
    if requested_org is not None and requested_org != user.organization_id:
        raise ApiError(403, "wrong_organization", "Actor cannot access this organization.")
    permission = "api.read" if request.method in {"GET", "HEAD", "OPTIONS"} else "api.write"
    if not RbacService(session).has_permission(
        user_id=user.id, organization_id=user.organization_id, permission_key=permission
    ):
        raise ApiError(403, "permission_denied", f"Missing permission: {permission}.")
    if request.url.path.endswith("/approvals") and user.principal_type == PrincipalType.SERVICE:
        raise ApiError(
            403,
            "human_authority_required",
            "Service accounts cannot exercise human approval authority.",
        )


async def organization_scope(request: Request) -> UUID | None:
    raw = request.query_params.get("organization_id")
    if raw is None and request.method not in {"GET", "HEAD"}:
        try:
            body: Any = await request.json()
            raw = body.get("organization_id") if isinstance(body, dict) else None
        except Exception:
            raw = None
    if raw is None:
        return None
    try:
        return UUID(str(raw))
    except ValueError:
        raise ApiError(422, "invalid_organization", "organization_id must be a UUID.") from None
