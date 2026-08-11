# Customer Need to Product Opportunity Foundation v1.0

Status: Sprint 022 implementation contract

## Purpose and ownership

This Intelligence-owned foundation maps source-traceable customer pain into customer needs, solution hypotheses, and advisory assessments of existing market opportunities. Decision retains recommendations, Build retains Product Truth, Finance retains economics, and Governance retains approvals.

## Evidence chain

`CustomerNeed` records a draft, validated, or archived need. `PainNeedMapping` links it to an existing customer pain cluster and requires its evidence count to equal the cluster's persisted source memberships. `ProductSolutionHypothesis` proposes a category and solution with bounded fit and confidence; it is not a Build product.

The resulting trace is:

```text
MarketDataRecord -> CustomerPainCandidate -> PainClusterMembership
-> CustomerPainCluster -> PainNeedMapping -> CustomerNeed
-> ProductSolutionHypothesis -> CustomerBackedOpportunityAssessment
-> existing MarketOpportunity
```

## Customer-backed assessment

An assessment requires an existing organization-scoped market opportunity, pain mapping, and solution hypothesis. All inputs are bounded from 0 to 100:

```text
overall = pain strength * 25%
        + solution fit * 25%
        + intent * 15%
        + competition attractiveness * 10%
        + margin evidence * 15%
        + inverse risk * 10%
```

Margin is supplied advisory evidence and does not replace Finance truth. The formula version is stored. The assessment creates no recommendation, approval, Product Truth, supplier action, or execution.

## Exclusions

No AliExpress, supplier search, Shopify, advertising, LLM, agent, product creation, opportunity creation, approval, or execution exists. Public deployment remains prohibited until verified authentication is active.
