from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any, cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from commerce_os.ai_runtime.adapters import (
    DeterministicProviderAdapter,
    OpenAICompatibleAdapter,
    ProviderAdapter,
    ProviderExecutionError,
    ProviderRequestContext,
)
from commerce_os.ai_runtime.errors import AIRuntimeScopeError, AIRuntimeValidationError
from commerce_os.ai_runtime.models import (
    AICostObservation,
    AIModelCapability,
    AIOutputClassification,
    AIProvider,
    AIRequest,
    AIRequestStatus,
    PromptVersion,
)
from commerce_os.ai_runtime.schemas import AIExecutionResult, AIExecutionSubmit
from commerce_os.governance.audit import AuditService
from commerce_os.governance.models import PrincipalType, User
from commerce_os.shared.models import utc_now

FORBIDDEN_AUTHORITY_TERMS = {
    "approve investment",
    "approve business decision",
    "publish content",
    "launch advertising",
    "change advertising budget",
    "contact customer",
    "issue refund",
    "modify product truth",
    "change price",
    "purchase inventory",
    "select supplier",
    "pay supplier",
    "transfer money",
    "modify finance truth",
}
TERMINAL = {"succeeded", "failed", "timed_out", "rate_limited", "cancelled"}


class AIExecutionService:
    def __init__(
        self, session: Session, adapters: dict[str, ProviderAdapter] | None = None
    ) -> None:
        self.session = session
        self.adapters = adapters or {}

    def submit(self, payload: AIExecutionSubmit, actor_id: UUID) -> AIRequest:
        capability = self._scoped(AIModelCapability, payload.capability_id, payload.organization_id)
        provider = self._scoped(AIProvider, capability.provider_id, payload.organization_id)
        if not capability.available or provider.availability_state != "available":
            raise AIRuntimeValidationError("Selected provider capability is unavailable.")
        if payload.prompt_version_id is not None:
            prompt = self._scoped(PromptVersion, payload.prompt_version_id, payload.organization_id)
            if prompt.status != "approved":
                raise AIRuntimeValidationError("Execution requires an approved prompt version.")
        entity = AIRequest(
            organization_id=payload.organization_id,
            requester_id=actor_id,
            purpose=payload.purpose,
            context_type=payload.context_type,
            context_reference=payload.context_reference,
            capability_id=payload.capability_id,
            approval_request_id=payload.approval_request_id,
            status=AIRequestStatus.QUEUED,
            output_classification=AIOutputClassification(payload.output_classification),
            output_metadata={"authority": "advisory_only"},
            failure_reason=None,
            prompt_version_id=payload.prompt_version_id,
            task_type=payload.task_type,
            system_instructions=payload.system_instructions,
            input_content=payload.input_content,
            expected_output_schema=payload.expected_output_schema,
            runtime_configuration=payload.runtime_configuration,
            provenance_context=payload.provenance_context,
            selected_provider_identity=provider.provider_identity,
            selected_model_identity=capability.model_identity,
            retry_count=0,
            submitted_at=utc_now(),
        )
        self.session.add(entity)
        self.session.flush()
        try:
            self._authority_gate(payload)
        except AIRuntimeValidationError:
            entity.status = AIRequestStatus.FAILED
            entity.failure_category = "safety_rejection"
            entity.failure_reason = "AI authority boundary rejected the requested action."
            entity.completed_at = utc_now()
            self._audit(entity, actor_id, "ai.execution.authority_rejected")
            self.session.commit()
            raise
        self._audit(entity, actor_id, "ai.execution.submitted")
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def execute(self, entity: AIRequest, worker_actor_id: UUID | None = None) -> AIRequest:
        if str(entity.status) != "queued":
            raise AIRuntimeValidationError("Only queued AI requests may execute.")
        capability = self._scoped(AIModelCapability, entity.capability_id, entity.organization_id)
        provider = self._scoped(AIProvider, capability.provider_id, entity.organization_id)
        actor_id = worker_actor_id or entity.requester_id
        if worker_actor_id is not None:
            worker = self._scoped(User, worker_actor_id, entity.organization_id)
            if worker.principal_type != PrincipalType.SERVICE:
                raise AIRuntimeValidationError(
                    "Worker execution requires an explicit service identity."
                )
        rejection = self._limit_rejection(entity, capability, provider)
        if rejection is not None:
            category, reason = rejection
            entity.status = (
                AIRequestStatus.RATE_LIMITED if category == "rate_limit" else AIRequestStatus.FAILED
            )
            entity.failure_category = category
            entity.failure_reason = reason
            entity.completed_at = utc_now()
            self._audit(entity, actor_id, f"ai.execution.{category}_rejected", "service")
            return self._commit(entity)
        entity.status = AIRequestStatus.RUNNING
        entity.started_at = utc_now()
        self._audit(entity, actor_id, "ai.execution.started", "service")
        self._audit(entity, actor_id, "ai.execution.provider_selected", "service")
        self.session.commit()
        attempts = int(provider.runtime_configuration.get("max_retries", 1)) + 1
        started = time.monotonic()
        for attempt in range(attempts):
            try:
                adapter = self._adapter(provider)
                response = adapter.execute(self._context(entity))
                self._validate_schema(response.content, entity.expected_output_schema)
                entity.status = AIRequestStatus.SUCCEEDED
                entity.response_content = response.content
                entity.structured_output_valid = True
                entity.provider_request_id = response.provider_request_id
                entity.input_tokens = response.input_tokens
                entity.output_tokens = response.output_tokens
                entity.total_tokens = response.total_tokens
                entity.latency_ms = round((time.monotonic() - started) * 1000)
                entity.completed_at = utc_now()
                self._record_cost(entity, capability, provider, response.provider_reported_cost)
                self._audit(entity, actor_id, "ai.execution.succeeded", "service")
                return self._commit(entity)
            except ProviderExecutionError as exc:
                entity.retry_count = attempt
                if exc.retryable and attempt + 1 < attempts:
                    continue
                entity.status = (
                    AIRequestStatus.TIMED_OUT
                    if exc.category == "timeout"
                    else AIRequestStatus.RATE_LIMITED
                    if exc.category == "rate_limit"
                    else AIRequestStatus.FAILED
                )
                entity.failure_category = exc.category
                entity.failure_reason = str(exc)
                entity.structured_output_valid = (
                    False if exc.category == "invalid_response" else None
                )
                entity.latency_ms = round((time.monotonic() - started) * 1000)
                entity.completed_at = utc_now()
                self._audit(entity, actor_id, "ai.execution.failed", "service")
                return self._commit(entity)
        raise AssertionError("bounded provider execution exhausted unexpectedly")

    def cancel(self, entity: AIRequest, actor_id: UUID) -> AIRequest:
        if str(entity.status) not in {"draft", "queued"}:
            raise AIRuntimeValidationError("Only draft or queued requests may be cancelled.")
        entity.status = AIRequestStatus.CANCELLED
        entity.completed_at = utc_now()
        self._audit(entity, actor_id, "ai.execution.cancelled")
        return self._commit(entity)

    def result(self, entity: AIRequest) -> AIExecutionResult:
        return AIExecutionResult(
            id=entity.id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            version=entity.version,
            organization_id=entity.organization_id,
            request_id=entity.id,
            status=str(entity.status),
            output_classification=str(entity.output_classification)
            if entity.output_classification
            else None,
            response_content=entity.response_content,
            structured_output_valid=entity.structured_output_valid,
            provider_request_id=entity.provider_request_id,
            provider=entity.selected_provider_identity,
            model=entity.selected_model_identity,
            input_tokens=entity.input_tokens,
            output_tokens=entity.output_tokens,
            total_tokens=entity.total_tokens,
            latency_ms=entity.latency_ms,
            retry_count=entity.retry_count,
            failure_category=entity.failure_category,
            failure_reason=entity.failure_reason,
        )

    def scoped_request(self, request_id: UUID, organization_id: UUID) -> AIRequest:
        return cast(AIRequest, self._scoped(AIRequest, request_id, organization_id))

    def _adapter(self, provider: AIProvider) -> ProviderAdapter:
        if provider.provider_identity in self.adapters:
            return self.adapters[provider.provider_identity]
        if provider.provider_identity == "deterministic_test":
            return DeterministicProviderAdapter(provider.runtime_configuration.get("test_response"))
        if provider.base_url is None:
            raise ProviderExecutionError("invalid_request", "Provider base URL is not configured.")
        return OpenAICompatibleAdapter(
            base_url=provider.base_url,
            credential_reference=provider.credential_reference,
            timeout_seconds=provider.timeout_seconds,
        )

    def _context(self, entity: AIRequest) -> ProviderRequestContext:
        config = entity.runtime_configuration
        return ProviderRequestContext(
            model=entity.selected_model_identity or "",
            system_instructions=entity.system_instructions or "",
            input_content=entity.input_content or "",
            output_schema=entity.expected_output_schema,
            temperature=config.get("temperature"),
            max_output_tokens=int(config.get("max_output_tokens", 1000)),
        )

    def _limit_rejection(
        self, entity: AIRequest, capability: AIModelCapability, provider: AIProvider
    ) -> tuple[str, str] | None:
        now = datetime.now(UTC)
        minute_count = (
            self.session.scalar(
                select(func.count())
                .select_from(AIRequest)
                .where(
                    AIRequest.organization_id == entity.organization_id,
                    AIRequest.capability_id == capability.id,
                    AIRequest.started_at >= now - timedelta(minutes=1),
                )
            )
            or 0
        )
        minute_limit = int(provider.runtime_configuration.get("requests_per_minute", 60))
        if minute_count >= minute_limit:
            return "rate_limit", "Local organization/provider/model rate limit exceeded."
        estimate = self._estimate_cost(entity, capability)
        max_request = Decimal(
            str(provider.runtime_configuration.get("max_estimated_request_cost", "10"))
        )
        if estimate > max_request:
            return "cost_limit", "Estimated request cost exceeds the configured request limit."
        daily = self.session.scalar(
            select(func.coalesce(func.sum(AICostObservation.estimated_cost), 0)).where(
                AICostObservation.organization_id == entity.organization_id,
                AICostObservation.created_at >= now - timedelta(days=1),
            )
        )
        daily_limit = Decimal(
            str(provider.runtime_configuration.get("organization_daily_budget", "100"))
        )
        if Decimal(str(daily)) + estimate > daily_limit:
            return "cost_limit", "Organization daily AI cost limit would be exceeded."
        return None

    def _estimate_cost(self, entity: AIRequest, capability: AIModelCapability) -> Decimal:
        input_estimate = Decimal(len(entity.input_content or "") / 4)
        output_estimate = Decimal(int(entity.runtime_configuration.get("max_output_tokens", 1000)))
        input_rate = Decimal(str(capability.cost_metadata.get("input_per_million", 0)))
        output_rate = Decimal(str(capability.cost_metadata.get("output_per_million", 0)))
        return (input_estimate * input_rate + output_estimate * output_rate) / Decimal(1_000_000)

    def _record_cost(
        self,
        entity: AIRequest,
        capability: AIModelCapability,
        provider: AIProvider,
        reported: str | None,
    ) -> None:
        estimate = self._estimate_cost(entity, capability)
        self.session.add(
            AICostObservation(
                organization_id=entity.organization_id,
                provider_id=provider.id,
                capability_id=capability.id,
                usage_quantity=Decimal(entity.total_tokens)
                if entity.total_tokens is not None
                else Decimal(0),
                usage_unit="tokens",
                estimated_cost=estimate,
                provider_reported_cost=Decimal(reported) if reported is not None else None,
                cost_basis="provider_reported" if reported is not None else "estimated",
                currency=str(capability.cost_metadata.get("currency", "USD")),
                project_id=None,
                related_request_id=entity.id,
                input_tokens=entity.input_tokens,
                output_tokens=entity.output_tokens,
                total_tokens=entity.total_tokens,
            )
        )

    @staticmethod
    def _authority_gate(payload: AIExecutionSubmit) -> None:
        combined = (
            f"{payload.purpose} {payload.system_instructions} {payload.input_content}".lower()
        )
        violation = next((term for term in FORBIDDEN_AUTHORITY_TERMS if term in combined), None)
        if violation:
            raise AIRuntimeValidationError(
                f"AI authority boundary rejected requested action: {violation}."
            )

    @classmethod
    def _validate_schema(cls, value: Any, schema: dict[str, Any] | None) -> None:
        if schema is None:
            return
        if schema.get("type") == "object":
            if not isinstance(value, dict):
                raise ProviderExecutionError(
                    "invalid_response", "Structured output must be an object."
                )
            missing = set(schema.get("required", [])) - set(value)
            if missing:
                raise ProviderExecutionError(
                    "invalid_response", "Structured output omitted required fields."
                )
            for key, rule in schema.get("properties", {}).items():
                if key in value and not cls._type_matches(value[key], rule.get("type")):
                    raise ProviderExecutionError(
                        "invalid_response", "Structured output field type is invalid."
                    )

    @staticmethod
    def _type_matches(value: Any, expected: str | None) -> bool:
        types: dict[str, type[Any] | tuple[type[Any], ...]] = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict,
        }
        return expected is None or isinstance(value, types.get(expected, object))

    def _scoped(self, model: type[Any], entity_id: UUID | None, organization_id: UUID) -> Any:
        entity = self.session.get(model, entity_id) if entity_id is not None else None
        if entity is None or entity.organization_id != organization_id:
            raise AIRuntimeScopeError("AI runtime record was not found in this organization.")
        return entity

    def _audit(
        self, entity: AIRequest, actor_id: UUID, action: str, actor_type: str = "human"
    ) -> None:
        AuditService(self.session).record(
            organization_id=entity.organization_id,
            actor_type=actor_type,
            actor_id=actor_id,
            action=action,
            entity_type="ai_requests",
            entity_id=entity.id,
            metadata={"result": "success", "authority": "advisory_only"},
        )

    def _commit(self, entity: AIRequest) -> AIRequest:
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity
