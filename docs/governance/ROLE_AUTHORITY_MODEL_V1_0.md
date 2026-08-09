# Commerce OS Role Authority Model v1.0

Status: abstract role model; no personal assignments or numeric thresholds

## Rules

Roles are organization-scoped grants, not job titles or identities. A person may hold multiple roles only when separation-of-duties policy permits. Authentication proves identity; authorization evaluates role, organization/project/resource, action, purpose, amount/threshold, policy version, and time. Absence of an explicit grant is denial. AI and service accounts never hold human approver roles.

| Role | Permitted authority | Prohibited authority | Typical approvals |
|---|---|---|---|
| `Owner` | Establish mission, risk appetite, policies, role assignments, provider use, budgets, product truth authority, and exceptions within law; approve any action within recorded legal/entity authority | Cannot bypass law, contractual duties, mandatory audit, or separation-of-duties controls; cannot erase audit history | Final escalation, new commitments, policy exceptions, role/threshold changes |
| `Finance Approver` | Review and approve financial actions within assigned entity, category, amount, and time limits; view required economics and receipts | Cannot approve own request where separation is required; cannot change operational/product facts or expand own limits | Refunds, supplier payments, advertising budget changes, pricing/discount exceptions with financial impact |
| `Operations Approver` | Approve operational exceptions, fulfillment/customer remedies, supplier operational changes, and handoff resolution within policy | Cannot authorize monetary execution alone when Finance approval is required; cannot modify financial truth or compliance rules | Fulfillment exception, non-monetary remedy, supplier operational commitment, customer escalation |
| `Growth Approver` | Approve campaign/creative/channel operational actions within a pre-approved financial envelope and brand/compliance policy | Cannot create/increase/decrease/reallocate paid budgets in v1 without required Owner/Finance approval; cannot approve deceptive claims or Product Truth changes | Creative publication, audience/channel selection, experiment treatment, zero-cost channel action |
| `Compliance Approver` | Approve or reject regulated claims, data purposes, provider data use, retention exceptions, high-risk identity handling, and compliance remediation | Cannot authorize unlawful action or substitute for Finance/Owner approval; cannot write business/financial truth | Sensitive-data use, regulated content, retention/legal hold, provider transfer, compliance exception where legally permissible |

## Approval composition

| Action class | Minimum v1 role composition |
|---|---|
| Monetary refund | Finance Approver or Owner within recorded limits; Operations may recommend |
| Paid advertising launch or any budget change | Growth Approver for content/channel plus Finance Approver or Owner for spend; Owner where policy requires |
| Supplier payment | Finance Approver or Owner; changed payee/bank details require independently verified Operations/Compliance control |
| Custom commercial commitment | Operations Approver plus Finance Approver when cost/financial exposure exists; Owner for policy exception; Compliance when legal/regulatory risk exists |
| Pricing/discount exception | Finance Approver or Owner; Growth/Operations may recommend according to path |
| Product Truth publication/change | Owner-designated product authority plus Compliance Approver for regulated/sensitive claims |
| Identity high-risk merge or cross-scope link | Compliance Approver or specifically delegated identity reviewer; never AI-only |
| Role, authority threshold, or policy change | Owner; Compliance review when control/privacy scope changes |

## Delegation and emergency control

Delegation records the grantor, grantee role, organization/project scope, action classes, maximum amount where relevant, start/expiry, purpose, and revocation. Delegation cannot exceed the grantor’s authority. Emergency stop authority may pause automation or access to prevent harm; it cannot initiate spend, approve a pending action, or conceal evidence.

Before production, named accountable humans and numeric thresholds must be configured outside this document and tested against the [Finance Authority Model](./FINANCE_AUTHORITY_MODEL_V1_0.md).
