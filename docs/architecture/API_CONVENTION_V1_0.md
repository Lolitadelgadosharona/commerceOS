# Commerce OS API Convention v1.0

Status: technology-neutral external and inter-module contract convention

## API style

V1 uses resource-oriented HTTPS JSON APIs for synchronous commands/queries and versioned business events for asynchronous integration. REST is the default public/integration style. Internal module calls may use in-process typed interfaces in a modular monolith, but must preserve the same ownership and authorization boundaries. GraphQL, public RPC, and direct cross-domain database writes are out of scope unless approved by an architecture decision record.

## Naming and representation

- Paths and JSON fields use lowercase `snake_case`; resource collections use plural nouns: `/api/v1/sales_opportunities`.
- Canonical entity type names remain PascalCase in documentation/code types: `SalesOpportunity`, never generic `Opportunity`.
- IDs are opaque typed strings; clients do not parse or derive meaning from them.
- Timestamps use RFC 3339 UTC with explicit offset; dates use ISO 8601; money uses integer minor units plus ISO 4217 currency; decimal quantities use strings when precision matters.
- Enums are documented stable lowercase strings. Unknown future enum values must not be treated as authorization.
- Optional, nullable, absent, and redacted fields have distinct schema semantics.

## HTTP semantics

- `GET` is side-effect free; `POST` creates or invokes a command; `PATCH` applies an explicitly modeled partial update; `DELETE` is used only for allowed lifecycle/deletion behavior, never hidden audit erasure.
- Use standard status codes: `200/201/202/204`, `400`, `401`, `403`, `404`, `409`, `412`, `422`, `429`, and `5xx` as appropriate.
- Mutation requests accept `Idempotency-Key`; concurrency-sensitive updates require an entity version/ETag precondition.
- List endpoints use stable cursor pagination, explicit sort/filter allowlists, bounded page size, and permission-filtered results.
- Long-running work returns an operation/job reference and exposes observable state rather than holding a request indefinitely.

## Versioning and compatibility

Major API version is in the path (`/api/v1`). Additive compatible fields do not require a new major version. Breaking semantic/schema changes require a new major version, migration guide, overlap window, telemetry, and rollback plan. Every event carries its own schema version. Provider API versions stop at adapters and never become Commerce OS domain versions.

## Authentication and authorization boundary

The backend validates authenticated human/service identity and derives organization/project scope from trusted credentials/session. It authorizes every resource/action/purpose and relevant financial threshold server-side. The frontend, provider callback, model output, request-supplied role, or organization ID is never an authority source. Service-to-service calls use distinct short-lived workload identities. Provider callbacks require signature/authentication, timestamp/replay checks, allowlisted source configuration where useful, and idempotency.

## Error handling

Errors use a consistent envelope:

```json
{
  "error": {
    "code": "approval_required",
    "message": "Human approval is required before this action can execute.",
    "request_id": "req_opaque",
    "details": []
  }
}
```

`code` is stable and machine-readable; `message` is safe for the caller; `request_id` correlates protected logs. Validation details identify safe field/code pairs. Errors never expose secrets, stack traces, internal topology, raw provider payloads, existence of unauthorized resources, or unnecessary PII. Retries occur only for documented retryable codes and respect backoff/idempotency.

## Event conventions

Events are immutable facts named `<domain>.<past_tense_fact>` and use the envelope in [Architecture Freeze v1.1](./ARCHITECTURE_FREEZE_V1_1.md). Events include `event_id`, `event_type`, `occurred_at`, `actor`, `source`, `idempotency_key`, `correlation_id`, `causation_id`, contextual IDs, schema version, and minimized payload/reference. Consumers assume at-least-once, tolerate replay/ordering gaps, and deduplicate. Corrections append a correction/supersession event; events do not grant command authority.

## Documentation and testing

Implemented APIs and events require machine-readable schemas, examples, authorization requirements, error codes, idempotency/concurrency behavior, owner, compatibility tests, and threat-focused tests. The schema technology and generation tooling are selected with the implementation stack.
