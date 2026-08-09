# Commerce OS Domain Ownership Model v1.0

Status: logical ownership contract; deployment boundaries remain implementation decisions

## Ownership rules

Each aggregate has exactly one write-owning domain. Other domains read through authorized contracts, projections, or append-only events. Cross-domain workflows coordinate; they do not transfer ownership implicitly. Shared foundation contracts are governed by Governance and do not form a ninth domain. Human role assignments must be recorded separately from these logical system owners.

| Domain | Owns | May decide/write | Must not own or override | Publishes to |
|---|---|---|---|---|
| Intelligence | Evidence synthesis, customer signals/clusters, root-cause cases, Customer 360 projection | Derived insights with lineage/confidence | Product Truth, ledger truth, approvals, execution state | Decision, Learning, authorized dashboards |
| Decision | Venture, creative, channel, and negotiation recommendations | Versioned recommendations and decision rationale | Execution, financial commitment, approval authority | Build, Growth, Operations, Governance |
| Build | Product/creative construction artifacts and model execution/performance | Asset versions, QA state, generation execution | Product Truth publication, paid launch, business approval | Growth, Decision, Learning |
| Growth | Acquisition/channel workflow and attribution evidence | Governed channel workflow state and zero-cost delegated actions | Budget authority, revenue truth, customer master | Finance, Learning, Operations |
| Operations | Customer, supplier coordination, conversations, B2B pipeline, orders/fulfillment workflow, handoff | Operational state under policy | Ledger entries, authority policy, Product Truth | Finance, Intelligence, Learning |
| Finance | Transactions, expenses, revenue classification, financial economics | Financial truth, reconciliation, controls and approval requirements | Operational/marketing execution, AI policy exceptions | Decision, Growth, Governance, dashboards |
| Learning | Immutable observations, experiment outcome synthesis, learning proposals | `LearningRecord` and recommendations for change | Product Truth, policies, production configuration, approvals | All domains through governed proposals |
| Governance | Identity/permissions, policy, approval records, audit/event standards, registries | Authority policy, approvals, access, compliance controls | Domain business truth, owner intent, ledger truth | Every command and projection boundary |

## Cross-domain dispute rule

The write owner resolves data-state conflicts; Governance resolves authority/compliance conflicts; Finance resolves financial classification and commitment conflicts; the authenticated owner resolves policy exceptions within law and contract. Corrections append evidence and preserve prior audit history.

## Key boundary decisions

- `VentureOpportunity` is owned by Decision; Intelligence supplies evidence.
- `SalesOpportunity` is owned by Operations; Decision may advise negotiation.
- `Product` and `ProductTruth` are owned by Build, with Product Truth publication requiring Governance-controlled authority. Learning cannot write either.
- `Order` is owned by Operations; `Transaction`, `Expense`, and `Revenue` are owned by Finance.
- `Approval` is owned by Governance; Finance defines financial approval requirements.
- `Experiment` is owned by Governance as a registry/control record; executing domains own treatment execution, and Learning owns outcome observations.

Entity details are in the [Data Ownership Contract](./DATA_OWNERSHIP_CONTRACT_V1_0.md).
