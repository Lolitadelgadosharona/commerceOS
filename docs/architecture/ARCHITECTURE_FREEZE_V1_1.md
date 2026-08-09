# COMMERCE OS — INCREMENTAL ARCHITECTURE FREEZE v1.1

Status: proposed incremental freeze; architecture/planning only

Supersedes: no repository artifact; requires reconciliation with the prior external freeze

Evidence limitation: [repository discovery](./REPOSITORY_DISCOVERY_AND_DRIFT.md)

Governed by the [AI Commerce OS Constitution](../governance/AI_COMMERCE_OS_CONSTITUTION_V1_0.md), [PRD](../product/COMMERCE_OS_PRD_V1_0.md), [Domain Ownership Model](../governance/DOMAIN_OWNERSHIP_MODEL_V1_0.md), [Data Ownership Contract](../governance/DATA_OWNERSHIP_CONTRACT_V1_0.md), [Security and Privacy Foundation](../governance/SECURITY_AND_PRIVACY_FOUNDATION_V1_0.md), [Finance Authority Model](../governance/FINANCE_AUTHORITY_MODEL_V1_0.md), and [MVP Boundary](../product/MVP_BOUNDARY_V1_0.md). The complete document map is in the [architecture index](../README.md).

## 1. Freeze contract

Commerce OS remains the system of record. The frozen core retains eight domains: Intelligence, Decision, Build, Growth, Operations, Finance, Learning, and Governance. v1.1 adds contracts and bounded capabilities; it does not replace or create a competing architecture. Because no prior architecture is present in this checkout, “unchanged” below means required unchanged by the mission baseline, not verified against code. Evidence: [repository discovery](./REPOSITORY_DISCOVERY_AND_DRIFT.md).

External AI, messaging, advertising, and channel products are replaceable execution providers behind registries and adapters. Provider output is advisory or operational input; it never owns business state or authority.

## 2. Final domain map

| Domain | Unchanged responsibility | v1.1 additions or extensions | State owned |
|---|---|---|---|
| Intelligence | Evidence and insight | Customer Intelligence service, signal clustering, Customer 360 projection inputs, root-cause analysis | `CustomerSignal`, `SignalCluster`, `RootCauseCase` analysis state |
| Decision | Recommendations and decisions | Creative Strategy, Channel Strategy, Negotiation Copilot recommendations | `CreativeHypothesis`, `ChannelStrategy`, `ChannelRecommendation`; no financial authority |
| Build | Product/creative construction | Creative generation service, Creative Router, QA workflow | `CreativeAsset`, `CreativeDNA`, `ModelExecution`, `ModelPerformance` |
| Growth | Acquisition and conversion | B2C conversion workflow, channel execution including Pinterest | campaign/channel workflow state and `AttributionTouch` |
| Operations | Customer and fulfillment operations | Conversation Commerce orchestration, AI Support Agent, Human Handoff | `Conversation`, message metadata, `Handoff`; order remains with existing owner when identified |
| Finance | Financial truth and economics | CFO-linked creative/revenue economics, quote/refund/commitment checks | financial approvals and economics projections; ledger remains authoritative |
| Learning | Append-only observations and feedback | revenue learning, creative/model performance learning, cross-functional feedback | `learning.observation_recorded`; cannot overwrite Product Truth |
| Governance | Policy, permissions, approvals, audit | Approval Service, Commercial Policy, provider/channel registries, AI Operating Committee workflow | `CommercialPolicy`, approval decisions, authority policy, registry controls |

Shared foundation contracts are not a ninth domain. They are domain-neutral interfaces governed by Governance: event envelope, identity keys, authorization context, Approval Service interface, Experiment Registry, Model Provider Registry, and Channel Capability Registry.

## 3. Capability normalization

| Capability | Form | Primary domain | Boundary |
|---|---|---|---|
| Creative Strategy | SERVICE / ENGINE | Decision | Produces hypotheses and recommendations. |
| Image/short-video generation | SERVICE / ENGINE | Build | Produces versioned assets through provider adapters. |
| Multi-model Creative Router | SERVICE / ENGINE | Build | Selects providers by capability/policy; cannot approve spend or publication. |
| Channel Strategy | SERVICE / ENGINE | Decision | Produces channel recommendations. |
| Pinterest | SERVICE / ENGINE adapter | Growth | Replaceable channel adapter, not a domain or agent. |
| Conversation Commerce | WORKFLOW | Operations | Routes untrusted messages through deterministic policy and specialized services. |
| B2C conversion path | WORKFLOW | Growth | Consumer discovery-to-order path. |
| B2B conversion path | WORKFLOW | Operations | Lead-to-`SalesOpportunity`-to-quote path. |
| AI Sales Agent | AGENT | Operations | Goal-bounded conversation participant; no policy mutation or financial authority. |
| AI Support Agent | AGENT | Operations | Support interaction participant; refunds require approval. |
| Human Handoff | WORKFLOW | Operations | Durable transfer with reason, transcript pointer, SLA, owner, and completion. |
| Negotiation Copilot | SERVICE / ENGINE | Decision | Advises a human/agent inside `CommercialPolicy`; does not commit terms. |
| Customer Intelligence | SERVICE / ENGINE | Intelligence | Derives signals with provenance. |
| Identity Resolution | SERVICE / ENGINE | Governance | Links observations with provenance/confidence; does not erase source identities. |
| Customer 360 | SERVICE / ENGINE read model | Intelligence | Derived projection, never an independent source of truth. |
| Strategic Accounts | WORKFLOW | Operations | Coordinates B2B account actions and approvals. |
| Revenue learning | WORKFLOW | Learning | Records observations and performance outcomes. |
| Root-cause analysis | SERVICE / ENGINE + WORKFLOW | Intelligence | Proposes cases/actions; approval gates consequential action. |
| AI Operating Committee | WORKFLOW | Governance | Human-accountable review cadence, not an autonomous super-agent. |
| CFO-linked economics | POLICY / CONTROL | Finance | Deterministic constraints and approval linkage. |
| Cross-functional feedback | WORKFLOW | Learning | Event-driven observations across domains. |

Rejected interpretations: a ninth “Customer” or “Creative” domain; provider-owned business state; generic `Opportunity`; autonomous AI Operating Committee; LLM-controlled approvals; learning writes into Product Truth; Pinterest as an agent; Customer 360 as a master database.

## 4. Canonical object contracts

Objects are proposed pending schema reconciliation documented in [gap analysis](./ARCHITECTURE_GAP_ANALYSIS_V1_1.md).

- `VentureOpportunity`: market/business opportunity. Never used for a B2B deal.
- `SalesOpportunity`: B2B commercial deal linked to a `Lead`, identity/account, requirements, stage history, and policy context.
- `CustomerIdentity`: durable internal subject plus source identity observations, provenance, confidence, timestamps, and linkage status.
- `Conversation`: channel, participants, purpose/path (`B2C`, `B2B`, `SUPPORT`), state, policy version, and timestamps.
- Message metadata: immutable message ID, conversation, direction, channel/provider IDs, timestamps, content reference/hash, trust classification, delivery status, actor, and correlation fields. Sensitive content is stored separately under retention/access policy.
- `Lead`, `BuyerRequirementProfile`, `Quote`, `StrategicAccount`, `CustomerSignal`, `SignalCluster`, `RootCauseCase`, `CorrectiveAction`, `CreativeHypothesis`, `CreativeAsset`, `CreativeDNA`, `ModelExecution`, `ModelPerformance`, `ChannelStrategy`, `ChannelRecommendation`, `Handoff`, `CommercialPolicy`, and `AttributionTouch` use typed IDs, lifecycle state, version, provenance, and audit timestamps.

State must have exactly one write owner. Cross-domain consumers use APIs/events or projections, never direct foreign-domain mutation.

## 5. Flows

### B2C

Untrusted inbound message → identity observation/resolution → conversation policy classification → AI Sales/Support Agent → product/channel recommendation → deterministic commercial/authority policy → human approval where required → order through the existing authoritative order boundary → attribution → learning observation.

### B2B

Untrusted inbound/referral → identity and account resolution → `Lead` qualification → `SalesOpportunity` → `BuyerRequirementProfile` → Negotiation Copilot → `Quote` → approval when terms, spend, refund, or commitment require it → human send/authorized execution → strategic-account workflow → revenue learning.

The paths share identity, conversation, policy, approval, event, and learning foundations but never share an ambiguous opportunity type.

### Human handoff

Risk, low confidence, explicit request, policy trigger, negotiation boundary, or SLA trigger creates `Handoff`. Automation pauses for the scoped action; context is transferred by reference with minimum necessary data. Completion records human owner, disposition, and resumption policy.

## 6. Creative and channel architecture

Creative Strategy creates `CreativeHypothesis`. Generation creates `CreativeAsset` variants and `ModelExecution` records through Model Provider Registry adapters. Deterministic/curated QA gates precede `creative.approved`. Creative Router can rank providers using capability, data policy, cost, latency, and `ModelPerformance`; it cannot grant approval. `CreativeDNA` is a versioned derived representation, not Product Truth.

Channel Strategy consumes product truth, customer aggregates, creative evidence, economics, and the Channel Capability Registry to emit `ChannelRecommendation`. Pinterest is one adapter. Paid launch and every paid budget change require recorded human approval.

## 7. Customer intelligence and Customer 360

Identity Resolution stores every observed identifier with source, collection basis, confidence, match method, and linkage history. Conflicting matches remain reviewable and reversible. Customer Intelligence turns authorized observations into `CustomerSignal`; clustering creates `SignalCluster`. Customer 360 is a permission-filtered read model assembled from authoritative domains with field lineage, freshness, purpose limitation, and deletion/retention behavior.

No raw provider response is trusted. External messages cannot change prompts, tools, policies, permissions, routing rules, or approval state.

## 8. Finance and authority

Finance provides deterministic economics inputs and is the authority for financial truth. Creative/channel reporting links spend, attributed revenue, margin assumptions, and confidence without claiming causal certainty. In v1, human approval is mandatory for paid-ad launch, paid-ad budget change, monetary refund, and new incremental financial commitment. Zero-incremental-cost commercial actions require an approved, versioned `CommercialPolicy` and complete audit evidence.

LLM or provider output cannot override policy. Approval records bind subject/action, requester, approver, authority basis, policy version, before/after values, expiry, and idempotency key.

## 9. Event model

Business events are append-only facts. The envelope requires `event_id`, `event_type`, `occurred_at`, `actor`, `source`, `idempotency_key`, `correlation_id`, `causation_id`, and nullable typed `project_context`, `product_context`, and `customer_context`; it also carries schema version and payload reference/hash. Consumers are idempotent. Corrections append superseding/correction events.

Initial taxonomy:

`customer.identity_observed`, `customer.identity_linked`, `conversation.started`, `conversation.message_received`, `conversation.message_sent`, `conversation.handoff_requested`, `conversation.handoff_completed`, `lead.created`, `lead.qualified`, `sales_opportunity.created`, `sales_opportunity.stage_changed`, `quote.created`, `quote.approval_required`, `quote.sent`, `customer_signal.detected`, `signal_cluster.threshold_crossed`, `creative.hypothesis_created`, `creative.asset_generated`, `creative.qa_failed`, `creative.approved`, `creative.test_recommended`, `channel.recommendation_created`, `order.created`, `order.fulfilled`, `refund.requested`, `refund.approved`, `dispute.created`, `root_cause_case.created`, `corrective_action.proposed`, `corrective_action.approved`, `learning.observation_recorded`.

Event existence never grants command authority. Sensitive payloads use references, minimization, encryption, access controls, and retention rules rather than uncontrolled event-body duplication.

## 10. Security and provider boundaries

- Authenticate actors and services; authorize each command against tenant/project, role, purpose, policy version, and resource.
- Treat external content and provider output as untrusted; separate data from instructions and allowlist tools/actions.
- Minimize PII; encrypt in transit/at rest; segregate secrets; log access; support retention, legal basis/consent, export, correction, and deletion without rewriting immutable financial/audit facts.
- Provider adapters receive least-necessary data, declare residency/retention/training constraints, and return normalized results plus provenance.
- Registry policy supports provider disablement, fallback, version pinning, cost ceilings, and circuit breaking. No provider identifier is a canonical business ID.
- Permission checks occur at command and projection boundaries. Customer 360 never bypasses source-domain entitlements.

## 11. Learning and operating governance

Operational, revenue, creative, support, dispute, and fulfillment outcomes emit observations. Learning may recommend new hypotheses, policies, routing weights, or corrective actions, but changes follow versioning, experiment, approval, and rollback controls. Product Truth is read-only to learning.

The AI Operating Committee is a Governance workflow consuming dashboards and exception cases. Humans remain accountable for policy, risk acceptance, financial authority, provider use, and corrective actions. CEO Control Center is a permissioned read/command surface over existing owners, never a parallel source of truth.

## 12. Open decisions

Any prior external freeze, system schemas, concrete service boundaries, finance-ledger integrations, retention schedule/legal basis by jurisdiction, tenant model, named human role/threshold assignments, API conventions, and deployment topology are absent. Logical ownership and minimum governance rules are now defined, but these implementation inputs must be resolved before Sprint 001. Evidence: [repository discovery](./REPOSITORY_DISCOVERY_AND_DRIFT.md) and [governance index](../README.md).
