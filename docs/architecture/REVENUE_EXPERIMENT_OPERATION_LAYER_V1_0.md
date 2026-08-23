# Revenue Experiment Operation Layer v1.0

Status: frozen for Sprint 065 Product Review

## Purpose

This layer makes existing GrowthOS revenue experiments practical for daily founder operation. It
adds no new intelligence engine and grants no external execution authority.

## Daily Experiment Workspace

Each tenant- and date-scoped workspace item joins an existing Revenue Experiment assignment to a
Prospect and optional Daily Opportunity, Growth Diagnosis, Growth Gift, and Offer Recommendation.
Priority is supplied or reused from existing deterministic scoring; missing priority stays null.

The founder may approve, reject, or save for later. Every action records the human actor, notes,
result, and audit event. Workspace approval means “approved for the next human operating step”; it
does not approve external communication, payment, discounts, or delivery.

## Email workflow references

Append-only Email Workflow records store external account, draft, thread, and inbound-reply
references. At least one message reference is required. They store no password, token, API key,
cookie, authorization value, message-sending capability, or impersonation authority. Creating a
reference never sends or follows up on an email.

## Customer feedback and Learning Loop

Customer Feedback stores the observed response, interest, objection, won/lost reason, proposed
learning signal, confidence, Prospect, and Revenue Experiment. The lifecycle is:

Draft → Reviewed → Approved or Rejected.

Only a human-approved record creates an immutable `LearningObservation` through the existing
Closed-Loop Learning service. The observation cites the feedback record and does not modify
Prospect, Finance, Sales Copilot, or experiment truth.

## Revenue Experiment Operations Dashboard

The read-only dashboard combines experiment assignments and existing source records:

- assigned and qualified Prospects;
- Growth Gifts;
- manually sent Outreach and received replies;
- positive Sales Copilot observations;
- tracked Offers and Finance-backed paid customers;
- Finance Revenue Observations;
- governed AI Runtime cost observations explicitly linked to the experiment.

Revenue and AI cost are aggregated only when their respective observations use one currency.
Unknown or mixed-currency results remain zero with no currency rather than being fabricated.

## Authority and non-goals

Authentication, RBAC, tenant isolation, and audit logging apply to all endpoints. GrowthOS owns the
workspace and feedback workflow; Finance owns revenue; Learning owns observations; AI Runtime owns
cost observations. This layer performs no autonomous outreach, follow-up, selling, negotiation,
payment, or SaaS operation.
