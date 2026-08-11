# Market Intelligence Connector Foundation v1.0

Status: Sprint 019 implementation contract

## Purpose and ownership

This foundation accepts caller-supplied external market data through stable contracts and stores both raw and normalized representations. Intelligence owns connector definitions, ingestion state, raw records, and normalized items. Decision retains opportunity recommendations; Governance, Finance, and Operations retain approvals, economic truth, and execution.

## Connector definitions

`MarketConnectorDefinition` describes a future integration without implementing it. Each organization-scoped definition records a name, platform, connector type, lifecycle status, and a JSON configuration schema. Supported types are Reddit, Amazon, Etsy, search trend, news, and social. Definitions begin inactive and may become active, inactive again, or archived.

The definition is distinct from the Sprint 017 `MarketDataSource`: connector definitions describe how data may enter, while data sources describe the provenance registry used by validated market signals. Sprint 019 deliberately does not auto-create or mutate a `MarketDataSource`.

## Raw and normalized storage

`MarketDataRecord` preserves caller-supplied content, metadata, source reference, content type, and capture time. Records require an active connector definition. Raw content is immutable through the V1 API.

`NormalizedMarketItem` attaches structured category, topic, customer language, signal type, and bounded confidence to an existing raw record. Normalization values are supplied by an authorized caller; no LLM, classifier, scraper, or automatic transformation exists. Normalized items do not create market signals or opportunities.

## Ingestion jobs

`MarketIngestionJob` records orchestration state only:

```text
PENDING -> RUNNING -> COMPLETED
                   -> FAILED
```

Starting and terminal timestamps are recorded by the service. Record count is non-negative. A job does not fetch data or invoke a connector.

## Tenant and authority boundaries

- Every entity carries `organization_id`; referenced definitions and records must belong to the same organization.
- APIs list only records explicitly scoped to an organization.
- Connector configuration stores a schema, never credentials or secrets.
- No endpoint executes a live sync, creates a market signal, creates an opportunity, recommends an action, or grants approval.
- This Sprint 019 statement is superseded for Reddit by the [Sprint 020 Reddit connector](./REDDIT_MARKET_INTELLIGENCE_CONNECTOR_V1.md); Amazon, Etsy, Google, social, and news integrations remain absent.
- No scraping, LLM, agent, autonomous research, or external network behavior is present.
- The existing authentication limitation continues to prohibit public deployment.
