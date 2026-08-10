# Channel Strategy and Conversion Path Foundation v1.0

Status: frozen Sprint 010 implementation contract

## Purpose and ownership

The Decision domain owns channel recommendations, their rationale, evidence lineage, deterministic opportunity scoring, and conversion-path plans. These records are advisory. Growth owns future acquisition and channel execution; Operations owns checkout, lead handling, qualification, quoting, and order execution; Governance owns approval authority; Finance owns actual revenue, cost, margin, and payment truth.

No Sprint 010 record authorizes publishing, spending, outreach, messaging, quoting, ordering, or external-system access.

## Strategy model

A `ChannelStrategy` is scoped to an organization, optional project, product, market, geography, audience, B2C or B2B business model, and objective. Its controlled lifecycle is `draft -> recommended -> approved`, with rejection and archival exits. Approval records intent only; it is not execution authority.

The optional `creative_strategy_id` preserves the conceptual chain `Product -> CreativeStrategy -> Channel x Audience x Objective`. Creative owns message and format decisions. Channel Strategy consumes that decision and does not duplicate it.

## Candidates and scoring

Initial accepted channel identifiers are TikTok, Instagram, Facebook, Pinterest, Google, and Reddit. Persistence uses an extensible string rather than a database enum. Distribution modes are organic, paid, community, search, messaging, and hybrid. Every recommendation records a reason; every exclusion records an explicit exclusion reason.

The `channel-opportunity-v1.0` formula averages only evidenced factors. Target-customer fit, product fit, buying intent, visual fit, organic potential, search-discovery potential, historical-performance confidence, and conversion-path fit contribute directly. Content cost, competition, and expected acquisition cost are penalties and contribute as `100 - input`. Inputs are 0–100. Equal weighting applies among present inputs. `evidence_coverage` is present factors divided by 11. Missing inputs remain null and do not become neutral or invented history; scoring with no evidence is rejected.

## Conversion paths

Paths copy the strategy business model to prevent B2C/B2B drift and contain uniquely ordered steps. B2C validation requires acquisition/discovery, a landing or product page, checkout, and order in order. B2B validation requires acquisition/discovery, lead form or message, qualification, quote, and order in order.

Step ownership is validated: Growth owns content, advertising, search discovery, community interaction, landing pages, and product pages; Operations owns checkout, lead forms, messages, qualification, quotes, and orders. Paid advertising retains an approval boundary. Quotes require human authority. Governance and Finance remain approval/truth boundaries rather than execution step owners.

## Measurement and evidence

Measurement plans define expected metric names only, including reach, engagement, acquisition, conversion, revenue, profitability, refunds, disputes, and lifetime value. They never store observed financial truth; Finance remains authoritative for actual monetary outcomes.

Decision evidence records the evidence type, source reference, summary, and confidence. Supported lineage includes customer, opportunity, product, listing/GEO, creative, historical observation, and market research. A creative evidence reference must match the strategy's linked Creative Strategy.

Reddit is modeled in two distinct contexts: intelligence sources are evidence observed from Reddit; a Reddit channel candidate is a separately evaluated acquisition/community choice. Evidence presence never implies channel recommendation.

## API and exclusions

The `/api/v1` boundary exposes channel strategies, candidates, opportunity scores, conversion paths, ordered steps, measurement plans, and evidence. It provides planning and validation only.

Explicitly excluded: connectors, publishing, advertising execution, messaging execution, autonomous optimization, LLMs, agents, scraping, external APIs, and customer-facing automation.
