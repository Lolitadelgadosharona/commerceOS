# Creative Asset Intelligence Foundation v1.0

Status: Sprint 027 implementation contract

## Purpose

This foundation records human-planned creative work without generating, publishing, or distributing content. It connects Decision-owned creative planning to a Build-owned artifact registry and accepts traceable performance observations for future analysis.

## Ownership and records

| Record | Owner | Contract |
|---|---|---|
| `CreativeBrief` | Decision | Defines product, strategy, audience, objective, message, required proof, call-to-action strategy, and planning confidence. |
| `CreativeAsset` | Build | Registers an artifact reference and descriptive metadata. New records begin `draft` with `pending` approval. |
| `CreativeAssetVersion` | Build | Appends a positive, sequential version number scoped to one asset, with a variation reason and experiment group. |
| `CreativePerformanceObservation` | Build | Stores a supplied decimal metric, source, period, and confidence; it is an observation, not Growth or Finance truth. |

The pre-existing creative brief contract is extended compatibly. `creative_strategy_id` is the public planning name while the stored `strategy_id` remains available to existing consumers. Legacy proof, CTA, and content-format fields remain readable during this compatibility period.

## Invariants

- Every record is organization-scoped, and every referenced product, strategy, or asset must belong to that organization.
- A brief's product must match its creative strategy's product.
- Brief and observation confidence values are bounded from zero through one.
- Asset version numbers begin at one, increase sequentially per asset, and are unique per asset.
- Performance metric values use fixed decimal precision; observations preserve source and period lineage.
- Asset creation cannot self-approve. Approval authority remains with Governance and is not exposed by these endpoints.

## API boundary

Sprint 027 exposes organization-scoped create and read contracts at:

- `/api/v1/creative-briefs`
- `/api/v1/creative-assets`
- `/api/v1/creative-versions`
- `/api/v1/creative-performance`

The API registers plans and records only. It has no publish, generate, distribute, advertise, or approval command.

## Explicit exclusions

This foundation does not store generated binary content, call image or video models, integrate with external providers, publish to a channel, execute advertising, create autonomous agents, or convert observations into financial truth. Those capabilities require separate architecture, authority, security, and economic review.
