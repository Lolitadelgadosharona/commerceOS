# Shopify Real Validation Plan

Status: deferred by design; no real Shopify store is available in Sprint 077.

## Entry conditions

Use only a founder-owned Shopify development/test store, a non-production Commerce OS environment, a non-public test product, and authorized operator and approver accounts. Never paste a token into source, documentation, the browser, database records, logs, Outbox payloads, screenshots, or issue trackers. Do not expose a local Mac publicly.

## Procedure

1. **Secure credential setup.** Provision least-privilege development credentials through the approved server-side secret mechanism. Store only the environment/secret reference in Commerce OS. Verify redaction in configuration and process output.
2. **Connection validation.** Register the exact `*.myshopify.com` domain, validate through the version-pinned GraphQL endpoint, and confirm that authentication failures reveal no secret or response payload.
3. **Scope validation.** Confirm the returned access scopes contain exactly the permissions needed for the bounded draft-product workflow (`read_products`, `write_products`). Verify a missing scope blocks readiness.
4. **Merchant identity.** Confirm Shopify Shop ID, canonical domain, merchant display name, plan display name, and development-store indicator match the intended test merchant.
5. **One governed draft publication.** Use an approved Product Truth and Listing; review the projection; obtain a separate human approval; explicitly authorize; then explicitly execute one draft `productSet` create. Confirm it is not published to a sales channel and has no fabricated inventory.
6. **Idempotency.** Re-submit and re-process the same publication command. Confirm only one Shopify Product and one Commerce OS external reference exist.
7. **Reconciliation.** Fetch the external draft and verify the result is `IN SYNC` with no automatic mutation.
8. **Update.** Approve a new Listing version, obtain a new publication approval, execute it, and verify the same Shopify Product ID is updated.
9. **External drift.** Manually change a connector-owned field in the development store. Reconcile and verify `EXTERNAL DRIFT`, no automatic overwrite, and a human-review requirement.
10. **Rollback.** Approve a new Listing version that intentionally restores the previous safe content, obtain fresh approval, and update the same external draft. Verify immutable prior publication history remains intact.
11. **Webhook delivery.** Configure a secure non-local HTTPS receiver in the test environment. Deliver signed fixtures and Shopify test deliveries; verify raw-body HMAC, duplicate Webhook ID handling, wrong signatures, topic recording, and no automatic business mutation.
12. **Inventory safety.** Inspect GraphQL variables and the resulting product. Confirm the connector sends no inventory quantities and does not assume locations or stock.
13. **Credential audit.** Search database values, API responses, frontend output/bundles, application and worker logs, Outbox events, exceptions, environment templates, CI artifacts, and screenshots. The gate fails on any secret exposure.

## Evidence and exit gate

Capture sanitized timestamps, actor IDs, approval IDs, publication/outbox IDs, external resource IDs, request classifications, reconciliation states, and test results. Never capture credentials or raw sensitive payloads. Real merchant validation passes only when all steps succeed in one controlled run; production remains blocked until the production gaps in the Sprint 077 completion report are separately closed.
