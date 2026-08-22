# GrowthOS Revenue Engine Foundation v2

Status: frozen for Sprint 057 implementation

## Independent engines and shared capabilities

GrowthOS is the business-customer revenue engine. CommerceOS is the market-opportunity and product
evaluation engine. Neither is subordinate to the other, and GrowthOS is not the exclusive source of
CommerceOS opportunities.

They reuse a shared capability layer: Demand Intelligence, Customer Intelligence, the evidence
framework, Learning Loop, Sales Copilot, and governed AI Runtime. Shared infrastructure does not
transfer source-of-truth ownership.

| Engine | Owned evidence and workflow |
|---|---|
| GrowthOS | Business websites, Google Business, social presence, public reviews, business pain, Growth Opportunities, Growth Gifts, reviewed outreach, sales conversations, and service delivery state |
| CommerceOS | Consumer and marketplace signals, Reddit, Amazon/Etsy reviews, social/search trends, predictive evidence, external research, market opportunities, and product/supplier evaluation |

GrowthOS customer signals may enter shared Demand Intelligence through the controlled bridge.
CommerceOS independently retains external, marketplace, social, trend, predictive, research, and
manual sources. The V2 dashboard reports GrowthOS and non-GrowthOS demand-source counts separately
to make this independence visible.

## Evidence-backed business intelligence

A Business Growth Profile is a tenant-scoped projection over a Growth Prospect and its immutable
evidence. It records business identity, industry, location, observed digital presence, customer
signals, strengths, weaknesses, possible growth areas, and confidence. Every profile requires
evidence belonging to the same prospect; unknown channels remain unknown.

Growth Opportunities continue using the canonical advisory analysis record. V2 supports website
conversion, SEO, Google Business, social media, content, branding, retention, and reputation
categories. Each record cites evidence and retains customer impact, recommended solution,
confidence, missing information, and an optional—not fabricated—purchase probability.

## Explainable revenue ranking

Prospect ranking uses the arithmetic mean of five supplied 0–100 inputs: pain severity, business
impact, accessibility, buying signals, and solution fit. If any input is missing, the total score is
`null`, the missing fields are listed, and no substitute value is invented. The formula is versioned
as `growth-revenue-ranking-v1`.

## Growth Gift, outreach, Sales Copilot, and pipeline

Growth Gifts extend the existing evidence chain with observed issue, before state, after concept,
recommended improvement, expected value, preview type, and preview status. Website, social, SEO,
and Google profile previews are metadata only; Sprint 057 does not generate or deliver them.

Outreach remains an evidence-first draft prepared through the governed AI Runtime. Generic agency
language, AI self-reference, and guaranteed/exaggerated ROI claims are rejected. Sending and
negotiation remain outside the system and require human authority. Sales Copilot continues producing
analysis, recommendations, and reply drafts for human review only.

The canonical pipeline remains Prospect → Evidence Reviewed → Growth Opportunity → Growth Gift →
Outreach → Reply → Qualified → Customer. Pipeline states record controlled observations; they do
not perform customer contact or conversion.

## Authority and non-goals

Growth owns revenue workflow state. Intelligence owns shared evidence contracts. Governance owns
approval. Finance owns monetary truth. AI may classify, analyze, recommend, and draft with
provenance; it may not send, negotiate, approve, promise ROI, commit money, or alter source truth.

Sprint 057 adds no scraping, live website/social/review connectors, autonomous outreach, autonomous
sales, customer messaging, product creation, supplier execution, or CommerceOS opportunity monopoly.
