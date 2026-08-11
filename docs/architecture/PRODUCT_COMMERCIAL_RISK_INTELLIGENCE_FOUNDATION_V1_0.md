# Product Commercial Risk Intelligence Foundation v1.0

Status: frozen for Sprint 023 implementation

## Purpose

This foundation records evidence-backed product risk and produces deterministic advisory assessments that help humans identify candidates that should not proceed. It does not approve, reject, publish, purchase, or otherwise execute a commercial action.

## Ownership and authority

- Intelligence owns `ProductRiskSignal`, `ProductRiskAssessment`, and `CommercialViabilityAssessment` as advisory evidence.
- Decision owns recommendations made from Intelligence evidence.
- Build owns Product Truth and cannot be modified by these assessments.
- Finance owns financial truth; the supplied opportunity score is an assessment input, not a financial ledger record.
- Governance owns approvals. No Sprint 023 model carries approval authority or changes an approval record.

Every record is scoped to an `organization_id`. Services validate that the referenced `ProductCandidate` belongs to the same organization before writing data.

## Product risk signals

Signals classify trademark, copyright, safety, regulatory, payment-dispute, refund, shipping, quality, and customer-expectation risk. Evidence is retained as structured source references, confidence is bounded from zero to one, and severity is `low`, `medium`, `high`, or `critical`.

Signals start `open` and may be moved once to `mitigated`, `accepted`, or `dismissed`. These states describe evidence treatment; `accepted` does not constitute Governance approval.

## Risk assessment v1

The deterministic formula maps severity to 25, 50, 75, or 100 and computes the confidence-weighted mean of all non-dismissed signals. With no aggregate confidence, the score is zero and confidence remains zero. At least one active signal is required.

Risk levels are:

| Score | Level |
| --- | --- |
| 0–24.99 | low |
| 25–49.99 | medium |
| 50–74.99 | high |
| 75–100 | critical |

The immutable assessment input snapshot stores signal identifiers, signal count, severity weights, and the excluded status. Formula version is `product-commercial-risk-v1`.

## Commercial viability v1

`adjusted_score = clamp(opportunity_score - risk_score, 0, 100)`.

The latest organization-scoped risk assessment is required. Recommendations are deterministic:

- `REJECT` when risk is at least 75 or adjusted score is below 30.
- `GO` when adjusted score is at least 70 and risk is below 40.
- `TEST` when adjusted score is at least 50 and risk is below 60.
- `REVIEW` otherwise.

The reasoning records the inputs, result, formula version, and the human authority requirement. Recommendation values are advisory labels only and never create an approval or execution task.

## API boundary

- `/api/v1/product-risk-signals`
- `/api/v1/product-risk-assessments`
- `/api/v1/commercial-viability-assessments`

The API supports evidence capture, controlled signal status changes, deterministic assessment, and organization-scoped reads. It exposes no approve or execute operation.

## Explicit exclusions

No trademark API, supplier execution, Shopify, ads, LLM, agent, automation, Product Truth mutation, financial mutation, approval creation, or autonomous recommendation is included.
