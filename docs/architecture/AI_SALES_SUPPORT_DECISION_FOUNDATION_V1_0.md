# AI Sales and Support Decision Foundation v1.0

Status: frozen Sprint 012 implementation contract

## Purpose and ownership

Decision owns sales profiles, sales recommendations, support-case intelligence, and customer-risk observations as advisory records. Operations remains authoritative for customers, conversation state, handoff, support execution, messaging, and orders. Governance owns AI action policy, permissions, and approvals. Build owns Product Truth. Finance owns monetary truth and financial execution.

No Sprint 012 record sends a message, responds to a customer, changes a price, creates a discount, issues a refund, makes a payment, or invokes an AI provider.

## Sales intelligence profiles

A sales profile is an organization-scoped, point-in-time advisory aggregation linking a Customer to its ConversationThread and optional Product. Profile creation validates that the conversation belongs to the supplied customer and organization and that the selected intent exists as an explicit ConversationIntent observation on that thread.

Estimated value and repeat probability are estimates, retain optionality, and are not Revenue, Transaction, Order, or other Finance/Operations truth. Repeat probability is constrained to 0–1. Risk level is an advisory classification.

## Sales recommendations

Recommendations record a type, evidence-based reason, confidence, and controlled lifecycle. Types are product recommendation, objection handling, follow-up, qualification, and escalation. The lifecycle is `draft -> reviewed -> accepted` or rejection. Acceptance means a human or governed workflow accepted the advice; it does not execute it.

## Support intelligence and customer risk

Support intelligence records supplied issue classification, severity, customer impact, risk, and a recommended resolution. It does not resolve a case. Customer risk signals record refund, dispute, churn, or fraud risk with an evidence reference. They are observations, not proof and not authority for adverse action.

No classification or recommendation is generated automatically. The API persists supplied decision-support inputs only.

## AI action policy

`AIActionPolicy` is Governance-owned and organization-scoped. It describes future behavior; it is not an executor. Initial safe defaults are:

| Action | Allowed by default | Approval required | Boundary |
|---|---:|---:|---|
| Recommend | Yes | No | Advisory only |
| Classify | Yes | No | Provenance-bearing observation only |
| Draft response | No | Yes | No generation exists in Sprint 012 |
| Send message | No | Yes | Operations execution absent |
| Issue refund | No | Yes | Finance/Operations execution absent |
| Change price | No | Yes | Build/Finance execution absent |
| Create discount | No | Yes | Finance/Growth execution absent |

The contract rejects any non-advisory policy that removes the approval requirement. `allowed=false` remains the default for every action except recommend and classify. Even an allowed future action remains subject to authentication, authorization, domain policy, approval, audit, and executor controls not implemented here.

## Tenant and security boundaries

Every record is scoped to an organization. Cross-organization customer, conversation, product, profile, and policy references are rejected. Evidence references must not contain secrets or unnecessary PII. Existing authentication limitations continue to prohibit public deployment.

Explicitly excluded: LLMs, agents, automated classification, automatic replies, customer-facing AI, external messaging, external integrations, refund/discount/payment automation, and autonomous financial or commercial action.
