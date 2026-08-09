# Backend Domain Ownership

The Python package follows [Module Boundary v1.0](../../docs/architecture/MODULE_BOUNDARY_V1_0.md).

| Package | Sprint 001 write-owned models |
|---|---|
| `commerce_os.governance` | `Organization`, `Project`, `CustomerIdentity`, `Approval`, `CommercialPolicy` |
| `commerce_os.decision` | `VentureOpportunity` |
| `commerce_os.operations` | `Brand`, `Store`, `Customer`, `SalesOpportunity`, `Conversation`, `MessageMetadata` |
| `commerce_os.shared` | Technical event envelope and outbox persistence only; no business aggregates |
| Other domain packages | Boundary placeholders only; no Sprint 001 business models |

No generic `Opportunity` model exists. Domain packages do not import other domain internals.
