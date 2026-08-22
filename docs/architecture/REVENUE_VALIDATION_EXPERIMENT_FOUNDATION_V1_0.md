# Revenue Validation Experiment Foundation v1.0

Status: frozen for Sprint 060 Product Review

## Purpose

The Revenue Validation Experiment Foundation moves GrowthOS from capability assembly to measured,
human-governed market validation. The first profile is `Beauty Growth Experiment #001`, targeting
independent lash, brow, facial, and small salon businesses. The contracts remain industry-neutral.

The system records what humans reviewed and did; it does not discover prospects externally, send
messages, negotiate, collect payment, or manufacture outcomes.

## Revenue experiment lifecycle

`RevenueExperiment` carries an optional Industry Profile, explicit segment, target count, start
date, and success-metric targets. Its lifecycle is:

`draft → active ⇄ paused → completed`

Completed experiments cannot resume. Existing archival support remains available for retention.
Prospects enter an experiment only after qualification, and each assignment preserves its tested
offer and message.

## Offer experiments

`OfferExperiment` represents a testable offer hypothesis for one prospect segment. Initial governed
types are Growth Visibility Audit, GEO Optimization, Website Growth Fix, and AI Content Growth.
`OfferExperimentOutcome` records sent, replied, positive-reply, and converted observations for a
prospect. It never sends outreach and cannot record positive or converted outcomes without a reply.

Response and conversion rates are calculated from recorded outcomes. Revenue is included only when
an outcome cites a tenant-scoped Finance `RevenueObservation`; Growth cannot assert revenue itself.

## Feedback learning

`ExperimentFeedbackSignal` captures reviewed replies, objections, questions, buying reasons, and
rejections. It records source traceability, frequency, industry context, a recommended response,
and an explicit learning statement. It can link to the existing Industry Learning Signal, keeping
Industry Intelligence, Sales Copilot, and offer recommendations on the established Learning Loop.
It does not change source conversations or Product Truth.

## Discovery source preparation

The existing Prospect Discovery Source contract now accepts Website, Google Business Profile,
Reviews, Instagram, TikTok, and Reddit source identities. These are metadata contracts only. Sprint
060 adds no crawling, provider credentials, network calls, or autonomous discovery.

## Revenue analytics and AI cost

The read-only experiment dashboard presents:

Prospects → Qualified → Gift Ready → Outreach Approved → Sent → Replies → Positive Replies →
Customers → Finance Revenue.

Stage conversion rates remain null when the preceding stage has no observations. Offer rates and
revenue use recorded outcomes only. Estimated AI cost is the sum of AI Runtime cost observations
whose request context explicitly references the experiment. Multiple currencies are never mixed;
an ambiguous monetary aggregate is withheld.

Existing provider-neutral model routing remains controlling: discovery and classification favor a
low-cost policy, while opportunity analysis and customer-reply drafting may require higher quality.
Sprint 060 does not call a provider.

## Authority boundary

- Growth owns experiments, offer observations, and workflow projections.
- Finance owns revenue truth.
- Governance owns approval and communication authority.
- Industry Intelligence and the existing Learning Loop own reusable learning.
- AI may analyze, classify, recommend, and draft; it cannot communicate or execute.
- Authentication, RBAC, tenant isolation, evidence ownership, and audit logging remain mandatory.

