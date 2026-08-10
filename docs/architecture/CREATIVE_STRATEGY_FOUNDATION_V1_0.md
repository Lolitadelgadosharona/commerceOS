# Creative Strategy Foundation v1.0

Status: Sprint 009 implementation contract

## Purpose and ownership

Decision owns creative strategy, hypotheses, channel-fit assessments, briefs, and experiment observations. Build owns any future creative artifacts; Growth owns future channel and advertising execution; Governance owns the canonical Experiment Registry and approval authority. Sprint 009 records plans and evidence only.

Creative records reference authoritative Build Products read-only. They cannot add Product Truth claims, publish content, generate media, create campaigns, spend money, or invoke an external provider.

## Structures

- `CreativeStrategy` describes audience, objective, core message, emotional angle, and creative direction. One current strategy exists per product.
- `CreativeHypothesis` records a falsifiable behavioral expectation, success metric, confidence, and review status.
- `CreativeBrief` records platform, audience, hook, story structure, proof points, CTA, and a controlled format: video, image, carousel, UGC, testimonial, or educational.
- `CreativeChannelFit` records a 0–100 suitability score and rationale for TikTok, Instagram, Facebook, Pinterest, or Google. It does not connect to those channels.
- `CreativeExperiment` is a creative test-plan/result observation linked to a hypothesis. It is not the Governance Experiment Registry and cannot execute a treatment.

## Lifecycles

Creative strategies move `draft → approved → active → archived`, with early archival allowed. Approval is internal strategy review and grants no publishing, advertising, or spending authority.

Creative experiments move `planned → running → completed`. States cannot be skipped or reversed, and completion requires a recorded result. `running` records a workflow observation only; no automated test execution is present.

## API and exclusions

The `/api/v1` resources are `/creative-strategies`, `/creative-hypotheses`, `/creative-briefs`, `/creative-channel-fits`, and `/creative-experiments`.

There is no LLM, agent, image/video generation, OpenAI image tool, Nano Banana, TikTok API, Meta Ads API, advertising, publishing, or external API integration. Public deployment remains prohibited until authentication activation is completed.
