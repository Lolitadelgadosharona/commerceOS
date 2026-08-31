# Commerce Intelligence Control Plane v1.0

## Purpose

Sprint 070 makes the existing Market, Product, Opportunity, and Governance records operable from the Commerce OS frontend. It does not introduce a new source of truth, scoring model, approval path, or business workflow.

## Implemented graph

```text
MarketDataSource -> MarketSignal -> MarketSignalEvidence
                                -> MarketSignalCluster (through membership)
                                -> MarketOpportunity (through explicit link)

DemandSignalSource -> DemandSignal -> DemandSignalEvidence
                                  -> OpportunityCandidate evidence

MarketOpportunity <- ProductHypothesis
ProductHypothesis -> ProductEconomics
                  -> SupplierCandidate
                  -> ProductRisk
                  -> ProductInvestmentScore

Product -> ProductTruth (versioned, approved publication only)

MarketOpportunity -> ApprovalRequest -> DecisionQueueItem
```

The product-to-opportunity relationship is represented by `ProductHypothesis.opportunity_id`. The frontend does not infer a Product Truth relationship from a hypothesis. Market signals and demand signals are evidence; neither creates a product or approval.

## UI contracts

- `/market-intelligence` composes market sources, signals, evidence, clusters, demand signals, demand evidence, and the demand dashboard.
- `/market-intelligence/[id]` resolves a signal from the tenant-scoped list and shows only its linked evidence.
- `/products` composes product hypotheses, economics, supplier candidates, risks, investment scores, sellable products, and Product Truth versions.
- `/products/[id]` resolves a hypothesis from the tenant-scoped list and links to its recorded source opportunity.
- `/opportunities` remains the canonical separation between advisory discovery candidates and governed MarketOpportunity investment records.
- `/decision-committee` composes ApprovalRequest and DecisionQueueItem records and sends investment decisions to the existing Opportunity detail workflow.
- `/decisions` redirects to the canonical committee route.

All reads use the server-side API client, `cache: no-store`, bearer authentication, `/api/v1/auth/me` organization resolution, and organization-scoped queries.

## Financial classification

ProductEconomics inputs are estimates in the current contract and are displayed as `ASSUMPTION`. Finance-owned actual observations remain `ACTUAL` only when sourced from Finance APIs. Missing values are `UNKNOWN`; the frontend does not coerce missing data to zero. A `FORECAST` label is reserved for an explicit persisted forecast contract and is not assigned to ProductEconomics.

## Failure behavior

Each workspace has explicit authentication, empty, not-found, and section-failure states. A failure in supporting evidence does not hide otherwise valid core records. No fixture or placeholder data is used at runtime.

## Known gaps

### P0

- Production interactive identity/session issuance remains required before public deployment.
- External evidence connectors and controlled collection policies are not activated; the UI can only show persisted records.

### P1

- MarketSignalOpportunityLink has no list/read endpoint, so signal detail cannot display the explicit opportunity edge without a backend contract.
- Product hypothesis detail has no single-resource tenant-scoped endpoint; the frontend safely resolves it from the organization-scoped list.
- ProductEconomics does not store field-level provenance or an explicit actual/assumption/forecast classification.

### P2

- Cluster membership has no read endpoint, limiting cluster drill-down.
- Decision Queue supports generic lifecycle state but no dedicated committee packet read model.
- Product Truth and product hypotheses are intentionally separate and lack a promotion projection for side-by-side comparison.

## Authority boundary

The control plane reads evidence and exposes the existing governed investment action. It cannot create products from signals, publish Product Truth, bypass self-approval controls, move money, or start external execution.
