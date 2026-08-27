import os

import pytest
from commerce_os.ai_runtime.adapters import (
    EnvironmentCredentialResolver,
    OpenAICompatibleAdapter,
    ProviderExecutionError,
    ProviderResponse,
)
from commerce_os.ai_runtime.errors import AIRuntimeScopeError, AIRuntimeValidationError
from commerce_os.ai_runtime.execution import AIExecutionService
from commerce_os.ai_runtime.models import AICostObservation
from commerce_os.ai_runtime.schemas import (
    AIExecutionSubmit,
    CapabilityCreate,
    ProviderCreate,
)
from commerce_os.ai_runtime.services import AIRuntimeService
from commerce_os.governance.authentication import AuthenticationService
from commerce_os.governance.models import ApprovalRequest, Organization, PrincipalType
from commerce_os.intelligence.research_schemas import ResearchAnalysisCreate
from commerce_os.intelligence.research_services import ResearchAnalystService
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session


class FailingAdapter:
    def execute(self, _context):  # type: ignore[no-untyped-def]
        raise ProviderExecutionError("provider_unavailable", "Provider unavailable.", True)


class InvalidAdapter:
    def execute(self, _context):  # type: ignore[no-untyped-def]
        return ProviderResponse(content={"wrong": True})


def test_openai_compatible_adapter_reads_standard_responses_output() -> None:
    body = {
        "output": [
            {
                "type": "message",
                "content": [
                    {
                        "type": "output_text",
                        "text": '{"summary":"Evidence reviewed","confidence":0.9}',
                    }
                ],
            }
        ]
    }
    assert OpenAICompatibleAdapter._output_text(body) == (
        '{"summary":"Evidence reviewed","confidence":0.9}'
    )


def test_runtime_context_allows_explicit_governed_web_search(db_session: Session) -> None:
    organization, user, _, capability = setup_runtime(db_session, "web-search")
    service = AIExecutionService(db_session)
    request = service.submit(
        payload(
            organization,
            capability,
            runtime_configuration={"max_output_tokens": 500, "web_search": True},
        ),
        user.id,
    )
    context = service._context(request)
    assert context.web_search is True


def setup_runtime(session: Session, slug: str, config=None):  # type: ignore[no-untyped-def]
    organization = Organization(name=f"Execution {slug}", slug=f"execution-{slug}")
    session.add(organization)
    session.commit()
    user = AuthenticationService(session).create_user(
        organization_id=organization.id,
        email=f"{slug}@example.com",
        display_name="AI Operator",
        password="correct horse battery staple",
    )
    registry = AIRuntimeService(session)
    provider = registry.create_provider(
        ProviderCreate(
            organization_id=organization.id,
            provider_identity=f"provider_{slug}",
            display_name="Governed Provider",
            availability_state="available",
            provider_version="v1",
            cost_metadata={},
            base_url="https://provider.invalid",
            credential_reference="TEST_PROVIDER_SECRET",
            runtime_configuration=config or {"max_retries": 1},
        ),
        user.id,
    )
    capability = registry.create_capability(
        CapabilityCreate(
            organization_id=organization.id,
            provider_id=provider.id,
            model_identity="analysis-model-v1",
            capability_type="text_generation",
            model_version="v1",
            available=True,
            cost_metadata={
                "input_per_million": "1.00",
                "output_per_million": "2.00",
                "currency": "USD",
            },
        ),
        user.id,
    )
    return organization, user, provider, capability


def payload(organization, capability, **changes):  # type: ignore[no-untyped-def]
    values = {
        "organization_id": organization.id,
        "purpose": "Analyze cited customer evidence",
        "context_type": "research_evidence",
        "context_reference": "evidence:set:1",
        "capability_id": capability.id,
        "task_type": "research_analysis",
        "system_instructions": "Return analysis only; do not execute business actions.",
        "input_content": "Summarize the supplied evidence.",
        "output_classification": "analysis",
        "expected_output_schema": {
            "type": "object",
            "required": ["summary", "confidence"],
            "properties": {"summary": {"type": "string"}, "confidence": {"type": "number"}},
        },
        "runtime_configuration": {"max_output_tokens": 200},
        "provenance_context": {"source_domain": "intelligence"},
    }
    values.update(changes)
    return AIExecutionSubmit(**values)


def test_deterministic_execution_usage_cost_and_no_authority_side_effects(
    db_session: Session,
) -> None:
    organization, user, provider, capability = setup_runtime(db_session, "success")
    from commerce_os.ai_runtime.adapters import DeterministicProviderAdapter

    service = AIExecutionService(
        db_session,
        {provider.provider_identity: DeterministicProviderAdapter()},
    )
    request = service.submit(payload(organization, capability), user.id)
    approvals = db_session.scalar(select(func.count()).select_from(ApprovalRequest))
    request = service.execute(request)
    assert str(request.status) == "succeeded"
    assert request.output_classification == "analysis"
    assert request.total_tokens == 18 and request.structured_output_valid is True
    assert db_session.scalar(select(func.count()).select_from(ApprovalRequest)) == approvals == 0
    observation = db_session.scalar(select(AICostObservation))
    assert observation is not None and observation.cost_basis == "estimated"
    analysis = ResearchAnalystService(db_session).create_analysis(
        ResearchAnalysisCreate(
            organization_id=organization.id,
            ai_request_id=request.id,
            analysis_type="market_insight",
            output_classification="analysis",
            output_summary=request.response_content["summary"],
            confidence=request.response_content["confidence"],
            methodology_version="governed-ai-runtime-v1",
        ),
        user.id,
    )
    assert analysis.status == "draft" and analysis.output_classification == "analysis"


def test_authority_rate_cost_schema_and_failure_boundaries(db_session: Session) -> None:
    organization, user, provider, capability = setup_runtime(
        db_session,
        "limits",
        {"requests_per_minute": 0, "max_estimated_request_cost": "0.000001"},
    )
    service = AIExecutionService(db_session, {provider.provider_identity: InvalidAdapter()})
    with pytest.raises(AIRuntimeValidationError):
        service.submit(
            payload(organization, capability, input_content="Issue refund to this customer."),
            user.id,
        )
    rate_limited = service.execute(service.submit(payload(organization, capability), user.id))
    assert (
        str(rate_limited.status) == "rate_limited" and rate_limited.failure_category == "rate_limit"
    )
    provider.runtime_configuration = {"requests_per_minute": 10, "max_estimated_request_cost": "10"}
    db_session.commit()
    invalid = service.execute(service.submit(payload(organization, capability), user.id))
    assert str(invalid.status) == "failed" and invalid.failure_category == "invalid_response"


def test_tenant_scope_secret_resolution_and_redaction(db_session: Session) -> None:
    organization, user, provider, capability = setup_runtime(db_session, "tenant")
    other, other_user, _, _ = setup_runtime(db_session, "other")
    service = AIExecutionService(db_session, {provider.provider_identity: FailingAdapter()})
    request = service.submit(payload(organization, capability), user.id)
    with pytest.raises(AIRuntimeScopeError):
        service.scoped_request(request.id, other.id)
    os.environ.pop("TEST_PROVIDER_SECRET", None)
    with pytest.raises(ProviderExecutionError) as error:
        EnvironmentCredentialResolver().resolve("TEST_PROVIDER_SECRET")
    assert "TEST_PROVIDER_SECRET" not in str(error.value)
    assert provider.credential_reference == "TEST_PROVIDER_SECRET"
    assert "secret" not in provider.runtime_configuration
    with pytest.raises(AIRuntimeScopeError):
        service.execute(request, other_user.id)
    with pytest.raises(AIRuntimeValidationError):
        service.execute(request, user.id)
    worker = AuthenticationService(db_session).create_user(
        organization_id=organization.id,
        email="worker@example.com",
        display_name="Runtime Worker",
        password="service credential only",
        principal_type=PrincipalType.SERVICE,
    )
    failed = service.execute(request, worker.id)
    assert failed.retry_count == 1 and failed.failure_reason == "Provider unavailable."


def test_execution_api_requires_authentication(db_session: Session) -> None:
    organization, _, _, capability = setup_runtime(db_session, "auth")
    from commerce_os.shared.database import get_session

    from apps.api.main import app

    def override():  # type: ignore[no-untyped-def]
        yield db_session

    app.dependency_overrides[get_session] = override
    app.state.auth_test_bypass = False
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/ai/executions", json=payload(organization, capability).model_dump(mode="json")
        )
    app.dependency_overrides.clear()
    assert response.status_code == 401
