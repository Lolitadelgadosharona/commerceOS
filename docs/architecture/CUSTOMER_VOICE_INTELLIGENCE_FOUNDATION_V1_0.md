# Customer Voice Intelligence Foundation v1.0

Status: Sprint 021 implementation contract

## Purpose and ownership

This foundation transforms source-traceable customer pain observations into reusable Intelligence-owned clusters, customer-language assets, and purchase-intent signals. These are advisory evidence assets for authorized consumers. Decision owns opportunity recommendations, Build owns Product Truth, Growth owns marketing execution, Operations owns customer operations, and Finance owns economics.

## Pain clusters and membership

`CustomerPainCluster` groups related pain candidates under an organization-scoped draft, active, or archived lifecycle. Severity is deterministic:

```text
severity = frequency * 30%
         + emotion * 25%
         + urgency * 30%
         + growth * 15%
```

Inputs and formula version are persisted as scoring evidence. Each input and the result are bounded from 0 to 100; confidence is bounded from 0 to 1.

`PainClusterMembership` links an existing organization-scoped `CustomerPainCandidate` to a cluster with relevance bounded from 0 to 1. The membership preserves the lineage from cluster through candidate to the original `MarketDataRecord`.

## Customer language library

`CustomerLanguageInsight` stores a phrase, its context, intended usage, and observed frequency against a cluster. Usage types are listing, creative, sales, support, and product. The asset is evidence for human-controlled downstream work; it cannot modify Product Truth, publish copy, contact a customer, or execute marketing.

## Purchase intent signals

`PurchaseIntentSignal` links directly to an existing raw source record and classifies supplied evidence as research, comparison, buying intent, or urgent need. Its deterministic score is:

```text
intent = question behavior * 20%
       + solution seeking * 35%
       + purchase language * 45%
```

Score inputs, evidence, and formula version are stored for explanation. The signal is an observation, not a recommendation, approval, sales action, or proof of purchase.

## Authority and scope limits

- All entities and relationships enforce organization ownership.
- Cluster and intent calculations are deterministic and reproducible.
- Source records and pain candidates remain immutable through these APIs.
- No opportunity, product, listing, creative, sales action, or support action is created automatically.
- No LLM, agent, customer outreach, posting, replying, marketing, Amazon, Etsy, or advertising integration exists.
- Public deployment remains prohibited until verified authentication and authorization are activated.
