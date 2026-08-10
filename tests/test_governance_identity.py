from uuid import uuid4

import pytest
from commerce_os.governance.approvals import ApprovalWorkflowService
from commerce_os.governance.authentication import AuthenticationService
from commerce_os.governance.errors import AuthorityError
from commerce_os.governance.identity import CustomerIdentityService
from commerce_os.governance.models import (
    ApprovalStatus,
    AuditLog,
    Organization,
    PasswordCredential,
    Permission,
    PrincipalType,
    Role,
)
from commerce_os.governance.rbac import RbacService
from commerce_os.governance.schemas import CustomerIdentityCreate
from commerce_os.operations.models import Customer
from sqlalchemy import select
from sqlalchemy.orm import Session

PASSWORD = "correct horse battery staple"


def organization(session: Session) -> Organization:
    value = Organization(name="Test Organization", slug="test-organization")
    session.add(value)
    session.commit()
    return value


def create_user(session: Session, org: Organization, email: str, **kwargs):  # type: ignore[no-untyped-def]
    return AuthenticationService(session).create_user(
        organization_id=org.id,
        email=email,
        display_name=email.split("@")[0].title(),
        password=PASSWORD,
        **kwargs,
    )


def test_password_authentication_uses_argon2_and_is_audited(db_session: Session) -> None:
    org = organization(db_session)
    service = AuthenticationService(db_session)
    user = create_user(db_session, org, "OWNER@EXAMPLE.COM")
    credential = db_session.scalar(
        select(PasswordCredential).where(PasswordCredential.user_id == user.id)
    )
    assert credential is not None
    assert credential.password_hash != PASSWORD
    assert credential.password_hash.startswith("$argon2")
    assert (
        service.authenticate_password(
            organization_id=org.id, email="owner@example.com", password=PASSWORD
        )
        == user
    )
    assert (
        service.authenticate_password(
            organization_id=org.id, email="owner@example.com", password="wrong password"
        )
        is None
    )
    actions = set(db_session.scalars(select(AuditLog.action)))
    assert {"user.created", "authentication.succeeded", "authentication.failed"} <= actions


def test_scoped_rbac_is_revocable_and_service_accounts_cannot_approve(
    db_session: Session,
) -> None:
    org = organization(db_session)
    owner = create_user(db_session, org, "owner@example.com")
    operator = create_user(db_session, org, "operator@example.com")
    service_user = create_user(
        db_session, org, "service@example.com", principal_type=PrincipalType.SERVICE
    )
    role = Role(organization_id=org.id, name="approver", grants_human_approval_authority=True)
    permission = Permission(
        key="approval.decide",
        resource="approval",
        action="decide",
        is_human_approval_permission=True,
    )
    db_session.add_all([role, permission])
    db_session.commit()
    rbac = RbacService(db_session)
    rbac.grant_permission(role_id=role.id, permission_id=permission.id, actor_id=owner.id)
    assignment = rbac.assign_role(
        user_id=operator.id,
        role_id=role.id,
        organization_id=org.id,
        project_id=None,
        assigned_by=owner.id,
    )
    assert rbac.has_permission(
        user_id=operator.id, organization_id=org.id, permission_key="approval.decide"
    )
    rbac.revoke_role(assignment_id=assignment.id, revoked_by=owner.id, reason="Rotation")
    assert not rbac.has_permission(
        user_id=operator.id, organization_id=org.id, permission_key="approval.decide"
    )
    with pytest.raises(AuthorityError):
        rbac.assign_role(
            user_id=service_user.id,
            role_id=role.id,
            organization_id=org.id,
            project_id=None,
            assigned_by=owner.id,
        )


def test_approval_decision_requires_authority_and_creates_audit(db_session: Session) -> None:
    org = organization(db_session)
    requester = create_user(db_session, org, "requester@example.com")
    approver = create_user(db_session, org, "approver@example.com")
    role = Role(organization_id=org.id, name="approver", grants_human_approval_authority=True)
    permission = Permission(
        key="approval.decide",
        resource="approval",
        action="decide",
        is_human_approval_permission=True,
    )
    db_session.add_all([role, permission])
    db_session.commit()
    rbac = RbacService(db_session)
    rbac.grant_permission(role_id=role.id, permission_id=permission.id, actor_id=requester.id)
    rbac.assign_role(
        user_id=approver.id,
        role_id=role.id,
        organization_id=org.id,
        project_id=None,
        assigned_by=requester.id,
    )
    workflow = ApprovalWorkflowService(db_session)
    approval = workflow.request(
        organization_id=org.id,
        project_id=None,
        requester_id=requester.id,
        object_type="pricing_exception",
        object_id=uuid4(),
        requested_action="pricing.override",
        reason="Contractual exception",
    )
    with pytest.raises(AuthorityError):
        workflow.decide(
            approval_id=approval.id,
            approver_id=requester.id,
            decision=ApprovalStatus.APPROVED,
            reason="Self approval",
        )
    decided = workflow.decide(
        approval_id=approval.id,
        approver_id=approver.id,
        decision=ApprovalStatus.APPROVED,
        reason="Within policy",
    )
    assert decided.status == ApprovalStatus.APPROVED
    assert (
        db_session.scalar(
            select(AuditLog).where(
                AuditLog.entity_id == approval.id, AuditLog.action == "approval.approved"
            )
        )
        is not None
    )


def test_external_customer_identity_mapping_preserves_evidence(db_session: Session) -> None:
    org = organization(db_session)
    customer = Customer(organization_id=org.id, display_name="Customer")
    db_session.add(customer)
    db_session.commit()
    identity = CustomerIdentityService(db_session).observe(
        CustomerIdentityCreate(
            organization_id=org.id,
            customer_id=customer.id,
            provider="instagram",
            external_identifier="ig_1234",
            confidence_score=0.85,
            verification_status="unverified",
            provenance={"source": "manual_observation"},
        )
    )
    assert identity.provider == "instagram"
    assert identity.external_identifier == "ig_1234"
    assert identity.confidence_score == 0.85
    assert identity.provenance == {"source": "manual_observation"}
