# AI Operating Committee and CEO Control Dashboard Foundation v1.0

Status: Sprint 015 implementation contract

## Purpose

This foundation provides an operator with prioritized, cross-domain visibility over metrics, signals, risks, recommendations, and decisions requiring human attention. It is an executive projection and review layer, not an autonomous CEO, agent, or execution system.

## Ownership

- Decision owns executive metric snapshots, operating signals, and operating committee recommendations.
- Governance owns decision queue items and remains the sole authority boundary for approvals.
- Finance, Operations, Growth, Build, and Intelligence retain ownership of their source truth.
- Dashboard views compose authorized records without writing back to source domains.

## Executive metrics

`ExecutiveMetricSnapshot` records an organization, category, name, numeric value, unit, source domain, financial period, and timestamp. Categories are revenue, profit, customer, product, creative, channel, and risk. A snapshot is a time-bound projection; it cannot modify the source record it summarizes.

## Operating signals

`OperatingSignal` describes a cross-functional observation with information, warning, or critical severity. Its lifecycle is `OPEN`, `ACKNOWLEDGED`, then `RESOLVED`; direct reversal or reopening is prohibited. Recommendations are advisory text only.

## Decision queue

`DecisionQueueItem` is Governance-owned. It centralizes an operator prompt requiring approve, review, or reject consideration. Queue lifecycle changes only acknowledge or close the prompt. They do not approve, reject, or otherwise mutate a linked `ApprovalRequest`; approval decisions must use the existing Governance approval workflow.

## Operating committee reviews

`OperatingCommitteeReview` is a periodic, Decision-owned evidence summary containing findings, risks, recommendations, confidence, and financial-period scope. Reviews move from draft to reviewed to archived. They do not execute recommendations.

## Dashboard views

Strategic-account indicators are read-only counts of account profiles, key/watch states, replenishment assessments, expansion opportunities, and next-best actions. Estimated commercial potential is advisory and must not be presented as observed Finance truth.

Eight read-only views are exposed:

- Executive overview
- Need your decision
- Financial health
- Product opportunities
- Customer health
- Creative performance
- Channel performance
- Risk overview

Views filter stored, organization-scoped projections and never calculate or overwrite another domain's source truth. There is no dashboard execution endpoint.

## Authority and activation limits

- Every record and view is organization-scoped.
- A recommendation, signal acknowledgment, queue closure, or committee review grants no execution authority.
- Human approval cannot be inferred from a queue item or dashboard state.
- No LLM, agent, Shopify, advertising, social, or other external integration is present.
- The existing authentication limitation continues to prohibit public deployment.
