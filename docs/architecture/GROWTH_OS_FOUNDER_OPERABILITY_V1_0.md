# Growth OS Founder Operability v1.0

## Purpose

Sprint 069 turns the Growth workspace into a founder-operated path from real evidence to a recorded commercial outcome. It does not add autonomous research, sending, approval, finance, or learning authority.

## Founder workflow

1. Create a Growth workspace for a real experiment.
2. Import a real prospect and source-backed observation.
3. Review or add evidence and activate the prospect.
4. Select evidence visually and compose an opportunity and Growth diagnosis.
5. Create a customer-specific Growth Gift.
6. Request and receive human approval.
7. Create and approve an evidence-backed outreach draft.
8. Copy the approved draft and send it manually outside Commerce OS.
9. Record the observed send, reply, follow-up, or conversion.
10. Review Finance-owned actuals and evidence-linked learning.

The system next action is deterministic and derived from persisted lifecycle state. It is displayed separately from any AI recommendation.

## Evidence contract

Every downstream artifact uses selected `GrowthProspectEvidence` records. The picker presents source, type, collection time, confidence, and observation without exposing UUIDs. Unknown facts remain unknown. Evidence is not copied into conclusions and AI output cannot replace source evidence.

## Operational readiness

The authenticated readiness endpoint reports only safe status:

- Growth OS readiness
- tenant AI capability availability
- durable worker heartbeat and queued or failed Growth research counts
- database reachability
- manual send mode
- external connector availability

It never returns provider credentials, session material, or secrets. A missing AI provider does not block manual evidence work. A missing worker blocks queued research, not founder-authored review.

## Authentication decision

The web application continues to use the repository's server-side bearer session and `/auth/me` organization resolution. Credentials remain outside the browser bundle and every server action resolves the authenticated organization again. A browser-side local bootstrap was deliberately not added: it would create a second authentication model and weaken the Sprint 034 boundary. Production deployment still requires a proper interactive login/session issuance flow and external identity operations; this is an explicit deployment gap, not hidden by a development shortcut.

## Human authority and sending

Approval and execution are separate events. Approval never sends, publishes, discounts, or records revenue. Outreach is copied by the founder, sent manually, and then recorded as an observed event. External connectors remain unconfigured.

## Economics

Actual revenue, cost, and contribution profit come only from Finance records. Missing revenue or cost is displayed as `Unknown`; the UI never substitutes zero or derives profit from incomplete observations. Offers and forecasts remain advisory. Linking a Growth experiment directly to canonical Project/Product finance dimensions remains a future integration requirement.

## Failure and first-run behavior

Empty workspaces explain the next setup step and do not fabricate sample businesses. Research displays queued, running, completed, or failed state. Failed jobs preserve evidence and direct the founder to review before retry. Worker and AI configuration gaps are shown in business language.

## Security invariants

- all operational APIs require verified authentication, organization scope, and RBAC;
- no UUID entry is required for normal founder actions;
- AI remains advisory and tenant-scoped;
- approvals remain human-only and separation-of-duty rules remain enforced;
- no external communication or paid provider call occurs in local acceptance tests.
