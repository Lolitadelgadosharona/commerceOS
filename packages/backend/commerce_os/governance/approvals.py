from uuid import UUID

from sqlalchemy.orm import Session

from commerce_os.governance.audit import AuditService
from commerce_os.governance.errors import AuthorityError, NotFoundError, StateTransitionError
from commerce_os.governance.models import (
    ApprovalRequest,
    ApprovalStatus,
    PrincipalType,
    User,
    UserStatus,
)
from commerce_os.governance.rbac import RbacService
from commerce_os.shared.models import utc_now


class ApprovalWorkflowService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.audit = AuditService(session)
        self.rbac = RbacService(session)

    def request(
        self,
        *,
        organization_id: UUID,
        project_id: UUID | None,
        requester_id: UUID,
        object_type: str,
        object_id: UUID,
        requested_action: str,
        reason: str,
        commit: bool = True,
    ) -> ApprovalRequest:
        requester = self.session.get(User, requester_id)
        if (
            requester is None
            or requester.organization_id != organization_id
            or requester.status != UserStatus.ACTIVE
        ):
            raise AuthorityError("Only an active in-scope principal can request approval.")
        approval = ApprovalRequest(
            organization_id=organization_id,
            project_id=project_id,
            requester_id=requester_id,
            object_type=object_type,
            object_id=object_id,
            requested_action=requested_action,
            reason=reason,
            status=ApprovalStatus.PENDING,
        )
        self.session.add(approval)
        self.session.flush()
        self.audit.record(
            organization_id=organization_id,
            actor_type=str(requester.principal_type),
            actor_id=requester.id,
            action="approval.requested",
            entity_type="approval_request",
            entity_id=approval.id,
            metadata={"requested_action": requested_action},
        )
        if commit:
            self.session.commit()
            self.session.refresh(approval)
        return approval

    def decide(
        self,
        *,
        approval_id: UUID,
        approver_id: UUID,
        decision: ApprovalStatus,
        reason: str,
    ) -> ApprovalRequest:
        approval = self.session.get(ApprovalRequest, approval_id)
        approver = self.session.get(User, approver_id)
        if approval is None or approver is None:
            raise NotFoundError("Approval request or approver was not found.")
        if approval.status != ApprovalStatus.PENDING:
            raise StateTransitionError("Only pending approvals can be decided.")
        if decision not in {ApprovalStatus.APPROVED, ApprovalStatus.REJECTED}:
            raise StateTransitionError("Decision must be approved or rejected.")
        if approver.id == approval.requester_id:
            raise AuthorityError("A requester cannot approve or reject their own request.")
        if approver.principal_type != PrincipalType.HUMAN:
            raise AuthorityError("Service principals cannot exercise human approval authority.")
        if not self.rbac.has_permission(
            user_id=approver.id,
            organization_id=approval.organization_id,
            project_id=approval.project_id,
            permission_key="approval.decide",
        ):
            raise AuthorityError("The approver lacks scoped approval authority.")
        approval.status = decision
        approval.approver_id = approver.id
        approval.decision_time = utc_now()
        approval.decision_reason = reason
        self.audit.record(
            organization_id=approval.organization_id,
            actor_type="human",
            actor_id=approver.id,
            action=f"approval.{decision.value}",
            entity_type="approval_request",
            entity_id=approval.id,
            metadata={"reason": reason},
        )
        self.session.commit()
        self.session.refresh(approval)
        return approval

    def cancel(self, *, approval_id: UUID, requester_id: UUID, reason: str) -> ApprovalRequest:
        approval = self.session.get(ApprovalRequest, approval_id)
        if approval is None:
            raise NotFoundError("Approval request was not found.")
        if approval.status != ApprovalStatus.PENDING:
            raise StateTransitionError("Only pending approvals can be cancelled.")
        if approval.requester_id != requester_id:
            raise AuthorityError("Only the requester can cancel a pending approval.")
        approval.status = ApprovalStatus.CANCELLED
        approval.decision_time = utc_now()
        approval.decision_reason = reason
        self.audit.record(
            organization_id=approval.organization_id,
            actor_type="human",
            actor_id=requester_id,
            action="approval.cancelled",
            entity_type="approval_request",
            entity_id=approval.id,
            metadata={"reason": reason},
        )
        self.session.commit()
        self.session.refresh(approval)
        return approval
