# Commerce OS Security and Privacy Foundation v1.0

Status: minimum control baseline; applicable law and contractual obligations may impose stricter controls

## Security principles

Default deny, least privilege, defense in depth, explicit trust boundaries, data minimization, separation of duties, secure failure, auditable authority, provider replaceability, and tested recovery apply to every domain. External messages, files, callbacks, model output, and provider metadata are untrusted input.

## PII classification

| Class | Examples | Minimum handling |
|---|---|---|
| P0 Public | Approved public product content | Integrity/version controls; no confidentiality assumption |
| P1 Internal | Internal plans, aggregate non-identifying metrics | Authenticated workforce/service access; no public disclosure |
| P2 Confidential | Customer/supplier profiles, conversations, order details, business financials | Purpose-based access, encryption, audit, controlled export/retention |
| P3 Restricted | Credentials, tokens, payment/bank data, government IDs, precise sensitive traits, authentication factors | Strong encryption/tokenization, tightly limited access, no model/provider transfer by default, enhanced audit |

Derived/inferred data inherits the highest relevant sensitivity and records inference source/confidence. Payment-card data should remain with a compliant payment provider; Commerce OS stores tokens and minimum receipts, not raw card data.

## OAuth and authentication

- Use standards-based OAuth 2.1/OIDC patterns suitable to the client; Authorization Code with PKCE for interactive public clients.
- Validate issuer, audience, signature, expiry, nonce/state, redirect URI, and authorized party; reject insecure or ambiguous tokens.
- Request narrow scopes; use short-lived access tokens and protected, rotated refresh tokens; revoke on role/provider disconnect.
- Use distinct service identities for workloads. Never use a human token as a shared automation credential.
- Step-up authentication is required for sensitive identity, secret, bank-detail, authority, and high-impact financial changes.

## Least privilege and authorization

Every read and command is authorized by actor/service, tenant/project, resource, action, purpose, data class, policy version, and relevant amount/threshold. Enforce server-side at source and projection boundaries. Separate request, approval, execution, and reconciliation roles where risk warrants. Emergency access is time-bound, justified, reviewed, and audited.

## Audit logging

Log authentication and authorization outcomes; privileged/PII access; configuration, policy, role, identity-link, secret, provider, and financial changes; approval lifecycle; provider/tool invocation; exports/deletions; and security events. Records include event ID, time, actor, source, action, target, outcome, reason/policy, correlation/causation, and safe before/after references. Logs are append-only/tamper-evident, access-controlled, time-synchronized, monitored, and must not contain raw secrets or unnecessary sensitive payloads.

## Secret management

Store secrets only in an approved secret manager, encrypted with managed keys. Repositories, prompts, logs, events, analytics, and client bundles must not contain secrets. Scope credentials per environment/provider/purpose; rotate, revoke, inventory, and alert on misuse. Provider adapters receive credentials at runtime, and secret values are never returned through Customer 360 or model context.

## Retention and privacy lifecycle

Each data class must have documented purpose/legal basis, source, owner, geography, retention period, deletion/de-identification behavior, and legal-hold exception before collection. Retain the minimum duration; isolate backups and apply expiry. Support authorized access, correction, export, restriction, and deletion requests. Immutable audit/financial records retain minimum legally required facts while PII is removed, tokenized, or cryptographically isolated when permissible.

## Identity resolution safety

- Preserve every observation’s source, collection basis, time, normalization, match method, confidence, and model/rule version.
- Never merge solely on an LLM assertion or low-confidence fuzzy match.
- Apply deterministic unique matches only under approved policy; quarantine ambiguity and high-risk conflicts for human review.
- Make links explainable, contestable, reversible, and historically auditable; do not erase source identities on merge.
- Prevent cross-tenant linking unless a separately approved business/legal basis and access policy exists.
- Measure false-link/false-split rates, restrict sensitive-attribute use, and propagate corrections to projections.
- Customer 360 consumes permission-filtered links and cannot broaden access.

## Minimum readiness evidence

Before Sprint 001 production deployment: approved threat model, data inventory/flow map, authority matrix, retention schedule, provider data-use review, access-control tests, identity-link test corpus, incident/backup recovery procedures, and named security/privacy accountable owners.
