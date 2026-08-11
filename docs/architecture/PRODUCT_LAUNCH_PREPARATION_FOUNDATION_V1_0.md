# Product Launch Preparation Foundation v1.0

Status: frozen for Sprint 025 implementation

## Purpose

This foundation converts an approved Build product into an evidence-backed preparation package before any channel is activated. It reports readiness gaps and an advisory score. It does not approve, publish, advertise, purchase, create an Operations launch, or execute a channel action.

## Ownership and authority

- Decision owns product positioning, offer strategy, objection guidance, launch-readiness assessment, and launch recommendations.
- Build owns the referenced Product and Product Truth. Sprint 025 never changes either.
- Growth owns future channel execution.
- Finance owns monetary truth. Pricing hypotheses are strategic prose, not prices or financial records.
- Governance owns approvals. A readiness state or score is never approval authority.

Every record is organization-scoped. Services validate that the referenced Build Product belongs to the organization and is `approved` or `active` before accepting preparation evidence.

## Preparation evidence

### Product positioning

Positioning records the target customer, customer problem, primary benefit, differentiation, positioning statement, and confidence. Records are append-only; the latest record is used when a package is generated.

### Offer strategy

Offer strategy records pricing, bundle, guarantee, bonus, and urgency hypotheses plus confidence. These are advisory strategies. They cannot change prices, issue guarantees, create discounts, or bind the business.

### Product objections

Each objection retains the objection type, customer language, recommended response, and a required evidence reference. Recommended responses remain drafts and must respect Product Truth and claim policies in future execution.

## Readiness calculation

Each of five components contributes zero, ten, or twenty points:

| Component | Missing | Review | Ready |
| --- | ---: | ---: | ---: |
| Positioning | no record | confidence below 0.70 | confidence at least 0.70 |
| Offer | no record | confidence below 0.70 | confidence at least 0.70 |
| Objections | no traceable objection | not used | at least one traceable objection |
| Creative | no strategy | draft/archived strategy | approved/active strategy |
| Listing | no strategy | draft/archived strategy | approved/active strategy |

`launch_score` is the sum and is bounded from zero to 100. The immutable package snapshots component statuses and score at generation time. It does not create a ProductLaunch or change any source record.

## API boundary

- `/api/v1/product-positioning`
- `/api/v1/offer-strategies`
- `/api/v1/product-objections`
- `/api/v1/launch-packages`

The API supports evidence capture, package generation, and organization-scoped reads. It exposes no approve, publish, advertise, purchase, activate, or execute route.

## Explicit exclusions

No Shopify, ads, publishing, LLM, agent, supplier purchasing, product mutation, financial mutation, approval creation, Operations launch creation, or channel execution is included.
