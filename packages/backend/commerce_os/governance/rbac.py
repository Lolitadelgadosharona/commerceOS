from uuid import UUID

from sqlalchemy import exists, or_, select
from sqlalchemy.orm import Session

from commerce_os.governance.audit import AuditService
from commerce_os.governance.errors import AuthorityError, NotFoundError
from commerce_os.governance.models import (
    Permission,
    PrincipalType,
    Role,
    RolePermission,
    User,
    UserRole,
)
from commerce_os.shared.models import utc_now


class RbacService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def grant_permission(
        self, *, role_id: UUID, permission_id: UUID, actor_id: UUID
    ) -> RolePermission:
        role = self.session.get(Role, role_id)
        permission = self.session.get(Permission, permission_id)
        if role is None or permission is None:
            raise NotFoundError("Role or permission was not found.")
        if permission.is_human_approval_permission:
            has_service_assignment = self.session.scalar(
                select(
                    exists().where(
                        UserRole.role_id == role.id,
                        UserRole.revoked_at.is_(None),
                        UserRole.user_id == User.id,
                        User.principal_type == PrincipalType.SERVICE,
                    )
                )
            )
            if has_service_assignment:
                raise AuthorityError(
                    "A role assigned to a service principal cannot receive approval authority."
                )
            role.grants_human_approval_authority = True
        mapping = RolePermission(role_id=role.id, permission_id=permission.id)
        self.session.add(mapping)
        AuditService(self.session).record(
            organization_id=role.organization_id,
            actor_type="human",
            actor_id=actor_id,
            action="role.permission_granted",
            entity_type="role",
            entity_id=role.id,
            metadata={"permission_id": str(permission.id)},
        )
        self.session.commit()
        self.session.refresh(mapping)
        return mapping

    def assign_role(
        self,
        *,
        user_id: UUID,
        role_id: UUID,
        organization_id: UUID,
        project_id: UUID | None,
        assigned_by: UUID,
    ) -> UserRole:
        user = self.session.get(User, user_id)
        role = self.session.get(Role, role_id)
        if user is None or role is None:
            raise NotFoundError("User or role was not found.")
        if user.organization_id != organization_id or role.organization_id != organization_id:
            raise AuthorityError("Role assignments cannot cross organization boundaries.")
        if user.principal_type == PrincipalType.SERVICE and role.grants_human_approval_authority:
            raise AuthorityError("Service principals cannot receive human approval authority.")
        assignment = UserRole(
            user_id=user.id,
            role_id=role.id,
            organization_id=organization_id,
            project_id=project_id,
            assigned_by=assigned_by,
            assigned_at=utc_now(),
        )
        self.session.add(assignment)
        self.session.flush()
        AuditService(self.session).record(
            organization_id=organization_id,
            actor_type="human",
            actor_id=assigned_by,
            action="user_role.assigned",
            entity_type="user_role",
            entity_id=assignment.id,
            metadata={"user_id": str(user.id), "role_id": str(role.id)},
        )
        self.session.commit()
        self.session.refresh(assignment)
        return assignment

    def revoke_role(self, *, assignment_id: UUID, revoked_by: UUID, reason: str) -> UserRole:
        assignment = self.session.get(UserRole, assignment_id)
        if assignment is None:
            raise NotFoundError("Role assignment was not found.")
        if assignment.revoked_at is not None:
            return assignment
        assignment.revoked_at = utc_now()
        assignment.revoked_by = revoked_by
        assignment.revocation_reason = reason
        AuditService(self.session).record(
            organization_id=assignment.organization_id,
            actor_type="human",
            actor_id=revoked_by,
            action="user_role.revoked",
            entity_type="user_role",
            entity_id=assignment.id,
            metadata={"reason": reason},
        )
        self.session.commit()
        self.session.refresh(assignment)
        return assignment

    def has_permission(
        self,
        *,
        user_id: UUID,
        organization_id: UUID,
        permission_key: str,
        project_id: UUID | None = None,
    ) -> bool:
        statement = (
            select(Permission.id)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(Role, Role.id == RolePermission.role_id)
            .join(UserRole, UserRole.role_id == Role.id)
            .join(User, User.id == UserRole.user_id)
            .where(
                UserRole.user_id == user_id,
                UserRole.organization_id == organization_id,
                UserRole.revoked_at.is_(None),
                Role.is_active.is_(True),
                User.status == "active",
                Permission.key == permission_key,
                or_(UserRole.project_id.is_(None), UserRole.project_id == project_id),
            )
            .limit(1)
        )
        return self.session.scalar(statement) is not None
