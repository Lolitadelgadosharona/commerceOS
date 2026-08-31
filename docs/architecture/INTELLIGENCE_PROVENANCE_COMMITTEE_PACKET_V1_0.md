# Intelligence Provenance and Committee Packet v1.0

## Purpose

This foundation makes Commerce OS intelligence traceable from observed market evidence through product hypotheses and governed investment review. It adds read projections; it does not transfer source-of-truth ownership or grant execution authority.

## Ownership and boundaries

- Intelligence owns Market Signals, Opportunity evidence, Product Hypotheses, supplier candidates, Product Risks, and advisory economics inputs.
- Build owns canonical Product and Product Truth records.
- Governance owns Approval Requests and human decision authority.
- Finance owns actual monetary truth. Intelligence economics remain estimates, quotes, observations, assumptions, forecasts, AI inferences, or unknowns.
- The Investment Committee Packet is read-only composition. It never approves, launches, spends, publishes, or mutates source records.

## Traceability contracts

- A Market Signal can project its explicit `MarketSignalOpportunityLink` relationships and the linked Opportunity summaries.
- A Market Signal Cluster can project persisted memberships, signals, and signal evidence.
- A Product Hypothesis detail read is tenant scoped and retains its required Opportunity link.
- Product Hypothesis and Product Truth are not canonically related in v1. The UI must state `No approved Product Truth yet` and must not infer identity from names.

## Economics provenance

`ProductEconomicInputProvenance` records one source classification per economic metric. Supported classifications are `actual`, `quoted`, `observed`, `assumption`, `forecast`, `ai_inference`, and `unknown`.

`unknown` requires a null value. Every other classification requires a numeric value, including a known zero. This prevents missing information from silently becoming zero. Source, confidence, as-of time, evidence reference, and notes remain visible to reviewers.

## Investment Committee Packet

The packet composes the Opportunity, Opportunity evidence, linked Market Signals, Product Hypotheses, field-level economics provenance, supplier candidates, Product Risks, investment scores, existing investment memo, Approval Request, Decision Queue item, and Launch Readiness.

It presents supporting evidence, opposing risks and unknowns, missing evidence, unavailable sections, and deterministic decision-quality warnings. Warnings include single-source dependence, missing product thesis, unknown critical economics, supplier cost assumptions, missing supplier evidence, missing ProductRisk records, approval before a report, and incomplete launch readiness.

Approval semantics are unchanged. The existing governed approval actions remain the only decision write path.

## Security

All endpoints remain behind the existing `/api/v1` authentication and authorization dependency, require `api.read` for reads, validate organization scope, and return no cross-tenant records. Frontend reads use `/auth/me`, server-side bearer handling, and no-store behavior from the shared API client.
