# Market Intelligence Data Foundation v1.0

Status: Sprint 017 implementation contract

## Purpose and ownership

This foundation accepts supplied external-market observations through governed data contracts. Intelligence owns source registrations, normalized signals, supporting evidence, clusters, and evidence links to market opportunities. Decision continues to own opportunity recommendations; Governance, Finance, and Operations retain approval, economic-truth, and execution ownership.

## Source registry

`MarketDataSource` records an organization-specific source name, platform, source type, access method, reliability score, and status. Supported platform classifications cover Reddit, Amazon reviews, Etsy reviews, Google Trends, Pinterest Trends, news, and social media. These are labels only; no connector credentials or network behavior are included.

Access methods are manual, file import, and future connector. Sources start inactive and may become active, inactive again, or archived. Archived sources are terminal. New signals require an active registered source.

## Market signals and evidence

`MarketSignal` stores the supplied region, category, signal type, title, description, trend direction, confidence, and observation time. Trends are rising, falling, or stable. Signals move from observed to validated to archived; an observed signal may also be archived directly. Descriptive signal data is append-only after creation.

`MarketSignalEvidence` is owned by the same organization and signal. It preserves evidence type, an opaque content reference, strength, and capture time. Content references do not trigger fetching, scraping, or processing.

Reliability, confidence, evidence strength, and cluster confidence are bounded from 0 to 1. Cluster impact is bounded from 0 to 100.

## Clustering

`MarketSignalCluster` groups related observations by explicit membership records. Adding a membership neither changes the source signal nor derives new content. Clusters are supplied analytical groupings; no LLM or automated clustering exists.

## Opportunity separation

`MarketSignalOpportunityLink` associates a signal with an existing, organization-scoped `MarketOpportunity` as evidence only. Linking validates that both records already exist and never creates, qualifies, recommends, approves, or executes an opportunity.

## Authority and activation limits

- Every record and association is organization-scoped.
- Intelligence observations do not become Decision recommendations automatically.
- No source connector, credential storage, API client, scraper, browser automation, LLM, agent, or autonomous research workflow is present.
- No record grants approval or execution authority.
- The existing authentication limitation continues to prohibit public deployment.
