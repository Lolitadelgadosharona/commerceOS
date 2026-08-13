# Commerce OS Module Boundary v1.0

Status: frozen modular-monolith dependency policy

## Universal boundary rules

The eight domains are Python modules in one deployable backend for V1, not eight services. Each owns its aggregate writes and exposes a narrow public application interface plus versioned events. No module imports another domain’s `domain`, `infrastructure`, SQLAlchemy models, database tables, or private API. Cross-domain commands go through public ports; cross-domain facts flow through events/read projections. Governance checks are injected as ports/middleware, not imported as mutable global state.

`shared` contains only typed identifiers, time/money primitives, event envelope, authorization context, common errors, and transaction abstractions. If a type has business lifecycle or policy, it belongs to a domain rather than `shared`.

`ai_runtime` is cross-cutting execution infrastructure rather than a ninth business domain. It owns provider/model metadata, governed request/provenance records, prompt versions/evaluations, and advisory usage costs. Governance supplies authority policy; requesting domains retain purpose and source truth. The runtime cannot approve, execute business workflows, or write owning-domain aggregates.

## Domain boundaries

| Module | Ownership | Responsibilities | Prohibited dependencies |
|---|---|---|---|
| Intelligence | `CustomerSignal`, `SignalCluster`, `MarketOpportunity`, opportunity/product hypotheses, supplier evaluation profiles/matches/decisions, evidence/economics/scores/risks, `RootCauseCase`, Customer 360 projections | Evidence synthesis, customer/opportunity/product/supplier intelligence, deterministic scoring and economics, clustering, analysis, lineage/confidence | Cannot import Operations customer/order/supplier repositories, Finance ledgers, Decision internals, promote hypotheses into execution truth, procure/pay suppliers, or write Product Truth/approvals/execution state |
| Decision | `VentureOpportunity`, `Decision`, creative strategies/hypotheses/briefs/channel fits/experiment observations and recommendations | Evidence-backed alternatives, creative planning and test observations, recommendation/decision records, economics requests, rationale | Cannot import Build/Growth/Operations infrastructure, generate artifacts, execute experiments/providers/channels, write financial truth, or approve its own decision |
| Build | `Product`, versioned `ProductTruth`, product knowledge/claim policies, listing strategies/briefs/discovery evidence, creative artifacts/executions | Product/content construction, product knowledge and claim guardrails, GEO-ready knowledge structures, QA state, model-execution records, approved Product Truth publication workflow | Cannot import Growth channel adapters, Learning internals, Finance ledgers, Intelligence hypotheses, generate/publish listings, or self-authorize publication/spend |
| Growth | Acquisition workflow, campaign/channel execution state, `AttributionTouch` | Governed organic/paid channel execution, acquisition experiments, attribution evidence | Cannot write Finance revenue/budgets, Operations customer/order state, Product Truth, or bypass Governance approval |
| Operations | `Brand`/`Store` operational records, `Supplier`, `Customer`, conversations, `SalesOpportunity`, `Order`, `Handoff` | Customer/supplier operations, B2C/B2B workflows, fulfillment, support, handoff | Cannot write Finance ledgers, Governance approvals/identity policy, Decision venture state, or import Growth/Finance infrastructure |
| Finance | `Transaction`, `Expense`, `Revenue`, financial economics/classification | Ledger truth, reconciliation, forecasts/economics inputs, financial-control requirements | Cannot execute operational/channel actions, write approvals, Product Truth, attribution, or depend on AI/provider SDKs in domain logic |
| Learning | `LearningRecord`, learning synthesis/proposals | Append-only observations, experiment outcome synthesis, cross-functional feedback | Cannot write any source-domain aggregate, Product Truth, policies, permissions, approvals, routing weights, or production configuration |
| Governance | `Organization`, `Project`, `CustomerIdentity`, `Approval`, `Experiment`, `CommercialPolicy`, registries/permissions/audit standards | Scope/identity, authorization, approvals, policy, experiments, provider/channel registry controls, compliance workflow | Cannot own operational/financial/product truth, execute business actions, import domain infrastructure, or let provider/LLM output modify authority |

## Allowed interaction patterns

1. Same-request coordination uses application ports and a defined transaction owner; it does not share ORM entities.
2. Post-commit propagation uses the PostgreSQL transactional outbox and versioned business events.
3. Read models subscribe to events or call authorized query ports; they are never write-back paths.
4. Workflows/sagas store their own coordination state and invoke domain commands; they cannot mutate multiple domain tables directly.
5. Finance and Governance can deny/require approval through deterministic interfaces. They do not take ownership of the requesting aggregate.

## Architecture enforcement

Sprint 001 must add import/dependency tests, package-public-surface tests, and database ownership conventions. CI fails on private cross-domain imports, direct cross-domain repository/table access, or business types added to `shared` without architecture review.
