# Live Revenue Experiment Support Foundation v1.0

Status: frozen for Sprint 066 Product Review

## Purpose

Sprint 066 turns the existing GrowthOS revenue workflow into a repeatable founder-operated daily
process. It coordinates existing prospect, evidence, Growth Gift, offer, conversation, Finance,
Learning, and AI Runtime records. It does not grant external execution authority.

## Ownership

- Growth owns daily revenue runs, founder action coordination, connector metadata, and delivery
  workflow state.
- Intelligence and Industry Intelligence continue to own evidence and analysis inputs.
- Sales Copilot provides advisory reply analysis only.
- Learning owns promoted learning observations.
- Finance remains the only source of paid revenue truth.
- Governance owns authentication, permissions, approval authority, and audit records.
- AI Runtime owns governed model requests and cost observations.

## Daily revenue run

A `DailyRevenueRun` is scoped to one organization and Revenue Experiment, date, industry, and
geography. Ranked prospects are stored separately with explicit evidence references. A prospect
must already be assigned to the experiment. A run cannot enter review without at least one
evidence-backed prospect and cannot execute outreach or create customer records.

Lifecycle:

`draft → ready_for_review → approved → completed`

`draft` or `ready_for_review` may instead become `rejected`.

## Founder action center

`FounderActionItem` provides one queue for prospect reviews, Gift approvals, reply analysis, offer
decisions, and delivery tasks. Every item references an existing tenant-owned source record.
Approve, reject, assign, and complete transitions are audited. Assignment requires an active human
user in the same organization. The queue coordinates work; it does not execute the referenced
action.

## External data connector boundary

`GrowthExternalDataConnector` is provider-neutral metadata for website, Google Business, social
profile, and email data preparation. It records collection mode, policy reference, external
credential reference, and non-secret configuration.

Allowed collection modes are human review, controlled import, and controlled connector. Secrets
must remain outside the database. `ready` means configuration has passed internal review; it does
not initiate crawling, bypass platform policy, send email, or call a provider.

## Customer delivery workflow

`CustomerServiceDelivery` references an accepted offer and may only be created after a
Finance-backed paid observation exists. `CustomerDeliveryItem` represents ordered checklist,
milestone, customer-feedback, or expansion-opportunity work. Delivery cannot complete while a
checklist or milestone remains incomplete. Feedback and expansion items require evidence before
completion.

These records track founder-managed delivery. They do not perform customer work, send messages,
collect payment, or modify Product Truth.

## Analytics

The read-only experiment projection reports reviewed prospects, approved Gifts, manually recorded
outreach and replies, positive reply signals, offers, paid customers, Finance revenue, and recorded
lost reasons. Missing Finance truth remains zero/unknown, and incompatible currencies are not
combined.

## Security and authority

All APIs use the existing authenticated `/api/v1` boundary, RBAC authorization, organization
scope, and Governance audit log. No endpoint autonomously discovers prospects, communicates with
customers, changes prices, approves finance, processes payments, or sells a service.
