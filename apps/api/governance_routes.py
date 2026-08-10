"""Internal governance APIs; authentication tokens are intentionally deferred."""

# FastAPI represents dependencies in function defaults by design.
# ruff: noqa: B008

from uuid import UUID

from commerce_os.governance.approvals import ApprovalWorkflowService
from commerce_os.governance.authentication import AuthenticationService
from commerce_os.governance.identity import CustomerIdentityService
from commerce_os.governance.models import (
    ApprovalRequest,
    ApprovalStatus,
    AuditLog,
    CustomerIdentity,
    Permission,
    PrincipalType,
    Role,
    User,
    UserRole,
)
from commerce_os.governance.rbac import RbacService
from commerce_os.governance.schemas import (
    ApprovalCancellation,
    ApprovalDecision,
    ApprovalRequestCreate,
    ApprovalRequestRead,
    AuditLogRead,
    CustomerIdentityCreate,
    CustomerIdentityRead,
    PermissionCreate,
    PermissionRead,
    RevokeRoleRequest,
    RoleCreate,
    RolePermissionCreate,
    RoleRead,
    RoleUpdate,
    UserCreate,
    UserRead,
    UserRoleCreate,
    UserRoleRead,
    UserUpdate,
)
from commerce_os.shared.database import get_session
from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

router = APIRouter()


def actor_id(x_actor_id: UUID = Header(alias="X-Actor-ID")) -> UUID:
    """Temporary internal actor boundary; token authentication is outside Sprint 002."""
    return x_actor_id


@router.post("/users", response_model=UserRead, status_code=201, tags=["users"])
def create_user(payload: UserCreate, session: Session = Depends(get_session)) -> User:
    return AuthenticationService(session).create_user(
        organization_id=payload.organization_id,
        email=str(payload.email),
        display_name=payload.display_name,
        password=payload.password.get_secret_value(),
        principal_type=PrincipalType(payload.principal_type),
    )


@router.get("/users", response_model=list[UserRead], tags=["users"])
def list_users(organization_id: UUID, session: Session = Depends(get_session)) -> list[User]:
    return list(session.scalars(select(User).where(User.organization_id == organization_id)))


@router.get("/users/{user_id}", response_model=UserRead, tags=["users"])
def get_user(user_id: UUID, session: Session = Depends(get_session)) -> User:
    from commerce_os.governance.errors import NotFoundError

    user = session.get(User, user_id)
    if user is None:
        raise NotFoundError("User was not found.")
    return user


@router.patch("/users/{user_id}", response_model=UserRead, tags=["users"])
def update_user(
    user_id: UUID,
    payload: UserUpdate,
    actor: UUID = Depends(actor_id),
    session: Session = Depends(get_session),
) -> User:
    from commerce_os.governance.audit import AuditService
    from commerce_os.governance.errors import NotFoundError

    user = session.get(User, user_id)
    if user is None:
        raise NotFoundError("User was not found.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    AuditService(session).record(
        organization_id=user.organization_id,
        actor_type="human",
        actor_id=actor,
        action="user.updated",
        entity_type="user",
        entity_id=user.id,
        metadata={"fields": list(payload.model_fields_set)},
    )
    session.commit()
    session.refresh(user)
    return user


@router.post("/roles", response_model=RoleRead, status_code=201, tags=["roles"])
def create_role(
    payload: RoleCreate,
    actor: UUID = Depends(actor_id),
    session: Session = Depends(get_session),
) -> Role:
    from commerce_os.governance.audit import AuditService

    role = Role(**payload.model_dump())
    session.add(role)
    session.flush()
    AuditService(session).record(
        organization_id=role.organization_id,
        actor_type="human",
        actor_id=actor,
        action="role.created",
        entity_type="role",
        entity_id=role.id,
    )
    session.commit()
    session.refresh(role)
    return role


@router.get("/roles", response_model=list[RoleRead], tags=["roles"])
def list_roles(organization_id: UUID, session: Session = Depends(get_session)) -> list[Role]:
    return list(session.scalars(select(Role).where(Role.organization_id == organization_id)))


@router.patch("/roles/{role_id}", response_model=RoleRead, tags=["roles"])
def update_role(
    role_id: UUID,
    payload: RoleUpdate,
    actor: UUID = Depends(actor_id),
    session: Session = Depends(get_session),
) -> Role:
    from commerce_os.governance.audit import AuditService
    from commerce_os.governance.errors import NotFoundError

    role = session.get(Role, role_id)
    if role is None:
        raise NotFoundError("Role was not found.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(role, field, value)
    AuditService(session).record(
        organization_id=role.organization_id,
        actor_type="human",
        actor_id=actor,
        action="role.updated",
        entity_type="role",
        entity_id=role.id,
    )
    session.commit()
    session.refresh(role)
    return role


@router.post("/permissions", response_model=PermissionRead, status_code=201, tags=["permissions"])
def create_permission(
    payload: PermissionCreate, session: Session = Depends(get_session)
) -> Permission:
    permission = Permission(**payload.model_dump())
    session.add(permission)
    session.commit()
    session.refresh(permission)
    return permission


@router.get("/permissions", response_model=list[PermissionRead], tags=["permissions"])
def list_permissions(session: Session = Depends(get_session)) -> list[Permission]:
    return list(session.scalars(select(Permission)))


@router.post("/roles/{role_id}/permissions", status_code=204, tags=["roles"])
def grant_permission(
    role_id: UUID,
    payload: RolePermissionCreate,
    actor: UUID = Depends(actor_id),
    session: Session = Depends(get_session),
) -> None:
    RbacService(session).grant_permission(
        role_id=role_id, permission_id=payload.permission_id, actor_id=actor
    )


@router.post("/role-assignments", response_model=UserRoleRead, status_code=201, tags=["roles"])
def assign_role(
    payload: UserRoleCreate,
    actor: UUID = Depends(actor_id),
    session: Session = Depends(get_session),
) -> UserRole:
    return RbacService(session).assign_role(**payload.model_dump(), assigned_by=actor)


@router.post(
    "/role-assignments/{assignment_id}/revoke", response_model=UserRoleRead, tags=["roles"]
)
def revoke_role(
    assignment_id: UUID,
    payload: RevokeRoleRequest,
    actor: UUID = Depends(actor_id),
    session: Session = Depends(get_session),
) -> UserRole:
    return RbacService(session).revoke_role(
        assignment_id=assignment_id, revoked_by=actor, reason=payload.reason
    )


@router.post("/approvals", response_model=ApprovalRequestRead, status_code=201, tags=["approvals"])
def request_approval(
    payload: ApprovalRequestCreate,
    actor: UUID = Depends(actor_id),
    session: Session = Depends(get_session),
) -> ApprovalRequest:
    return ApprovalWorkflowService(session).request(**payload.model_dump(), requester_id=actor)


@router.get("/approvals", response_model=list[ApprovalRequestRead], tags=["approvals"])
def list_approvals(
    organization_id: UUID,
    status: ApprovalStatus | None = None,
    session: Session = Depends(get_session),
) -> list[ApprovalRequest]:
    statement = select(ApprovalRequest).where(ApprovalRequest.organization_id == organization_id)
    if status is not None:
        statement = statement.where(ApprovalRequest.status == status)
    return list(session.scalars(statement.order_by(ApprovalRequest.created_at.desc())))


@router.post(
    "/approvals/{approval_id}/decision", response_model=ApprovalRequestRead, tags=["approvals"]
)
def decide_approval(
    approval_id: UUID,
    payload: ApprovalDecision,
    actor: UUID = Depends(actor_id),
    session: Session = Depends(get_session),
) -> ApprovalRequest:
    return ApprovalWorkflowService(session).decide(
        approval_id=approval_id,
        approver_id=actor,
        decision=ApprovalStatus(payload.decision),
        reason=payload.reason,
    )


@router.post(
    "/approvals/{approval_id}/cancel", response_model=ApprovalRequestRead, tags=["approvals"]
)
def cancel_approval(
    approval_id: UUID,
    payload: ApprovalCancellation,
    actor: UUID = Depends(actor_id),
    session: Session = Depends(get_session),
) -> ApprovalRequest:
    return ApprovalWorkflowService(session).cancel(
        approval_id=approval_id, requester_id=actor, reason=payload.reason
    )


@router.get("/audit-logs", response_model=list[AuditLogRead], tags=["audit_logs"])
def list_audit_logs(
    organization_id: UUID,
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_session),
) -> list[AuditLog]:
    return list(
        session.scalars(
            select(AuditLog)
            .where(AuditLog.organization_id == organization_id)
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
        )
    )


@router.post(
    "/customer-identities",
    response_model=CustomerIdentityRead,
    status_code=201,
    tags=["customer_identities"],
)
def create_customer_identity(
    payload: CustomerIdentityCreate, session: Session = Depends(get_session)
) -> CustomerIdentity:
    return CustomerIdentityService(session).observe(payload)


@router.get(
    "/customer-identities",
    response_model=list[CustomerIdentityRead],
    tags=["customer_identities"],
)
def list_customer_identities(
    customer_id: UUID, session: Session = Depends(get_session)
) -> list[CustomerIdentity]:
    return list(
        session.scalars(select(CustomerIdentity).where(CustomerIdentity.customer_id == customer_id))
    )
