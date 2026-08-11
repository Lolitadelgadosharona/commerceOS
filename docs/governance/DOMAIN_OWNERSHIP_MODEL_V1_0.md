# Commerce OS Domain Ownership Model v1.0

Status: logical ownership contract; deployment boundaries remain implementation decisions

## Ownership rules

Each aggregate has exactly one write-owning domain. Other domains read through authorized contracts, projections, or append-only events. Cross-domain workflows coordinate; they do not transfer ownership implicitly. Shared foundation contracts are governed by Governance and do not form a ninth domain. Human role assignments must be recorded separately from these logical system owners.

| Domain | Owns | May decide/write | Must not own or override | Publishes to |
|---|---|---|---|---|
| Intelligence | Evidence synthesis, customer and market signals/clusters, connector definitions, raw/normalized market data, ingestion state, signal interpretation, opportunity assessments/reports, market opportunities, product hypotheses/economics/risks, root-cause cases, Customer 360 projection | Connector and source metadata, supplied raw data/evidence/interpretation, deterministic normalization and assessments, advisory reports, evidence-only opportunity links, and scored observations with lineage/confidence | Live connector execution, autonomous research/recommendations, Venture/investment approval, Build Product/Product Truth, supplier selection/payment, ledger truth, approvals, execution state | Decision, Build, Finance, Governance, Learning, authorized dashboards |
| Decision | Venture, creative strategy/asset/router/economic planning, channel, negotiation, sales/support intelligence, executive projections, operating signals, and committee recommendations | Versioned recommendations, provider evaluations, supplied advisory classifications, executive snapshots, risk observations, and decision rationale | Model/generation execution, artifact ownership, distribution, financial or operational source truth, Product Truth, AI authority policy, approval authority | Build, Growth, Operations, Governance, Finance |
| Build | Approved products, append-only Product Truth, supporting product knowledge, brand claim guardrails, creative construction artifacts and model execution/performance | Governed product facts, Build lifecycle state, asset versions, QA state, generation execution | Governance approvals, Intelligence hypotheses, supplier/payment truth, paid/channel execution, ledger truth | Decision, Growth, Operations, Governance, Learning |
| Growth | Acquisition/channel workflow and attribution evidence | Governed channel workflow state and zero-cost delegated actions | Budget authority, revenue truth, customer master | Finance, Learning, Operations |
| Operations | Customer, supplier coordination, conversation threads/messages, supplied intent/emotion observations, human handoffs, launch workflows, execution tasks/blockers, B2B pipeline, orders/fulfillment workflow | Operational and launch state under policy and references to trusted knowledge | Ledger entries, authority policy, Product Truth, identity resolution, publishing, channel execution, automated reply or task execution authority | Finance, Intelligence, Build, Governance, Growth, Learning |
| Finance | Transactions, expenses, revenue/cost observations, financial periods, contribution profit, unit economics, and financial risk | Financial truth, deterministic economic assessments, reconciliation, controls and approval requirements | Operational/marketing execution, recommendations, AI policy exceptions, or money movement without authority | Decision, Growth, Governance, dashboards |
| Learning | Immutable observations, experiment outcome synthesis, learning proposals | `LearningRecord` and recommendations for change | Product Truth, policies, production configuration, approvals | All domains through governed proposals |
| Governance | Identity/permissions, policy, approval records, audit/event standards, registries | Authority policy, approvals, access, compliance controls | Domain business truth, owner intent, ledger truth | Every command and projection boundary |

## Cross-domain dispute rule

The write owner resolves data-state conflicts; Governance resolves authority/compliance conflicts; Finance resolves financial classification and commitment conflicts; the authenticated owner resolves policy exceptions within law and contract. Corrections append evidence and preserve prior audit history.

## Key boundary decisions

- `VentureOpportunity` is owned by Decision; Intelligence supplies evidence.
- `MarketOpportunity` is an Intelligence observation and must not be treated as a `VentureOpportunity`, investment approval, `SalesOpportunity`, or product commitment.
- `ProductHypothesis`, its economics, supplier references, risks, and score are Intelligence evidence. They must not be treated as a Build `Product`, Product Truth, supplier selection, procurement commitment, or investment approval.
- `SalesOpportunity` is owned by Operations; Decision may advise negotiation.
- `Product` and `ProductTruth` are owned by Build, with Product Truth publication requiring Governance-controlled authority. Learning cannot write either.
- `Order` is owned by Operations; `Transaction`, `Expense`, and `Revenue` are owned by Finance.
- Conversation records are owned by Operations; they may reference but never overwrite Governance identity/authority or Build Product Truth. AI sender classification grants no execution authority.
- AI action policy is owned by Governance. Decision may consume it but cannot weaken approval requirements or convert accepted advice into execution.
- Creative provider registry and routing records are Decision-owned evaluations only; Build owns future artifacts and provider execution, Growth owns distribution, and Finance owns actual economics.
- Financial observations, contribution-profit assessments, unit economics, and financial risk signals are Finance-owned. `CFOInsight` is Decision-owned because it contains recommendations; it cannot modify financial truth or authorize execution.
- Executive metrics, operating signals, and operating committee reviews are Decision-owned projections. Decision queue items are Governance-owned prompts; their state never substitutes for an approval decision or modifies source-domain truth.
- Product launches, milestones, tasks, action plans, and blockers are Operations-owned execution state. Launch approval requires a matching approved Governance request; AI task ownership is a routing label and grants no execution authority.
- Market source registrations, supplied market signals/evidence, clusters, and signal-opportunity links are Intelligence-owned. A link supplies evidence to an existing MarketOpportunity and cannot create, qualify, recommend, approve, or execute one.
- Signal analyses, deterministic opportunity assessments, and opportunity reports are Intelligence-owned advisory records. Report links create Governance review prompts only and cannot create recommendations, approvals, opportunity state changes, or execution.
- Connector definitions, raw market records, normalized items, and ingestion jobs are Intelligence-owned contracts and state. They do not execute connectors, create signals or opportunities, or store credentials.
- The read-only Reddit adapter is Intelligence-owned and may ingest configured posts/comments into raw records and deterministic pain evidence. It cannot post, reply, contact users, recommend opportunities, or execute actions.
- Customer pain clusters, cluster memberships, customer-language insights, and purchase-intent signals are Intelligence-owned evidence assets. Downstream domains may consume them but cannot treat them as Product Truth, opportunity approval, customer consent, or execution authority.
- Customer needs, pain mappings, product solution hypotheses, and customer-backed opportunity assessments are Intelligence evidence. They cannot create or approve opportunities, become Build Product Truth, override Finance economics, select suppliers, or execute commerce.
- Product commercial risk signals, risk assessments, and viability assessments are Intelligence evidence. Their `GO`, `TEST`, `REVIEW`, and `REJECT` labels are advisory and cannot modify Product Truth, financial truth, approvals, supplier state, or execution state.
- `Approval` is owned by Governance; Finance defines financial approval requirements.
- `Experiment` is owned by Governance as a registry/control record; executing domains own treatment execution, and Learning owns outcome observations.

Entity details are in the [Data Ownership Contract](./DATA_OWNERSHIP_CONTRACT_V1_0.md).
