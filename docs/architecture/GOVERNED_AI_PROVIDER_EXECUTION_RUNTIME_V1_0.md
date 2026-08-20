# Governed AI Provider Execution Runtime v1.0

Status: Frozen for Sprint 043

## Invariant

**AI INFERENCE ≠ BUSINESS AUTHORITY.** A successful response is information. It never means approved, executed, paid, refunded, published, purchased, ordered, budget changed, or customer contacted.

## Ownership and flow

AI Runtime is infrastructure. It owns governed inference transport, provider routing, runtime provenance, operational usage/cost evidence, and normalized failures. Source domains continue to own Product Truth, customers, conversations, Finance truth, Growth and Operations execution, approvals, and business decisions.

```mermaid
flowchart LR
    E["Evidence / Business Context"] --> R["Governed AI Request"]
    R --> A["Authority Gate"]
    A --> G["Cost / Rate Gate"]
    G --> P["Provider Router"]
    P --> D["Provider Adapter"]
    D --> O["AI Response"]
    O --> S["Schema Validation"]
    S --> U["Provenance / Usage / Cost"]
    U --> I["Advisory Domain Output"]
    I --> H["Human / Governed Workflow"]
```

## Provider and secret boundary

The canonical Sprint 035 provider/model registries are extended with base URL, credential reference, timeout, and non-secret runtime controls. Database and API records contain only an environment variable reference. Runtime resolution occurs immediately before transport. Secrets are never persisted, returned, audited, logged, or included in normalized exceptions.

The first real adapter uses the OpenAI-compatible Responses API shape. It serializes the request, invokes the provider, normalizes errors, extracts structured response and usage metadata, and contains no Commerce OS business logic. A deterministic adapter provides credential-free CI coverage. Later Anthropic, Gemini, DeepSeek, gateway, image, video, or speech adapters can implement the same contract.

## Lifecycle and governance

The execution extension uses `queued → running → succeeded`, with terminal `failed`, `timed_out`, `rate_limited`, and `cancelled` paths. Only draft or queued work can be cancelled. Terminal records cannot be reopened. Governed prompt versions are snapshotted by ID/version metadata; provider/model, timestamps, source context, classification, runtime configuration, result, usage, and failures remain auditable.

Only recommendation, draft, analysis, candidate, and classification outputs are representable. A deterministic authority gate rejects execution-oriented requests before provider invocation. Structured JSON is validated against supplied required fields/types; malformed output becomes `invalid_response` and is never treated as valid.

## Rate, cost, and failure controls

Local organization/provider/model request limits run before external invocation. Preflight cost estimates use configured model rates and explicit token limits. Per-request and rolling organization budget limits reject work before transport. AI cost observations distinguish estimated from provider-reported values and remain operational evidence; Finance retains monetary truth. Missing usage remains null.

Failures normalize to authentication, rate limit, timeout, unavailable provider, invalid request/response, safety rejection, cost limit, or internal error without exposing secrets. Retry is bounded and limited to explicitly retryable transient failures.

## Worker and integration boundary

The execution service accepts an explicit service actor and is compatible with the existing worker composition root; service identities receive no human approval authority. Sprint 043 keeps processing controllable without adding distributed orchestration.

The first domain composition path maps successful `ANALYSIS` output into a draft Sprint 038 Research Analysis record. The application layer performs this composition. It cannot create opportunities, approvals, launches, Product Truth changes, Growth execution, customer contact, or Finance mutations.

## OpenAI-compatible implementation note

The adapter follows the official OpenAI Responses API conventions for instructions/input, bearer credentials, usage metadata, and JSON Schema structured output. Provider-specific availability, pricing, and limits remain configuration rather than hard-coded assumptions.
