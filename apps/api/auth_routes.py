from typing import Annotated
from uuid import UUID

from commerce_os.governance.authentication import AuthenticationService
from commerce_os.governance.models import AuthSession, User
from commerce_os.governance.sessions import SessionService
from commerce_os.shared.database import get_session
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, EmailStr, SecretStr
from sqlalchemy.orm import Session

from apps.api.errors import ApiError

router = APIRouter()
SessionDependency = Annotated[Session, Depends(get_session)]


class LoginRequest(BaseModel):
    organization_id: UUID
    email: EmailStr
    password: SecretStr


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: str
    organization_id: UUID
    user_id: UUID


@router.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, session: SessionDependency) -> TokenResponse:
    user = AuthenticationService(session).authenticate_password(
        organization_id=payload.organization_id,
        email=str(payload.email),
        password=payload.password.get_secret_value(),
    )
    if user is None:
        raise ApiError(401, "invalid_credentials", "Invalid credentials.")
    token, record = SessionService(session).issue(user)
    return TokenResponse(
        access_token=token,
        expires_at=record.expires_at.isoformat(),
        organization_id=user.organization_id,
        user_id=user.id,
    )


@router.post("/auth/logout", status_code=204)
def logout(request: Request, session: SessionDependency) -> None:
    user = getattr(request.state, "actor", None)
    auth_session = getattr(request.state, "auth_session", None)
    if not isinstance(user, User) or not isinstance(auth_session, AuthSession):
        raise ApiError(401, "unauthenticated", "Authentication required.")
    SessionService(session).revoke(user, auth_session)


@router.get("/auth/me")
def me(request: Request) -> dict[str, str]:
    user = getattr(request.state, "actor", None)
    if not isinstance(user, User):
        raise ApiError(401, "unauthenticated", "Authentication required.")
    return {
        "user_id": str(user.id),
        "organization_id": str(user.organization_id),
        "principal_type": str(user.principal_type),
    }
