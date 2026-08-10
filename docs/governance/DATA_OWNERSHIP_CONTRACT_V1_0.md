# Commerce OS Data Ownership Contract v1.0

Status: canonical logical ownership; physical stores and service names are intentionally unspecified

## Contract rules

The source of truth is the authoritative Commerce OS aggregate or ledger named below. External provider records are evidence or execution receipts, not canonical IDs. Writes require authenticated actor, tenant/project scope, authorization, validation, idempotency where applicable, version conflict protection, and an append-only audit/event record. Consumers receive only purpose-authorized fields.

| Entity | Owner | Source of truth | Write authority | Read consumers | Audit requirement |
|---|---|---|---|---|---|
| `Customer` | Operations | Canonical Commerce OS customer aggregate linked to identity observations | Operations service; human correction under Governance policy | Intelligence, Growth, Finance, Learning, Support | Create/update/merge/split, field provenance, actor, reason, identity linkage |
| `Product` | Build | Canonical product aggregate | Build workflow; owner-authorized lifecycle transitions | All domains as purpose permits | Versioned mutations, actor, source, lifecycle transition |
| `ProductTruth` | Build | Approved immutable/versioned truth release | Authorized product owner through Governance approval; never AI/Learning alone | Decision, Growth, Operations, Finance, Learning | Full version diff, evidence, approver, effective time, supersession |
| `Supplier` | Operations | Canonical supplier/counterparty aggregate | Authorized Operations role; payment details need strong verification | Build, Finance, Governance | Identity/bank-detail changes, verification, access, actor |
| `VentureOpportunity` | Decision | Decision-domain venture aggregate | Authorized owner/Decision workflow; AI may draft/rank | Intelligence, Build, Finance, Learning | Evidence, score/assumptions, stage changes, decision actor |
| `SalesOpportunity` | Operations | B2B pipeline aggregate | Authorized Sales/Operations role; AI only within delegated workflow | Decision, Finance, Intelligence, Learning | Stage/value/terms changes, actor, source conversation, approvals |
| `Order` | Operations | Commerce OS order aggregate reconciled to commerce/payment receipts | Authorized order workflow; customer confirmation and policy as required | Customer service, Finance, Intelligence, Learning | State transitions, line/price snapshot, actor, idempotency, external receipt |
| `Transaction` | Finance | Append-only financial transaction ledger | Finance ingestion/reconciliation; corrections by compensating entry | Finance, Governance, authorized dashboards/Learning | Immutable entry, source document, reconciliation, correction linkage |
| `Expense` | Finance | Finance expense ledger/classification | Finance service or authorized finance role; commitments gated | Decision, Growth, Operations, Learning | Amount/currency/vendor/category, evidence, approval, actor |
| `Revenue` | Finance | Finance revenue ledger/classification | Finance reconciliation only; attribution cannot write truth | Decision, Growth, Intelligence, Learning | Transaction/order lineage, recognition/classification changes |
| `Approval` | Governance | Append-only approval decision record | Authenticated authorized human; service may request/expire, never self-approve | Command owners, Finance, audit, dashboards | Request/decision, scope, before/after, policy, authority, expiry, idempotency |
| `Experiment` | Governance | Versioned Experiment Registry | Authorized experiment owner; treatments need domain/finance approvals | Decision, Build, Growth, Intelligence, Learning | Hypothesis, metrics, population, risks, approvals, assignments, stop decision |
| `LearningRecord` | Learning | Append-only Learning store | Learning ingestion/analysis with provenance; promotion requires owner approval | Intelligence, Decision, domain owners, Governance | Evidence links, model/method/version, confidence, correction/supersession |
| `SignalSource` | Intelligence | Intelligence source registry | Authorized internal Intelligence workflow; connectors remain separate adapters | Intelligence, Governance, Learning | Source creation/state, organization, type, actor |
| `CustomerSignal` | Intelligence | Intelligence signal store with immutable source references | Authorized Intelligence ingestion using permitted evidence; source/customer scope validated | Intelligence, Decision, Build, Growth, Operations, Learning | Source lineage, classification, confidence, actor, corrections |
| `CustomerVoiceCluster` | Intelligence | Intelligence cluster aggregate plus explicit membership records | Authorized Intelligence workflow using selected signals; no implicit AI grouping in V1 | Intelligence, Decision, Build, Growth, Operations, Learning | Membership, count, severity/trend inputs, method/version |
| `CustomerInsight` | Intelligence | Intelligence insight aggregate plus explicit evidence records | Authorized Intelligence workflow; text and recommended action are human/rule supplied in V1 | Decision and affected domain owners, Governance, Learning | Evidence links/count, impact, status changes, actor/method |
| `MarketOpportunity` | Intelligence | Intelligence market-observation aggregate | Authorized Intelligence workflow using supplied evidence; qualification does not create a venture decision | Decision, Build, Finance, Learning | Trigger, timing, geography, confidence, lifecycle, actor |
| `OpportunityEvidence` | Intelligence | Intelligence evidence links | Authorized Intelligence workflow; external references are supplied observations, not connector output in V1 | Intelligence, Decision, Governance, Learning | Source type/reference, summary, confidence, opportunity lineage |
| `ProductCandidate` | Intelligence | Intelligence product-hypothesis records | Authorized Intelligence workflow; selection remains non-authoritative until a later governed product/venture workflow | Decision, Build, Finance | Opportunity link, need, estimated margin, risk/status changes |
| `OpportunityScore` | Intelligence | Versioned deterministic score record | Frozen scoring service only | Decision, Finance, Governance, Learning | Inputs, overall score, formula version, timestamp |
| `OpportunityRisk` | Intelligence | Intelligence opportunity-risk observations | Authorized Intelligence workflow; accepting risk here does not grant business authority | Decision, Governance, Finance, Build | Type, severity, status, description, opportunity lineage |

## Naming and projection constraints

- No generic internal `Opportunity` type: market/business opportunities are `VentureOpportunity`; B2B deals are `SalesOpportunity`.
- Customer 360 is a permission-filtered projection and never a source of truth.
- Attribution is evidence associated with Finance truth; it cannot mutate `Revenue`.
- Deletion/retention actions preserve required financial and approval audit while removing or de-identifying PII as allowed by policy and law.

See the [Domain Ownership Model](./DOMAIN_OWNERSHIP_MODEL_V1_0.md), [Security Foundation](./SECURITY_AND_PRIVACY_FOUNDATION_V1_0.md), and [Finance Authority Model](./FINANCE_AUTHORITY_MODEL_V1_0.md).
