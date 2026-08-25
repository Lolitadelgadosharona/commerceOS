# Growth OS Founder Revenue Workspace v1.0

## Purpose

Sprint 068 exposes the existing Growth OS domain as a founder-operated local revenue workflow. It is an initial B2B vertical slice, not a redefinition of Growth OS around email or consulting.

## Operational flow

Revenue Experiment → Prospect Candidate → Evidence → Qualification / Research → Active Prospect → Diagnosis → Growth Gift → Outreach Draft → Human Approval → Manual External Action → Observed Outcome → Finance Observation → Learning Recommendation.

## Ownership and truth

- Growth owns prospect, diagnosis, gift, outreach draft, outcome, and learning workflow records.
- Governance owns approval authority. AI and service identities cannot approve.
- Finance owns recorded revenue, cost, and contribution profit.
- External actions remain human-controlled. The UI never equates an approved draft with a sent message.
- Manual evidence is stored with provenance. AI-derived analysis is visually and structurally distinct from source evidence.

## Background execution

Growth research requests write a durable organization-scoped outbox event in the same transaction as the research run. The worker claims one event with database locking, records explicit processing state, executes through the governed AI runtime, and marks completion or a bounded retry failure. The existing outbox is used, so no new queue table or migration is required. Redis remains available for future transport use but is not treated as durable job truth.

## Local limitations

- No external email sender is configured; founders send manually and record the observed event.
- No unrestricted crawler or social, advertising, publishing, payment, creative-generation, or Shopify connector is introduced.
- AI research requires an available tenant-scoped model capability. Missing configuration is shown as a blocked capability, never a fake success.
- Diagnosis, Growth Gift, outreach, offer, finance, and learning records shown in the workspace are existing backend facts. Empty data remains an honest empty state.

## Extension boundary

Channel-specific execution adapters can later attach to the common evidence, approval, event, finance, and learning contracts. The workspace does not encode email as the only channel.
