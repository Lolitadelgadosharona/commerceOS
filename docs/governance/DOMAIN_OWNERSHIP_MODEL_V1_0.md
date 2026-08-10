# Commerce OS Domain Ownership Model v1.0

Status: logical ownership contract; deployment boundaries remain implementation decisions

## Ownership rules

Each aggregate has exactly one write-owning domain. Other domains read through authorized contracts, projections, or append-only events. Cross-domain workflows coordinate; they do not transfer ownership implicitly. Shared foundation contracts are governed by Governance and do not form a ninth domain. Human role assignments must be recorded separately from these logical system owners.

| Domain | Owns | May decide/write | Must not own or override | Publishes to |
|---|---|---|---|---|
| Intelligence | Evidence synthesis, customer signals/clusters, market opportunities, product hypotheses/economics/risks, root-cause cases, Customer 360 projection | Derived insights and deterministic scored observations with lineage/confidence | Venture/investment approval, Build Product/Product Truth, supplier selection/payment, ledger truth, approvals, execution state | Decision, Build, Finance, Learning, authorized dashboards |
| Decision | Venture, creative strategy/asset/router/economic planning, channel, negotiation, sales/support intelligence, executive projections, operating signals, and committee recommendations | Versioned recommendations, provider evaluations, supplied advisory classifications, executive snapshots, risk observations, and decision rationale | Model/generation execution, artifact ownership, distribution, financial or operational source truth, Product Truth, AI authority policy, approval authority | Build, Growth, Operations, Governance, Finance |
| Build | Approved products, append-only Product Truth, supporting product knowledge, brand claim guardrails, creative construction artifacts and model execution/performance | Governed product facts, Build lifecycle state, asset versions, QA state, generation execution | Governance approvals, Intelligence hypotheses, supplier/payment truth, paid/channel execution, ledger truth | Decision, Growth, Operations, Governance, Learning |
| Growth | Acquisition/channel workflow and attribution evidence | Governed channel workflow state and zero-cost delegated actions | Budget authority, revenue truth, customer master | Finance, Learning, Operations |
| Operations | Customer, supplier coordination, conversation threads/messages, supplied intent/emotion observations, human handoffs, B2B pipeline, orders/fulfillment workflow | Operational state under policy and references to trusted knowledge | Ledger entries, authority policy, Product Truth, identity resolution, automated reply authority | Finance, Intelligence, Build, Governance, Learning |
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
- `Approval` is owned by Governance; Finance defines financial approval requirements.
- `Experiment` is owned by Governance as a registry/control record; executing domains own treatment execution, and Learning owns outcome observations.

Entity details are in the [Data Ownership Contract](./DATA_OWNERSHIP_CONTRACT_V1_0.md).
