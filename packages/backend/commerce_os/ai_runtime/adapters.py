from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class ProviderRequestContext:
    model: str
    system_instructions: str
    input_content: str
    output_schema: dict[str, Any] | None
    temperature: float | None
    max_output_tokens: int


@dataclass(frozen=True)
class ProviderResponse:
    content: dict[str, Any]
    provider_request_id: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    provider_reported_cost: str | None = None


class ProviderExecutionError(RuntimeError):
    def __init__(self, category: str, message: str, retryable: bool = False) -> None:
        super().__init__(message)
        self.category = category
        self.retryable = retryable


class ProviderAdapter(Protocol):
    def execute(self, context: ProviderRequestContext) -> ProviderResponse: ...


class EnvironmentCredentialResolver:
    def resolve(self, reference: str | None) -> str:
        if reference is None or not reference.isidentifier() or reference.upper() != reference:
            raise ProviderExecutionError("authentication_error", "Credential reference is invalid.")
        value = os.environ.get(reference)
        if not value:
            raise ProviderExecutionError(
                "authentication_error", "External provider credential is not configured."
            )
        return value


class DeterministicProviderAdapter:
    def __init__(self, response: dict[str, Any] | None = None) -> None:
        self.response = response or {
            "summary": "Deterministic governed analysis.",
            "confidence": 0.8,
        }

    def execute(self, context: ProviderRequestContext) -> ProviderResponse:
        return ProviderResponse(
            content=self.response,
            provider_request_id="deterministic-test-response",
            input_tokens=10,
            output_tokens=8,
            total_tokens=18,
        )


class OpenAICompatibleAdapter:
    """Provider transport only; contains no Commerce OS business rules."""

    def __init__(
        self,
        *,
        base_url: str,
        credential_reference: str | None,
        timeout_seconds: int,
        resolver: EnvironmentCredentialResolver | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.credential_reference = credential_reference
        self.timeout_seconds = timeout_seconds
        self.resolver = resolver or EnvironmentCredentialResolver()

    def execute(self, context: ProviderRequestContext) -> ProviderResponse:
        secret = self.resolver.resolve(self.credential_reference)
        payload: dict[str, Any] = {
            "model": context.model,
            "instructions": context.system_instructions,
            "input": context.input_content,
            "max_output_tokens": context.max_output_tokens,
        }
        if context.temperature is not None:
            payload["temperature"] = context.temperature
        if context.output_schema is not None:
            payload["text"] = {
                "format": {
                    "type": "json_schema",
                    "name": "commerce_os_governed_output",
                    "strict": True,
                    "schema": context.output_schema,
                }
            }
        request = urllib.request.Request(
            f"{self.base_url}/v1/responses",
            data=json.dumps(payload).encode(),
            headers={"Authorization": f"Bearer {secret}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                body = json.loads(response.read())
        except urllib.error.HTTPError as exc:
            category = {
                400: "invalid_request",
                401: "authentication_error",
                403: "authentication_error",
                429: "rate_limit",
            }.get(exc.code, "provider_unavailable" if exc.code >= 500 else "invalid_request")
            raise ProviderExecutionError(
                category,
                f"Provider request failed with HTTP {exc.code}.",
                category in {"rate_limit", "provider_unavailable"},
            ) from None
        except TimeoutError:
            raise ProviderExecutionError("timeout", "Provider request timed out.", True) from None
        except (urllib.error.URLError, json.JSONDecodeError):
            raise ProviderExecutionError(
                "provider_unavailable", "Provider response was unavailable.", True
            ) from None
        try:
            content = json.loads(body["output_text"])
        except (KeyError, TypeError, json.JSONDecodeError):
            raise ProviderExecutionError(
                "invalid_response", "Provider returned an invalid structured response."
            ) from None
        usage = body.get("usage") or {}
        return ProviderResponse(
            content=content,
            provider_request_id=body.get("id"),
            input_tokens=usage.get("input_tokens"),
            output_tokens=usage.get("output_tokens"),
            total_tokens=usage.get("total_tokens"),
        )
