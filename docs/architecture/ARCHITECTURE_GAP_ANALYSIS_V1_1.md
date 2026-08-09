# Architecture Gap Analysis — Freeze v1.1

Evidence note: no implementation or prior architecture exists in the checkout; therefore no equivalence can be proven. Every `NEW` item means new to the observable repository, while `MODIFIED` means an extension required by the mission’s frozen conceptual baseline. See [repository discovery](./REPOSITORY_DISCOVERY_AND_DRIFT.md) and the [v1.1 freeze](./ARCHITECTURE_FREEZE_V1_1.md).

Priority: P0 foundation, P1 first vertical foundations, P2 subsequent integration, P3 control-surface/reporting.

| Capability | Existing equivalent | Status | Domain | Dependencies | Migration risk | Security / authority implications | Priority |
|---|---|---|---|---|---|---|---|
| Eight-domain core | Not observable | UNCHANGED | All eight | Prior freeze import | High reconciliation | Domain authorization and state ownership | P0 |
| Append-only event envelope | None | NEW | Governance/shared | IDs, actor/auth context, schema registry | High if legacy events exist elsewhere | PII minimization, integrity, replay/idempotency | P0 |
| Approval Service extensions | None | MODIFIED | Governance | Authority matrix, CommercialPolicy, audit | High | Human financial authority; separation of duties | P0 |
| Commercial Policy | None | NEW | Governance | Approval, permissions, versioning | Medium | Deterministic policy must dominate LLM output | P0 |
| Model Provider Registry | None | NEW | Governance | secrets, provider adapters, policy | Low data / high operational | Data transfer, lock-in, cost ceilings | P0 |
| Channel Capability Registry | None | NEW | Governance | channel adapters, policy | Low | Paid-action permissions, credential isolation | P0 |
| Experiment Registry | None | NEW | Governance | event envelope, metrics | Medium | Prevent unauthorized exposure/spend | P0 |
| Identity Resolution | None | NEW | Governance | CustomerIdentity, consent/retention | High | Highly sensitive PII, false linkage, provenance | P0 |
| CustomerIdentity | None | NEW | Governance | identity observations, typed contexts | High | PII, confidence, reversible links | P0 |
| Conversation + message metadata | None | NEW | Operations | identity, events, channel registry | High | Untrusted input, transcript access/retention | P0 |
| Lead | None | NEW | Operations | identity, conversation | Medium | PII, qualification bias | P0 |
| SalesOpportunity | None | NEW | Operations | Lead, account, policy | High terminology | Must not collide with VentureOpportunity | P0 |
| VentureOpportunity | None observable | UNCHANGED | Intelligence/Decision | Prior product/opportunity owner | High reconciliation | Business confidentiality | P0 |
| Handoff | None | NEW | Operations | conversation, permissions, SLA | Medium | Minimum necessary context, human accountability | P0 |
| CustomerSignal / SignalCluster | None | NEW | Intelligence | identity, events, taxonomy | Medium | Profiling, inference, bias, retention | P0 |
| ModelPerformance | None | NEW | Build | model execution, experiment/event metrics | Medium | Sensitive prompts/outputs; evaluation integrity | P0 |
| Creative Strategy | None | NEW | Decision | Product Truth, experiments, economics | Low | IP/brand safety, no authority | P1 |
| Creative generation | None | NEW | Build | provider registry, asset store, QA | Medium | IP, safety, PII leakage, provider terms | P1 |
| Creative Router | None | NEW | Build | registry, performance, cost/policy | Medium | Provider lock-in and covert cost risk | P1 |
| Channel Strategy | None | NEW | Decision | channel registry, creative/economics | Medium | Recommendation explainability | P1 |
| Pinterest adapter | None | NEW | Growth | channel registry, credentials, approvals | Medium | Platform policy, paid launch controls | P2 |
| B2C conversion | None | NEW | Growth | conversation, product/order, policy | High | Consumer protection, consent, payments | P1 |
| B2B conversation commerce | None | NEW | Operations | lead, SalesOpportunity, quote, policy | High | Terms authority, confidentiality | P1 |
| AI Sales Agent | None | NEW | Operations | conversation, policy, handoff | High | Prompt injection, misrepresentation, commitments | P2 |
| AI Support Agent | None | NEW | Operations | conversation, order/support, handoff | High | Refund authority, sensitive account data | P2 |
| Negotiation Copilot | None | NEW | Decision | requirements, quote, policy | High | Unauthorized terms, competition/fairness concerns | P2 |
| Customer 360 read model | None | NEW | Intelligence | identity + source APIs/events | High | Aggregation risk, entitlement leakage, deletion | P2 |
| Strategic Accounts | None | NEW | Operations | SalesOpportunity, Customer 360, handoff | Medium | Confidentiality, account-level entitlements | P2 |
| Root cause / corrective action | None | NEW | Intelligence/Governance | signals, orders, disputes, learning | Medium | Incorrect causality, consequential actions | P2 |
| Revenue learning | None | MODIFIED | Learning | attribution, finance, experiments | High | Causal overclaim, Product Truth protection | P2 |
| AI Operating Committee | None | NEW | Governance | metrics, exceptions, approval records | Low | Must remain human-accountable | P3 |
| CEO Control Center | None | MODIFIED | Governance | all projections and command APIs | High | Privilege concentration, source-of-truth ambiguity | P3 |

## Cross-cutting findings

### Overlaps

- Customer 360 overlaps source-domain customer/order/finance views; resolve as a lineage-rich, permission-filtered projection only. Evidence: [v1.1 §7](./ARCHITECTURE_FREEZE_V1_1.md).
- Creative Strategy, Channel Strategy, and AI agents can all recommend actions; Decision owns recommendation semantics while operational workflows own execution. Evidence: [domain map](./ARCHITECTURE_FREEZE_V1_1.md).
- Root-cause analysis and revenue learning consume similar outcomes; Intelligence owns analysis cases, Learning owns append-only observations. Evidence: [v1.1 §11](./ARCHITECTURE_FREEZE_V1_1.md).
- Approval Service and Commercial Policy overlap at gates; policy evaluates, approval records authorized human decisions. Evidence: [v1.1 §8](./ARCHITECTURE_FREEZE_V1_1.md).

### Conflicts and terminology collisions

- Generic `Opportunity` would conflate market exploration and B2B deals. It is rejected in favor of `VentureOpportunity` and `SalesOpportunity`.
- “AI Operating Committee” could imply autonomous authority; normalized to a human-accountable workflow.
- “Customer 360” could imply a master database; constrained to a read model.
- “Agent” could absorb routing, strategy, or policy; only Sales and Support are agents, with the rest normalized to services, policies, or workflows.

### Missing dependencies

Prior architecture/Constitution/PRD; Product Truth and order contracts; canonical IDs and tenant/project model; financial ledger/budget/attribution contracts; authority matrix; consent, retention and deletion policy; content/asset storage; secrets/KMS; schema registry; observability; API conventions; provider/channel credential lifecycle; legal/compliance rules; deployment topology. Evidence: [discovery matrix](./REPOSITORY_DISCOVERY_AND_DRIFT.md).

### Circular-dependency controls

- Learning → Decision → execution → Learning is a feedback cycle, not a synchronous module cycle: events carry outcomes; proposed changes require experiment/policy/approval.
- Customer Intelligence → Conversation personalization → new signals is event-driven; Conversation may query a projection but cannot write Intelligence state.
- Finance → Channel/Creative recommendation → attribution → Finance is split: Finance publishes authoritative economics; attribution submits evidence and cannot mutate ledger truth.
- Customer 360 consumes source events and must not become a command path back into those sources.

### State ownership ambiguity

Order, Product Truth, customer master, financial ledger, campaign, and account ownership cannot be assigned from this checkout. Sprint 001 must establish ownership records before schemas are created. Evidence: [repository discovery](./REPOSITORY_DISCOVERY_AND_DRIFT.md).

### Principal risks

- **Provider lock-in:** provider-specific IDs/capabilities leaking into domain contracts; mitigate normalized adapters, portable asset storage, exit tests, registry-driven routing.
- **Security:** prompt injection, data exfiltration, unsafe generated content, secret leakage, event poisoning; mitigate trust boundaries, tool allowlists, least privilege, content scanning, signed/validated events.
- **Permission:** cross-tenant/customer leakage and projection bypass; authorize commands and reads at source and projection.
- **Financial authority:** implied commitment through ads, quotes, negotiations, or refunds; enforce deterministic gates and human approval records.
- **PII/privacy:** identity linkage and Customer 360 magnify re-identification/profiling risk; retain provenance/confidence, minimize fields, enforce purpose/retention/access/deletion.

## Readiness conclusion

The architecture is internally coherent as a proposed contract, but implementation is not ready because repository equivalence, ownership, and prior-freeze reconciliation are impossible with the current empty checkout. Evidence: [drift report](./REPOSITORY_DISCOVERY_AND_DRIFT.md).
