# Opportunity Intelligence Analysis Foundation v1.0

Status: Sprint 018 implementation contract

## Purpose and ownership

This foundation converts supplied market signals and evidence into structured, reproducible opportunity analysis records. Intelligence owns signal interpretation, deterministic assessments, and advisory reports. Decision retains opportunity recommendation ownership; Governance, Finance, and Operations retain approval, economic-truth, and execution ownership.

## Signal analysis

`MarketSignalAnalysis` attaches supplied interpretation to an existing, organization-scoped market signal. It records analysis type, market impact, timing, customer relevance, commercial relevance, and confidence. Confidence is bounded from 0 to 1. Text is provided by an authorized caller; no LLM or autonomous interpretation exists.

## Opportunity assessment

`OpportunityAssessment` requires an existing `MarketOpportunity` with at least one linked market signal. Five supplied scores are bounded from 0 to 100. V1 calculates:

```text
overall = demand * 25%
        + timing * 20%
        + evidence * 20%
        + (100 - risk) * 10%
        + commercial * 25%
```

A higher risk input reduces the result. The formula version and caller-supplied explanation are stored for reproducibility. Scores are advisory analysis and do not replace Finance economic truth.

## Opportunity reports

`OpportunityReport` requires an existing structured assessment. It stores supplied summary, evidence summary, recommended actions, risk summary, and a controlled draft-to-review-to-presented lifecycle. Recommended actions are advisory text, not autonomous recommendations or commands.

## Investment committee and decision queue

A report may be linked once to a Governance-owned decision queue item. The composition endpoint creates a `REVIEW` prompt for human attention and stores its identifier on the report. It does not create an `ApprovalRequest`, grant authority, change the opportunity, or execute an action. Closing the queue prompt remains distinct from approval.

## Authority and activation limits

- Every analysis, assessment, report, and relationship is organization-scoped.
- No opportunity is created automatically.
- No report changes source signals, evidence, opportunities, financial truth, or execution state.
- No LLM, AI agent, scraper, connector, external API, autonomous recommendation, approval, or execution is present.
- The existing authentication limitation continues to prohibit public deployment.
