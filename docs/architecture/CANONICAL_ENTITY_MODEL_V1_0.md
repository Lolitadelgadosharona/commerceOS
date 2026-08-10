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
| `ProductKnowledgeItem` | Typed supporting knowledge with confidence and approval state; subordinate to Product Truth | Build | Build product-knowledge store | Authorized Build workflow; approval status cannot publish Product Truth | Growth, Operations, Intelligence, Learning |
| `ProductClaimPolicy` | Brand-scoped deterministic guardrail for product claim categories | Build | Build claim-policy registry governed by brand policy | Authorized Build/Governance workflow | Product Truth publication, Growth, Operations, Governance |
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

## Sprint 002 governance identity extensions

These supporting entities implement, but do not change, the frozen ownership model:

| Entity | Purpose | Owning domain | Source of truth | Write authority | Primary consumers |
|---|---|---|---|---|---|
| `User` | Internal human or service principal profile and lifecycle state | Governance | Governance user registry | Authenticated Governance administration; initial bootstrap is deployment-controlled | Authentication, authorization, audit |
| `PasswordCredential` | One-way password verifier isolated from profile data | Governance | Credential store | Authentication service only | Authentication service |
| `Role` | Named Owner, Approver, Operator, or Viewer authority bundle | Governance | Governance role registry | Authorized Governance administrator | Authorization and approval services |
| `Permission` | Atomic resource/action capability | Governance | Governance permission registry | Authorized Governance administrator | Role composition and authorization checks |
| `UserRole` | Revocable organization/project-scoped role assignment | Governance | Governance assignment registry | Authorized Governance administrator | Authorization, approvals, audit |
| `ApprovalRequest` | V1 stateful request for a precisely scoped human decision | Governance | Governance approval-request store | Requester may request/cancel; distinct authorized human may approve/reject | Executing domains and audit |
| `AuditLog` | Append-only security and authority evidence | Governance | Governance audit store | Internal services append; no update/delete API | Governance, security, compliance |

## Sprint 003 customer intelligence extensions

| Entity | Purpose | Owning domain | Source of truth | Write authority | Primary consumers |
|---|---|---|---|---|---|
| `SignalSource` | Organization-scoped registry of permitted signal channel types | Intelligence | Intelligence source registry | Authorized internal Intelligence workflow | CustomerSignal ingestion and Governance review |
| `CustomerSignal` | Classified, confidence-scored observation retaining its source and content reference | Intelligence | Intelligence signal store | Authorized Intelligence ingestion after tenant/source validation | Clustering, insights, Decision, Build, Growth, Operations, Learning |
| `CustomerVoiceCluster` | Named deterministic grouping of explicitly selected signals | Intelligence | Cluster aggregate and membership rows | Authorized Intelligence workflow | Insights and affected domain owners |
| `CustomerInsight` | Business interpretation and recommended action grounded in explicit signal evidence | Intelligence | Insight aggregate and evidence rows | Authorized Intelligence workflow; human/rule supplied in V1 | Decision and affected domain owners, Governance, Learning |

## Sprint 004 opportunity intelligence extensions

| Entity | Purpose | Owning domain | Source of truth | Write authority | Primary consumers |
|---|---|---|---|---|---|
| `MarketOpportunity` | Evidence-backed observation of a possible market opening | Intelligence | Intelligence market-opportunity store | Authorized Intelligence workflow | Decision, Build, Finance, Learning |
| `OpportunityEvidence` | Supporting reference and supplied summary linked to a market observation | Intelligence | Intelligence opportunity-evidence store | Authorized Intelligence workflow | Scoring, Decision, Governance, Learning |
| `ProductCandidate` | Non-authoritative product hypothesis for an opportunity | Intelligence | Intelligence candidate store | Authorized Intelligence workflow; cannot create Product Truth | Decision, Build, Finance |
| `OpportunityScore` | Reproducible deterministic evaluation inputs and result | Intelligence | One current versioned score per MarketOpportunity | Frozen scoring service | Decision, Finance, Governance, Learning |
| `OpportunityRisk` | Typed risk observation for an opportunity | Intelligence | Intelligence opportunity-risk store | Authorized Intelligence workflow | Decision, Governance, Finance, Build |
| `ProductHypothesis` | Detailed proposed solution for a MarketOpportunity; not a Build Product | Intelligence | Intelligence product-hypothesis store | Authorized Intelligence workflow | Decision, Build, Finance, Governance |
| `ProductEconomics` | Deterministic estimated unit economics for a hypothesis | Intelligence | One current versioned economics row per ProductHypothesis | Frozen economics service | Decision, Finance, Build |
| `SupplierCandidate` | Non-authoritative manually supplied supplier reference | Intelligence | Intelligence supplier-candidate store | Authorized Intelligence workflow; no procurement authority | Build, Operations, Finance, Governance |
| `ProductRisk` | Typed product-specific risk observation | Intelligence | Intelligence product-risk store | Authorized Intelligence workflow; risk status is not approval | Decision, Build, Governance, Finance |
| `ProductInvestmentScore` | Reproducible deterministic hypothesis evaluation | Intelligence | One current versioned score per ProductHypothesis | Frozen scoring service | Decision, Finance, Governance, Learning |
| `SupplierProfile` | Non-authoritative evaluated supplier observation; not the Operations Supplier master | Intelligence | Intelligence supplier-profile store | Authorized Intelligence workflow | Decision, Build, Operations, Finance, Governance |
| `SupplierEvaluation` | Reproducible supplier evaluation evidence | Intelligence | Append-only Intelligence evaluation store | Frozen scoring service | Decision, Build, Operations, Finance, Governance |
| `SupplierRisk` | Typed supplier risk observation | Intelligence | Intelligence supplier-risk store | Authorized Intelligence workflow | Decision, Build, Operations, Governance |
| `ProductSupplierMatch` | Advisory fit assessment between Build Product and SupplierProfile | Intelligence | Intelligence match store | Deterministic match service | Decision, Build, Operations, Finance |
| `SupplierDecisionRecord` | Explainable advisory supplier choice | Intelligence | Intelligence decision-evidence store | Authorized Intelligence workflow with approved profile and recommended match | Decision, Build, Operations, Governance |
| `ListingStrategy` | Product-grounded positioning and differentiation plan; no publication authority | Build | Build listing-strategy store | Authorized Build workflow; approval requires Product Truth | Growth, Decision, Governance, Learning |
| `CustomerQuestion` | Provenanced product discovery or purchase question | Build | Build customer-question map | Authorized Build workflow using supplied evidence | Growth, Operations, Intelligence, Learning |
| `ProductDiscoveryKnowledge` | Confidence-scored entity relationship for future discoverability | Build | Build discovery-knowledge store | Authorized Build workflow; cannot create Product Truth | Growth, Intelligence, Learning |
| `ContentBrief` | Human-authored product content direction grounded in truth/evidence | Build | Build content-brief store | Authorized Build workflow | Growth, Governance, Learning |
| `ListingEvidence` | Provenanced support for product content planning | Build | Build listing-evidence store | Authorized Build workflow; specification references require matching Product Truth | Growth, Governance, Learning |

`MarketOpportunity` is intentionally distinct from Decision-owned `VentureOpportunity` and Operations-owned `SalesOpportunity`. Qualification or a high score is evidence for a later decision; it is not investment authority, a product commitment, or a customer deal.
