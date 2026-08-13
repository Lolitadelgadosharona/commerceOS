# Strategic Account Intelligence Foundation v1.0

Status: implemented advisory foundation; no customer outreach or commercial execution

## Purpose and ownership

Strategic Account Intelligence identifies accounts needing human attention without redefining customer or monetary truth. Operations owns persistent account profiles and supplied stakeholders. Intelligence owns replenishment assessments. Decision owns expansion opportunities, next-best-action recommendations, and strategic scores. Governance owns decision-queue review. Finance remains the only monetary source of truth.

Customer 360 remains a projection only. These records cannot update Customer 360 inputs, customer records, conversations, SalesOpportunity, orders, pricing, discounts, refunds, approvals, or Finance records.

## Contracts

`StrategicAccountProfile` records bounded relationship, commercial, expansion, replenishment, and risk indicators. Account status is candidate, active, watch, dormant, or closed; tier is standard, growth, strategic, or key. Order value alone never determines strategic status.

`AccountStakeholder` stores supplied tenant-scoped contact references, roles, influence, decision-maker status, relationship strength, and evidence. It neither duplicates CustomerIdentity nor creates, enriches, or contacts external people.

`ReplenishmentAssessment` calculates a purchase window only when a supplied last-purchase date and cycle exist. Probability is emitted only when relevant evidence and a frequency indicator exist; missing evidence remains null.

`CustomerExpansionOpportunity` is distinct from VentureOpportunity, MarketOpportunity, and SalesOpportunity. It cannot create a SalesOpportunity. Status is identified, review, ready, dismissed, or expired.

`CustomerNextBestAction` supports follow-up, replenishment check, product recommendation, cross-sell review, account review, human outreach, no action, and risk review recommendations. Every record is advisory. `NO_ACTION` is valid and never creates a decision-queue item.

## Strategic account score v1.0

All supplied inputs are bounded 0–100. Positive weights are contribution margin 14%, repeat probability 14%, purchase frequency 10%, LTV 10%, B2B potential 8%, expansion 10%, referral 6%, relationship 10%, strategic importance 8%. Penalties are payment risk 4%, refund risk 2.5%, dispute risk 2.5%, and operational burden 4%. The score is bounded 0–100. Missing inputs remain null; evidence coverage and confidence equal the proportion of the 13 inputs supplied. The formula does not substitute optimistic defaults and does not use order value alone.

## Governance and dashboard

Only high/critical, human-review-required actions other than `NO_ACTION` create a Governance-owned DecisionQueueItem. That item requests review and grants no approval or execution authority.

Existing dashboard views include read-only counts for strategic/key/watch accounts, replenishment assessments, expansion opportunities, and next-best actions. Estimated commercial potential is an indicator, never observed Finance truth.

## Explicit exclusions

No email, DM, quotation, pricing change, discount, order, refund, external API, contact enrichment, connector, LLM, agent, autonomous execution, or customer outreach is implemented.
