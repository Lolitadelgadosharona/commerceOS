# Commerce OS Canonical Entity Model v1.0

Status: logical contract; no physical schema is selected

## Model rules

Each entity has one canonical source of truth and one write-owning domain. Other domains consume authorized APIs, projections, or append-only events. External systems contribute observations and execution receipts but never define Commerce OS canonical identifiers. All mutable entities carry a typed identifier, organization scope, version, lifecycle state, actor provenance, and audit timestamps as applicable.

| Entity | Purpose | Owning domain | Source of truth | Write authority | Primary consumers |
|---|---|---|---|---|---|
| `Organization` | Top-level legal/operating boundary and future tenant | Governance | Commerce OS organization registry | Owner through Governance-controlled administration | Every domain for scope and authorization |
| `Brand` | Commercial identity, policy, and presentation boundary within an organization | Governance | Commerce OS brand registry | Owner or delegated Governance administrator | Build, Growth, Operations, Intelligence |
| `Store` | Commerce sales surface/account tied to a brand | Operations | Commerce OS store registry reconciled to platform observations | Authorized Operations role; sensitive connection changes need Governance control | Growth, Finance, Operations, Intelligence |
| `Project` | Bounded initiative/work context across domains | Governance | Commerce OS project registry | Owner or delegated project administrator | All participating domains |
| `VentureOpportunity` | Market/business opportunity under evaluation | Decision | Decision-domain venture aggregate | Owner/authorized Decision workflow; AI may draft or rank | Intelligence, Build, Finance, Learning |
| `Product` | Lifecycle identity for an offered good/service | Build | Build-domain product aggregate | Authorized Build workflow | Decision, Growth, Operations, Finance, Learning |
| `ProductTruth` | Approved versioned claims, attributes, constraints, and evidence | Build | Approved Product Truth release | Authenticated product owner via Governance approval; never Learning/AI alone | Decision, Growth, Operations, Intelligence, Learning |
| `Supplier` | Counterparty able to provide goods/services | Operations | Operations supplier aggregate | Authorized Operations role; payment identity requires independent verification | Build, Finance, Governance |
| `Customer` | Canonical commercial/customer subject | Operations | Operations customer aggregate | Operations service; human merge/split/correction under policy | Intelligence, Growth, Finance, Learning, Support |
| `CustomerIdentity` | Provenanced identity observations and reversible links | Governance | Identity-resolution aggregate | Identity service within approved deterministic policy; ambiguous/high-risk links require authorized review | Operations, Intelligence, Growth, Finance |
| `SalesOpportunity` | B2B commercial deal and stage history | Operations | Operations B2B pipeline aggregate | Authorized Sales/Operations role; AI limited to delegated draft/workflow actions | Decision, Finance, Intelligence, Learning |
| `Order` | Customer purchase obligation and fulfillment state | Operations | Commerce OS order aggregate reconciled to provider receipts | Authorized order workflow subject to product, price, customer, and policy controls | Finance, Support, Intelligence, Learning |
| `Transaction` | Immutable monetary movement or financial posting | Finance | Finance transaction ledger | Finance ingestion/reconciliation; correction by compensating entry | Finance, Governance, authorized reporting/Learning |
| `Expense` | Cost/commitment classification and evidence | Finance | Finance expense ledger | Finance service/role after required approval | Decision, Growth, Operations, Learning |
| `Revenue` | Authoritative revenue recognition/classification | Finance | Finance revenue ledger | Finance reconciliation; attribution cannot write it | Decision, Growth, Intelligence, Learning |
| `Decision` | Versioned choice with alternatives, rationale, evidence, and authority | Decision | Decision register | Authorized decision owner; AI may recommend but not impersonate authority | Executing domain, Governance, Learning |
| `Approval` | Authenticated authorization for a precisely scoped action | Governance | Append-only approval store | Authorized human approver; service may request/expire only | All command owners, Finance, audit/dashboard |
| `Experiment` | Hypothesis, treatment, population, metrics, safeguards, and lifecycle | Governance | Experiment Registry | Authorized experiment owner plus affected domain/Finance approvals | Decision, Build, Growth, Intelligence, Learning |
| `LearningRecord` | Append-only observation or synthesized lesson with provenance/confidence | Learning | Learning store | Authorized ingestion/analysis; promotion requires owning-domain approval | Intelligence, Decision, every domain owner, Governance |

## Relationships and naming constraints

- An `Organization` contains zero or more `Brand`, `Store`, and `Project` records. V1 may create exactly one of each required default scope without exposing multi-tenant administration.
- A `Brand` may have multiple `Store` records. A `Project` may reference one brand/store or be organization-wide.
- `VentureOpportunity` can lead to a `Product` decision but is never a B2B deal.
- `SalesOpportunity` represents only a B2B deal and may result in an `Order`.
- `ProductTruth` versions belong to one `Product`; publication is an approval-gated transition.
- `Transaction`, `Expense`, and `Revenue` remain Finance truth even when linked to orders, experiments, campaigns, or attribution.
- `Decision`, `Approval`, `Experiment`, and `LearningRecord` preserve their distinct semantics: recommendation/choice, authority, controlled test, and observation.

Physical tables, indexes, storage engines, and API endpoints are Sprint 001 design decisions governed by this contract and the [Data Ownership Contract](../governance/DATA_OWNERSHIP_CONTRACT_V1_0.md).
