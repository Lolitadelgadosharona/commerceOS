# Supplier Intelligence Foundation v1.0

Status: Sprint 007 implementation contract

## Purpose and ownership

Intelligence owns `SupplierProfile` evaluation observations, evaluations, risks, product matches, and explanatory decision records. These are not the Operations-owned Supplier master and cannot create purchase orders, payments, inventory, fulfillment, or external supplier actions. Build Product is referenced read-only.

An `approved` SupplierProfile means approved for internal evaluation use only. It is not supplier onboarding, procurement approval, contractual acceptance, or permission to spend.

## Models and lifecycle

- `SupplierProfile` records manually supplied identity, origin, capabilities, certifications, and evaluation lifecycle. Allowed progression is discovered to evaluating, rejected, or archived; evaluating to approved, rejected, or archived; approved/rejected to archived. Approval requires at least one evaluation.
- `SupplierEvaluation` is append-only and stores five bounded input scores, confidence, overall result, and formula version.
- `SupplierRisk` records quality, delivery, compliance, counterfeit, capacity, or communication risk with severity and status. Risk acceptance is not Governance approval.
- `ProductSupplierMatch` links an authoritative Build Product to an evaluated profile. Scores at or above 70 are deterministically recommended.
- `SupplierDecisionRecord` explains an advisory supplier choice and its evidence. It requires an approved profile and recommended match but creates no operational commitment.

## Deterministic evaluation v1.0

```text
overall = (quality + price + lead time + communication + compliance) / 5
```

Inputs and output are bounded 0–100. The result is rounded to two decimals and stores formula version `v1.0`. Confidence is separately bounded 0–1 and does not alter the score.

## API and exclusions

The `/api/v1` resources are `/suppliers`, `/supplier-evaluations`, `/supplier-risks`, `/product-supplier-matches`, and `/supplier-decisions`.

There are no supplier APIs, AliExpress, Alibaba, scraping, procurement, purchasing, payments, inventory, Shopify, or fulfillment automation. Public deployment remains prohibited until the documented authentication activation limitation is resolved.
