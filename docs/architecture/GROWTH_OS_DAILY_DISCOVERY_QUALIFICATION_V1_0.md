# Growth OS Daily Discovery and Qualification v1.0

## Purpose

This foundation converts a founder-supplied business category and geography into a bounded daily queue of public, evidence-backed prospect candidates. It does not create customers, approve outreach, or contact a business.

## Controlled workflow

1. The founder selects an industry, geography, optional filters, and a target of one to ten candidates.
2. GrowthOS creates or updates a tenant-scoped daily discovery plan and queues the first run.
3. The worker uses the governed AI Runtime with explicit public web search enabled for that request.
4. Each saved candidate requires a direct public source URL, observed evidence, timestamp, and confidence.
5. The governed discovery output recommends four qualification inputs, pain points, a filter-match explanation, and confidence. Each recommendation must be grounded in the returned public evidence; unsupported inputs remain null.
6. The deterministic formula withholds a score until all four inputs are present. Candidates are displayed in descending score order, and the founder can inspect or correct every input.
7. A score of at least 70 unlocks founder approval. Approval promotes the candidate and copies immutable discovery evidence into the formal prospect evidence store.
8. The prospect then enters the existing Growth Diagnosis, Before/After Growth Gift, approval, outreach draft, revision, and manual-send workflow.

## Candidate review UI

Each candidate has a tenant-scoped review route that shows:

- overall score and discovery confidence;
- the four deterministic score inputs;
- qualification rationale and missing inputs;
- observed pain points;
- every source URL, observation, evidence type, and evidence confidence;
- the founder approval boundary and downstream preparation state.

The UI never describes a candidate as approved until the founder performs the approval action. It also identifies email delivery as unavailable when no governed email connector is configured.

## Boundaries

- Each run saves at most ten candidates.
- Search is limited to publicly accessible sources and must not bypass platform controls.
- Duplicate businesses are suppressed within an organization.
- AI output is a candidate and evidence record, never an approval or execution instruction.
- Missing facts remain unknown. The AI may recommend a qualification input only when the public evidence supports it; otherwise the value is null.
- Growth Gift and outreach require the existing Governance workflow.
- Sending remains a founder-confirmed external action; GrowthOS only records the observed result.
- The AI provider's web-search usage and cost controls remain active.

## Qualification formula

The existing versioned formula remains authoritative:

- Growth pain: 35%
- Purchase probability: 30%
- Accessibility: 20%
- Quick-win potential: 15%

All values range from 0 to 100. A blank field produces no total score.

## Scheduling and failure behavior

The first run is queued immediately. The daily plan records its next due time and the worker queues one due plan at a time. Jobs use the existing durable outbox, bounded retries, service identity, tenant scope, cost controls, and visible failure state. A failed run creates no customer contact or downstream commercial record.
