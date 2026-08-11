# Creative Execution Adapter Foundation v1.0

Status: Sprint 029 implementation contract

## Purpose

This foundation connects creative generation workflow records to a provider-neutral execution contract. It defines execution state, evidence, artifact registration, and estimated cost observations without including any real adapter implementation, provider credential, network call, media generation, publishing, or advertising.

## Adapter contract

`CreativeExecutionAdapter` is an abstract Build-domain contract with provider and capability identity plus three required operations:

- `execute(input_snapshot)` returns a future output reference.
- `validate_output(output_reference)` evaluates a future provider output.
- `estimate_cost(generation_parameters)` returns an estimate only.

Supported future capability types are image generation, video generation, voice generation, and editing. Sprint 029 provides no concrete subclass and never invokes these methods.

## State machine

Generation jobs use the following controlled transitions:

- `pending` to `queued` or `cancelled`
- `queued` to `running` or `cancelled`
- `running` to `validating`, `failed`, `retrying`, or `cancelled`
- `validating` to `succeeded`, `failed`, or `retrying`
- `retrying` to `queued`, `failed`, or `cancelled`
- `succeeded`, `failed`, and `cancelled` are terminal

The workflow records start and completion timestamps, requires a reason for failure, and increments retry count when entering `retrying`. These transitions record state only and do not call an adapter.

## Records and ownership

| Record | Owner | Boundary |
|---|---|---|
| `CreativeExecutionRecord` | Build | Immutable supplied execution evidence tied to the job's provider and current state. |
| `CreativeArtifact` | Build | Links a succeeded job to a Build-owned creative asset and an artifact reference; it conveys no publication authority. |
| `CreativeGenerationCostObservation` | Build | Records provider/job estimates and supplied actual cost with currency; Finance remains monetary source of truth. |

All records are organization-scoped. Provider, job, asset, artifact, and cost references must resolve within the same tenant.

## API

- `/api/v1/creative-execution-records`
- `/api/v1/creative-artifacts`
- `/api/v1/creative-generation-costs`
- `/api/v1/creative-generation-jobs/{job_id}` for recorded state transitions

There is no execute, provider callback, publish, distribute, advertise, or approve endpoint.

## Authority boundaries

Decision owns recommendations. Build owns workflow and artifact records. Governance owns approvals. Growth owns distribution and publishing. Finance owns monetary truth. A succeeded state, valid artifact, or cost observation cannot substitute for approval, publication authority, advertising authority, or a Finance transaction.

## Explicit exclusions

No external AI SDK, HTTP client, provider credentials, OpenAI call, image generation, video generation, voice generation, editing implementation, binary media storage, publishing, advertising, autonomous agent, payment, or accounting entry is included.
