# Creative Generation Workflow Foundation v1.0

Status: Sprint 028 implementation contract

## Purpose

This foundation records provider-neutral requests, capabilities, planned jobs, and human quality reviews for future creative generation. It deliberately contains no provider adapter, network client, model invocation, artifact generation, publishing, or advertising execution.

## Ownership

| Record | Owner | Boundary |
|---|---|---|
| `CreativeGenerationRequest` | Build | References a Decision-owned brief and records requested intent and parameters. |
| `CreativeProviderCapability` | Build | Describes an organization-scoped provider contract without credentials or executable integration code. |
| `CreativeGenerationJob` | Build | Records a pending provider-neutral work item and cost estimate; it cannot invoke a provider. |
| `CreativeQualityReview` | Build | Records a supplied review of an existing creative asset; its recommendation is advisory. |

Decision retains creative recommendations. Governance retains approval authority. Growth retains distribution and publishing. Finance retains actual economic truth; generation job costs are estimates or future supplied observations only.

## Lifecycle and invariants

- Requests begin `draft` and may be submitted or cancelled through the public API.
- A job may be registered only for a submitted request and an active, available, same-organization provider capability.
- Jobs begin `pending` with no output reference, actual cost, or latency. Sprint 028 exposes no command that moves a job into execution or completion.
- Requests, providers, jobs, and reviews are organization-scoped; cross-tenant references are rejected.
- Estimated and actual cost columns use fixed decimal precision and non-negative constraints. Latency is non-negative when supplied in a future governed workflow.
- Quality scores are bounded from zero through 100.
- Creating or submitting these records never creates or substitutes for a Governance approval.

## API

- `/api/v1/creative-generation-requests`
- `/api/v1/creative-providers`
- `/api/v1/creative-generation-jobs`
- `/api/v1/creative-quality-reviews`

The request endpoint supports a constrained draft-to-submitted or draft-to-cancelled transition. The remaining endpoints create and read registry records only.

## Explicit exclusions

No OpenAI API, Nano Banana, image generation, video generation, voice generation, editing provider, credential storage, external network execution, generated binary, publishing, advertising, autonomous agent, or financial transaction is included.
