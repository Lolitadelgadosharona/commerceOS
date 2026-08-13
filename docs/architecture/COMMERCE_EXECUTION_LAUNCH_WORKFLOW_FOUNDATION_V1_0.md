# Commerce Execution and Launch Workflow Foundation v1.0

Sprint 033 composes this workflow from an approved MarketOpportunity investment review. The orchestration command creates only a draft launch and gap-derived work; Product Truth and launch approvals remain separate gates.

Status: Sprint 016 implementation contract

## Purpose and ownership

This foundation gives Commerce OS controlled visibility over product-launch work without performing commerce execution. Operations owns launch state, milestones, tasks, action plans, and blockers. Governance retains approval authority; Decision recommendations, Growth channel execution, and Finance economic truth remain outside this module.

## Product launch lifecycle

`ProductLaunch` scopes an approved Build product to an organization, project, market, and priority. Its lifecycle is:

```text
DRAFT -> APPROVED -> IN_PROGRESS -> COMPLETED
                    |           ^
                    v           |
                  BLOCKED ------+
```

Draft, approved, in-progress, or blocked launches may be cancelled only through allowed state transitions. Completed and cancelled launches are terminal.

Moving from draft to approved requires a Governance `ApprovalRequest` that:

- belongs to the same organization and project;
- is already approved through the Governance workflow;
- identifies the exact launch as `product_launch`;
- authorizes `approve_launch`.

The Operations API cannot create or decide this approval.

## Milestones and tasks

Milestones are ordered uniquely within each launch and support product approval, supplier readiness, listing readiness, creative readiness, channel readiness, and launch readiness. Their lifecycle is todo, in progress, blocked, then done.

Execution tasks use the same controlled work lifecycle. AI, human, and team owner types are labels for future routing and accountability. An `AI` owner label does not start an agent, grant approval authority, or execute the task.

## Action plans and blockers

`ActionPlan` records a dated, prioritized launch summary and its provenance for future CEO daily views. It is a plan record, not an executable command.

`ExecutionBlocker` records reason, severity, impact, and status. Creating a blocker while a launch is in progress moves that launch to blocked. Resolving a blocker does not automatically resume the launch; Operations must explicitly return the launch to in progress after verifying readiness.

## Authority and activation limits

- Every record and referenced entity is organization-scoped.
- No endpoint publishes, advertises, sends, purchases, or integrates externally.
- No task, plan, milestone, or blocker invokes automation.
- Recommendations and AI ownership labels provide no execution authority.
- Shopify, advertising, social platforms, publishing, LLMs, and agents are excluded.
- The existing authentication limitation continues to prohibit public deployment.
