from decimal import Decimal

import pytest
from commerce_os.ai_runtime.errors import AIRuntimeScopeError, AIRuntimeValidationError
from commerce_os.ai_runtime.models import AICostObservation, AIProvider, AIRequest
from commerce_os.ai_runtime.schemas import (
    AIRequestCreate,
    AIRequestTransition,
    CapabilityCreate,
    CostObservationCreate,
    PromptEvaluationCreate,
    PromptPurposeCreate,
    PromptTemplateCreate,
    PromptVersionCreate,
    ProviderCreate,
)
from commerce_os.ai_runtime.services import AIRuntimeService
from commerce_os.governance.authentication import AuthenticationService
from commerce_os.governance.models import (
    AuditLog,
    Organization,
    Permission,
    Role,
    RolePermission,
    UserRole,
)
from commerce_os.shared.models import utc_now
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.main import app


def identity(session: Session, slug: str):  # type: ignore[no-untyped-def]
    organization = Organization(name=f"AI {slug}", slug=f"ai-{slug}")
    session.add(organization)
    session.commit()
    user = AuthenticationService(session).create_user(
        organization_id=organization.id,
        email=f"{slug}@example.com",
        display_name="AI Operator",
        password="correct horse battery staple",
    )
    return organization, user


def provider_and_capability(service: AIRuntimeService, organization_id, actor_id):  # type: ignore[no-untyped-def]
    provider = service.create_provider(
        ProviderCreate(
            organization_id=organization_id,
            provider_identity="provider-neutral-test",
            display_name="Neutral Provider",
            availability_state="available",
            provider_version="registry-v1",
            cost_metadata={"basis": "advisory"},
        ),
        actor_id,
    )
    capability = service.create_capability(
        CapabilityCreate(
            organization_id=organization_id,
            provider_id=provider.id,
            model_identity="model-metadata-only",
            capability_type="classification",
            model_version="v1",
            available=True,
            cost_metadata={"unit": "item"},
        ),
        actor_id,
    )
    return provider, capability


def test_provider_request_output_cost_and_audit_boundaries(db_session: Session) -> None:
    organization, user = identity(db_session, "runtime")
    service = AIRuntimeService(db_session)
    provider, capability = provider_and_capability(service, organization.id, user.id)
    request = service.create_request(
        AIRequestCreate(
            organization_id=organization.id,
            purpose="Classify supplied evidence",
            context_type="customer_signal",
            context_reference="signal:test",
            capability_id=capability.id,
        ),
        user.id,
    )
    request = service.transition_request(
        request.id,
        AIRequestTransition(organization_id=organization.id, status="submitted"),
        user.id,
    )
    request = service.transition_request(
        request.id,
        AIRequestTransition(organization_id=organization.id, status="ready"),
        user.id,
    )
    with pytest.raises(AIRuntimeValidationError):
        service.transition_request(
            request.id,
            AIRequestTransition(organization_id=organization.id, status="completed"),
            user.id,
        )
    request = service.transition_request(
        request.id,
        AIRequestTransition(
            organization_id=organization.id,
            status="completed",
            output_classification="classification",
            output_metadata={"artifact_reference": "candidate:1", "authority": "none"},
        ),
        user.id,
    )
    assert str(request.status) == "completed"
    observation = service.observe_cost(
        CostObservationCreate(
            organization_id=organization.id,
            provider_id=provider.id,
            capability_id=capability.id,
            usage_quantity=Decimal("12.123456"),
            usage_unit="items",
            estimated_cost=Decimal("0.012345"),
            currency="USD",
            related_request_id=request.id,
        ),
        user.id,
    )
    assert observation.estimated_cost == Decimal("0.012345")
    actions = set(db_session.scalars(select(AuditLog.action)))
    assert {"ai.provider.created", "ai.request.completed", "ai.cost_observation.created"} <= actions


def test_tenant_provider_isolation_and_prompt_versioning(db_session: Session) -> None:
    organization, user = identity(db_session, "one")
    other, other_user = identity(db_session, "two")
    service = AIRuntimeService(db_session)
    provider, _ = provider_and_capability(service, organization.id, user.id)
    with pytest.raises(AIRuntimeScopeError):
        service.create_capability(
            CapabilityCreate(
                organization_id=other.id,
                provider_id=provider.id,
                model_identity="cross-tenant",
                capability_type="vision",
                model_version="v1",
                available=True,
            ),
            other_user.id,
        )
    purpose = service.create_purpose(
        PromptPurposeCreate(
            organization_id=organization.id,
            name="Evidence classification",
            description="Classify supplied evidence without business execution.",
            owning_domain="intelligence",
        ),
        user.id,
    )
    template = service.create_template(
        PromptTemplateCreate(
            organization_id=organization.id, purpose_id=purpose.id, name="Evidence v1"
        ),
        user.id,
    )
    first = service.create_version(
        PromptVersionCreate(
            organization_id=organization.id,
            template_id=template.id,
            prompt_content="Classify the supplied evidence.",
        ),
        user.id,
    )
    second = service.create_version(
        PromptVersionCreate(
            organization_id=organization.id,
            template_id=template.id,
            prompt_content="Classify evidence and include provenance.",
        ),
        user.id,
    )
    evaluation = service.evaluate_prompt(
        PromptEvaluationCreate(
            organization_id=organization.id,
            prompt_version_id=second.id,
            score=91,
            result="pass",
            notes="Human supplied evaluation.",
        ),
        user.id,
    )
    assert (first.version_number, second.version_number, evaluation.score) == (1, 2, 91)


def test_ai_api_requires_permission(client: TestClient, db_session: Session) -> None:
    organization, user = identity(db_session, "permission")
    role = Role(
        organization_id=organization.id,
        name="reader",
        description="Read only",
        grants_human_approval_authority=False,
        is_active=True,
    )
    permission = Permission(
        key="api.read",
        resource="api",
        action="read",
        description="Read API",
        is_human_approval_permission=False,
    )
    db_session.add_all([role, permission])
    db_session.flush()
    db_session.add_all(
        [
            UserRole(
                user_id=user.id,
                role_id=role.id,
                organization_id=organization.id,
                project_id=None,
                assigned_by=user.id,
                assigned_at=utc_now(),
            ),
            RolePermission(role_id=role.id, permission_id=permission.id),
        ]
    )
    db_session.commit()
    login = client.post(
        "/api/v1/auth/login",
        json={
            "organization_id": str(organization.id),
            "email": "permission@example.com",
            "password": "correct horse battery staple",
        },
    )
    token = login.json()["access_token"]
    app.state.auth_test_bypass = False
    try:
        headers = {"Authorization": f"Bearer {token}"}
        assert (
            client.get(
                "/api/v1/ai/providers",
                params={"organization_id": organization.id},
                headers=headers,
            ).status_code
            == 200
        )
        denied = client.post(
            "/api/v1/ai/providers",
            headers=headers,
            json={
                "organization_id": str(organization.id),
                "provider_identity": "denied",
                "display_name": "Denied",
                "availability_state": "disabled",
                "provider_version": "v1",
                "cost_metadata": {},
            },
        )
        assert denied.status_code == 403
    finally:
        app.state.auth_test_bypass = True


def test_ai_provider_api_creates_metadata_only_record(
    client: TestClient, db_session: Session
) -> None:
    organization, user = identity(db_session, "api")
    response = client.post(
        "/api/v1/ai/providers",
        headers={"X-Actor-ID": str(user.id)},
        json={
            "organization_id": str(organization.id),
            "provider_identity": "metadata-provider",
            "display_name": "Metadata Provider",
            "availability_state": "disabled",
            "provider_version": "registry-v1",
            "cost_metadata": {"execution": False},
        },
    )
    assert response.status_code == 201
    assert response.json()["provider_identity"] == "metadata-provider"
    assert db_session.scalar(
        select(AIProvider).where(AIProvider.organization_id == organization.id)
    )


def test_runtime_has_no_external_execution_contract(db_session: Session) -> None:
    assert not hasattr(AIRuntimeService(db_session), "execute")
    assert set(AIRequest.__table__.columns.keys()).isdisjoint({"approval", "payment", "refund"})
    assert db_session.scalar(select(AIProvider)) is None
    assert db_session.scalar(select(AICostObservation)) is None
