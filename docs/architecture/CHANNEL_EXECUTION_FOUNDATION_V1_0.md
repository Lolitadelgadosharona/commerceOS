# Channel Execution and Creative Distribution Foundation v1.0

Status: Sprint 030 implementation contract

## Purpose

This foundation creates the Growth-owned workflow between approved creative records and future channel operations. It stores execution plans, experiment designs, distribution state, and performance observations only. It cannot publish, buy media, call an external channel, create a campaign, or modify Build, Governance, or Finance truth.

## Ownership

| Record | Owner | Boundary |
|---|---|---|
| `ChannelExecutionPlan` | Growth | References an existing Build asset and records channel intent; it cannot create an asset or spend money. |
| `CreativeChannelExperiment` | Growth | Stores hypotheses, existing asset-version references, success metrics, and test notes; it cannot start a campaign. |
| `DistributionRecord` | Growth | Records a controlled distribution lifecycle and supplied reference; it performs no publishing. |
| `ChannelPerformanceObservation` | Growth | Stores traceable channel metrics; Finance remains the source of truth for spend, revenue, and profitability. |

Decision retains channel recommendations and hypotheses. Build retains creative assets and versions. Governance retains approval authority. Finance retains monetary truth.

## Lifecycle and approval rules

Channel execution plans move from `draft` to `ready`, then require a matching approved Governance request before `approved`. Approved plans may become `active`, `paused`, `completed`, or `cancelled`, but these labels represent internal workflow state only.

Distribution records move from `draft` to `ready`. The `approved` transition requires a matching approved Governance request for the same record and organization. A record cannot become `published` unless that approval remains valid and a supplied reference is recorded. The transition never contacts a channel.

Experiments move from `draft` to `ready`, then to `completed` or `cancelled`. Every creative variant must be an existing version of the plan's creative asset.

## Tenant and data boundaries

- Plans validate organization-scoped project, creative asset, and creator references.
- Experiments, variants, distributions, and observations validate all referenced records within the same organization.
- Growth services import neither Product Truth mutation services nor Finance mutation services.
- Performance metrics use fixed decimal precision and preserve channel, asset, experiment, source, and observation time.
- Contribution-profit metrics are observations only and never create revenue, expense, transaction, or profitability truth.

## API contract

The `/api/v1` API exposes:

- `POST`, `GET`, and `PATCH /channel-execution-plans`; `GET /channel-execution-plans/{id}`
- `POST`, `GET`, and `PATCH /channel-experiments`; `GET /channel-experiments/{id}`
- `POST`, `GET`, and `PATCH /distribution-records`; `GET /distribution-records/{id}`
- `POST` and `GET /channel-performance`; `GET /channel-performance/{id}`

No delete, publish, schedule-on-channel, campaign, budget, spend, or external integration endpoint is included.

## Explicit exclusions

No ads, media buying, actual publishing, social posting, Shopify, TikTok, Meta, Pinterest, external API, campaign execution, provider credential, autonomous agent, actual spend, revenue mutation, or Product Truth mutation is included.
