# Governed Shopify Channel Adapter v1.0

Status: frozen for Sprint 076

## Purpose and ownership

The adapter projects an exact approved Commerce OS Listing version into a Shopify **draft** product. Build owns Product Truth and Listing Truth, Governance owns authorization, Operations owns the integration workflow, and Shopify owns its external resource. The adapter does not own pricing truth, inventory truth, publication, traffic, or customer acquisition.

## Connection and credentials

A tenant-scoped `ShopifyConnection` records the merchant domain, API version, granted scopes, policy and lifecycle. It stores only an environment-variable reference. The token is resolved in the server or Worker process and is never returned by an API, rendered in the browser, logged, or stored in the database.

V1 supports a deliberately bounded local-token connection for a merchant-owned development store and leaves an OAuth-compatible authentication mode in the contract. A production multi-merchant installation must add OAuth authorization-code exchange, encrypted/managed secret storage, revocation and reinstall handling before use.

The least Shopify scopes for this bounded product-draft workflow are `read_products` and `write_products`. Shopify documents access-scope configuration and the `productSet` write requirement in its official [access-scope guide](https://shopify.dev/docs/apps/build/authentication-authorization/manage-access-scopes) and [GraphQL mutation reference](https://shopify.dev/docs/api/admin-graphql/latest/mutations/productSet).

## Projection and validation

The projection is deterministic and version pinned:

- the exact approved `ProductTruth` id/version;
- the exact approved Listing id/version;
- factual title, HTML description, vendor, product type, SEO data, options, variants, metafields and supplied media references;
- external status fixed to `draft`;
- no fabricated inventory quantities.

Readiness blocks missing/invalid connection, missing scopes, absent or stale approved Listing, missing price, incomplete variants and required media. Optional media and SEO gaps remain explicit warnings. A changed Listing or Product Truth invalidates prior authorization and requires a new request.

## Governed lifecycle

`readiness → request → ApprovalRequest/DecisionQueue → human decision → authorize exact source snapshot → explicit execute → Outbox → Worker → adapter → external draft → reconcile`

Approval is not execution. Authorization pins the approved source and projection hash but does not call Shopify. A separate authenticated human action writes an idempotent Outbox command. The Worker executes with a scoped service identity and records the initiating human.

## Create, update, idempotency and drift

The first successful command creates one external draft and stores its Shopify product/variant identifiers. Later approved Listing versions update that same linked product; they never silently create a duplicate. Idempotency is enforced by publication key, outbox command and persisted external-resource identity.

Reconciliation fetches the remote resource, compares an owned-field hash, and reports `in_sync`, `commerce_os_newer`, `shopify_changed_externally`, or `missing_external`. It never overwrites either side automatically. External drift requires human review and a newly authorized update.

## Failure and retry

Failures are classified without token or payload leakage: authentication, authorization/scope, validation, rate limit, provider, timeout and not found. Only transient rate-limit/provider/timeout failures are retryable, with bounded attempts and delayed Outbox availability. Validation and authorization failures require human correction.

## Rollback and webhooks

V1 rollback is governed compensating action: retain immutable publication/source history, restore an earlier approved Listing through a new authorization, and update the same external draft. Destructive deletion and automatic rollback are prohibited.

A tenant-scoped immutable webhook event contract exists for future reconciliation. No public webhook receiver, signature validation endpoint or automatic mutation is enabled in Sprint 076. Poll/manual reconciliation is the only active inbound path.

## Explicit boundaries

- No real Shopify credential is required for acceptance; deterministic adapters cover automated tests.
- No automated public sales-channel publication.
- No invented inventory, variants, media, price, claims or SEO.
- No Amazon, Etsy, Walmart, ads, Creative Factory, AI agent, purchasing, payment, freight, production deployment or Customer 360 behavior.
- Live Commerce to Customer Acquisition remains missing: a draft product alone cannot create traffic, checkout demand or revenue.

