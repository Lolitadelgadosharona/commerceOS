# Growth OS Daily Discovery and Qualification v1.0

## Purpose

This foundation converts a founder-supplied business category and geography into a bounded daily queue of public, evidence-backed prospect candidates. It does not create customers, approve outreach, or contact a business.

## Controlled workflow

1. The founder selects an industry, geography, optional filters, and a target of one to ten candidates.
2. GrowthOS creates or updates a tenant-scoped daily discovery plan and queues the first run.
3. The worker uses the governed AI Runtime with explicit public web search enabled for that request.
4. Each saved candidate requires a direct public source URL, observed evidence, timestamp, and confidence.
5. The founder reviews evidence and supplies only supported qualification inputs.
6. The deterministic formula withholds a score until all four inputs are present. A score of at least 70 unlocks activation.
7. Activation enters the existing Growth Diagnosis, Growth Gift, approval, outreach draft, and manual-send workflow.

## Boundaries

- Each run saves at most ten candidates.
- Search is limited to publicly accessible sources and must not bypass platform controls.
- Duplicate businesses are suppressed within an organization.
- AI output is a candidate and evidence record, never an approval or execution instruction.
- Missing facts remain unknown. The AI does not fabricate qualification inputs.
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
