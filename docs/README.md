# Commerce OS Architecture and Governance Index

Status: Sprint 059 Revenue Experiment Execution Layer

## Governing documents

Read these documents together. If they conflict, the [Constitution](./governance/AI_COMMERCE_OS_CONSTITUTION_V1_0.md) governs product values and authority; the [Security Foundation](./governance/SECURITY_AND_PRIVACY_FOUNDATION_V1_0.md) and [Finance Authority Model](./governance/FINANCE_AUTHORITY_MODEL_V1_0.md) govern their respective controls; the [Architecture Freeze](./architecture/ARCHITECTURE_FREEZE_V1_1.md) governs structure; and the [PRD](./product/COMMERCE_OS_PRD_V1_0.md) and [MVP Boundary](./product/MVP_BOUNDARY_V1_0.md) govern delivery scope. A stricter legal, security, financial, or human-approval rule always prevails.

| Document | Purpose |
|---|---|
| [AI Commerce OS Constitution v1.0](./governance/AI_COMMERCE_OS_CONSTITUTION_V1_0.md) | Mission, principles, AI permissions, and owner authority |
| [Commerce OS PRD v1.0](./product/COMMERCE_OS_PRD_V1_0.md) | Product goals, users, workflows, and acceptance principles |
| [Incremental Architecture Freeze v1.1](./architecture/ARCHITECTURE_FREEZE_V1_1.md) | Frozen domain structure and incremental capabilities |
| [Repository Reality Audit v1.0](./architecture/REPOSITORY_REALITY_AUDIT_V1_0.md) | Observed source, stack, database, API, test, CI, and deployment state |
| [Canonical Entity Model v1.0](./architecture/CANONICAL_ENTITY_MODEL_V1_0.md) | Entity purpose, ownership, authority, and consumers |
| [Domain Ownership Model](./governance/DOMAIN_OWNERSHIP_MODEL_V1_0.md) | Domain responsibilities and cross-domain write rules |
| [Data Ownership Contract](./governance/DATA_OWNERSHIP_CONTRACT_V1_0.md) | Entity-level source-of-truth and authority assignments |
| [Role Authority Model v1.0](./governance/ROLE_AUTHORITY_MODEL_V1_0.md) | Abstract human roles and approval composition |
| [Security and Privacy Foundation](./governance/SECURITY_AND_PRIVACY_FOUNDATION_V1_0.md) | PII, identity, access, audit, secrets, and retention controls |
| [Production Authorization Foundation v1.0](./security/PRODUCTION_AUTHORIZATION_FOUNDATION_V1_0.md) | Verified sessions, universal API authorization, tenant boundary, worker identity, and security audit |
| [Finance Authority Model](./governance/FINANCE_AUTHORITY_MODEL_V1_0.md) | AI-executable versus owner-approved financial actions |
| [Tenant Model v1.0](./architecture/TENANT_MODEL_V1_0.md) | Single-operator V1 scope with future-compatible hierarchy |
| [Deployment Topology v1.0](./architecture/DEPLOYMENT_TOPOLOGY_V1_0.md) | Vendor-neutral logical runtime and integration topology |
| [API Convention v1.0](./architecture/API_CONVENTION_V1_0.md) | Synchronous API, errors, auth, versioning, and event conventions |
| [Customer Intelligence Foundation v1.0](./architecture/CUSTOMER_INTELLIGENCE_FOUNDATION_V1_0.md) | Signal lineage, deterministic clustering, insight evidence, and scope limits |
| [Opportunity Intelligence Foundation v1.0](./architecture/OPPORTUNITY_INTELLIGENCE_FOUNDATION_V1_0.md) | Market observations, evidence, product hypotheses, deterministic scoring, and risks |
| [Product Intelligence Foundation v1.0](./architecture/PRODUCT_INTELLIGENCE_FOUNDATION_V1_0.md) | Product hypotheses, economics, supplier references, risks, and deterministic investment scoring |
| [Product Truth Foundation v1.0](./architecture/PRODUCT_TRUTH_FOUNDATION_V1_0.md) | Authoritative products, approved truth versions, product knowledge, and brand claim guardrails |
| [Supplier Intelligence Foundation v1.0](./architecture/SUPPLIER_INTELLIGENCE_FOUNDATION_V1_0.md) | Supplier evaluation profiles, deterministic scoring, risks, matches, and advisory decisions |
| [Listing Intelligence and GEO Foundation v1.0](./architecture/LISTING_INTELLIGENCE_GEO_FOUNDATION_V1_0.md) | Product-grounded strategy, question maps, discovery knowledge, briefs, and evidence |
| [Creative Strategy Foundation v1.0](./architecture/CREATIVE_STRATEGY_FOUNDATION_V1_0.md) | Creative strategy, hypotheses, briefs, channel fit, and experiment observations |
| [Channel Strategy and Conversion Path Foundation v1.0](./architecture/CHANNEL_STRATEGY_CONVERSION_FOUNDATION_V1_0.md) | Evidence-led channel recommendations, deterministic scoring, B2C/B2B paths, and authority boundaries |
| [Conversation Commerce Foundation v1.0](./architecture/CONVERSATION_COMMERCE_FOUNDATION_V1_0.md) | Operations-owned threads, messages, observations, human handoffs, and trusted-knowledge links |
| [AI Sales and Support Decision Foundation v1.0](./architecture/AI_SALES_SUPPORT_DECISION_FOUNDATION_V1_0.md) | Evidence-grounded advisory profiles, recommendations, risk signals, and Governance-owned AI policy |
| [Creative Intelligence and Multi-Model Router Foundation v1.0](./architecture/CREATIVE_INTELLIGENCE_ROUTER_FOUNDATION_V1_0.md) | Asset strategy, provider evaluations, deterministic routing, economic assessment, and Creative DNA references |
| [CFO and Revenue Intelligence Foundation v1.0](./architecture/CFO_REVENUE_INTELLIGENCE_FOUNDATION_V1_0.md) | Financial observations, deterministic profitability, unit economics, CFO recommendations, and financial risk boundaries |
| [AI Operating Committee and CEO Dashboard Foundation v1.0](./architecture/AI_OPERATING_COMMITTEE_CEO_DASHBOARD_FOUNDATION_V1_0.md) | Cross-domain executive projections, operating signals, human decision queue, reviews, and read-only dashboards |
| [Commerce Execution and Launch Workflow Foundation v1.0](./architecture/COMMERCE_EXECUTION_LAUNCH_WORKFLOW_FOUNDATION_V1_0.md) | Governed product launches, ordered milestones, assigned tasks, action plans, blockers, and non-execution boundaries |
| [Market Intelligence Data Foundation v1.0](./architecture/MARKET_INTELLIGENCE_DATA_FOUNDATION_V1_0.md) | Registered market sources, normalized signals, evidence, clusters, and evidence-only opportunity links |
| [Opportunity Intelligence Analysis Foundation v1.0](./architecture/OPPORTUNITY_INTELLIGENCE_ANALYSIS_FOUNDATION_V1_0.md) | Signal interpretation, deterministic assessments, advisory reports, and review-only decision queue links |
| [Market Intelligence Connector Foundation v1.0](./architecture/MARKET_INTELLIGENCE_CONNECTOR_FOUNDATION_V1_0.md) | Connector contracts, raw records, normalized items, and ingestion job state |
| [Reddit Market Intelligence Connector v1](./architecture/REDDIT_MARKET_INTELLIGENCE_CONNECTOR_V1.md) | Read-only Reddit ingestion, raw records, pain detection, evidence, and safety boundaries |
| [Customer Voice Intelligence Foundation v1.0](./architecture/CUSTOMER_VOICE_INTELLIGENCE_FOUNDATION_V1_0.md) | Pain clusters, customer-language assets, deterministic severity and intent scoring, and source traceability |
| [Customer Need to Product Opportunity Foundation v1.0](./architecture/CUSTOMER_NEED_PRODUCT_OPPORTUNITY_FOUNDATION_V1_0.md) | Customer needs, pain mappings, solution hypotheses, and customer-backed opportunity assessment |
| [Product Commercial Risk Intelligence Foundation v1.0](./architecture/PRODUCT_COMMERCIAL_RISK_INTELLIGENCE_FOUNDATION_V1_0.md) | Product risk evidence, deterministic assessments, commercial viability, and advisory authority boundaries |
| [Product Economics and Margin Intelligence Foundation v1.0](./architecture/PRODUCT_ECONOMICS_MARGIN_INTELLIGENCE_FOUNDATION_V1_0.md) | Decimal economic assumptions, profit simulation, scenarios, and risk-adjusted advisory scoring |
| [Product Launch Preparation Foundation v1.0](./architecture/PRODUCT_LAUNCH_PREPARATION_FOUNDATION_V1_0.md) | Positioning, offer strategy, objections, and deterministic pre-execution readiness packages |
| [AI Discovery Listing Intelligence Foundation v1.0](./architecture/AI_DISCOVERY_LISTING_INTELLIGENCE_FOUNDATION_V1_0.md) | Evidence-backed listing blueprints, GEO knowledge, quality scoring, and AI discovery readiness |
| [Creative Asset Intelligence Foundation v1.0](./architecture/CREATIVE_ASSET_INTELLIGENCE_FOUNDATION_V1_0.md) | Human-planned creative briefs, artifact registry, sequential versions, and supplied performance observations |
| [Creative Generation Workflow Foundation v1.0](./architecture/CREATIVE_GENERATION_WORKFLOW_FOUNDATION_V1_0.md) | Provider-neutral requests, capability contracts, pending jobs, and human quality review records |
| [Creative Execution Adapter Foundation v1.0](./architecture/CREATIVE_EXECUTION_ADAPTER_FOUNDATION_V1_0.md) | Abstract adapter contract, controlled job state, artifact links, execution records, and cost observations |
| [Channel Execution and Creative Distribution Foundation v1.0](./architecture/CHANNEL_EXECUTION_FOUNDATION_V1_0.md) | Growth-owned channel plans, experiment designs, governed distribution state, and performance observations |
| [Customer 360 Identity Resolution Foundation v1.0](./architecture/CUSTOMER_360_IDENTITY_RESOLUTION_FOUNDATION_V1_0.md) | Operations identity observations, Intelligence journey projection, and advisory customer value assessment |
| [Strategic Account Intelligence Foundation v1.0](./architecture/STRATEGIC_ACCOUNT_INTELLIGENCE_FOUNDATION_V1_0.md) | Account state, supplied stakeholders, replenishment, expansion, next-best actions, and deterministic strategic scoring |
| [Opportunity-to-Launch Integration v1.0](./architecture/OPPORTUNITY_TO_LAUNCH_INTEGRATION_V1_0.md) | First end-to-end investment memo, readiness, Governance review, launch activation, and action-plan composition |
| [AI Runtime Foundation v1.0](./architecture/AI_RUNTIME_FOUNDATION_V1_0.md) | Provider/model metadata, governed request lifecycle, prompt versioning, output authority, and advisory costs |
| [External Intelligence Connector Foundation v1.0](./architecture/EXTERNAL_INTELLIGENCE_CONNECTOR_FOUNDATION_V1_0.md) | Secure registry, ingestion lifecycle, immutable evidence, normalization, credential references, and rate limits |
| [Marketplace Customer Voice Foundation v1.0](./architecture/MARKETPLACE_CUSTOMER_VOICE_FOUNDATION_V1_0.md) | Amazon- and Etsy-compatible immutable review evidence, normalization, explicit intelligence links, and compliance boundaries |
| [AI Research Analyst Foundation v1.0](./architecture/AI_RESEARCH_ANALYST_FOUNDATION_V1_0.md) | Cited AI-assisted analysis, structured research, confidence, and human review boundaries |
| [Creative AI Production Foundation v1.0](./architecture/CREATIVE_AI_PRODUCTION_FOUNDATION_V1_0.md) | Controlled creative production, AI provenance, artifact lifecycle, quality gates, and approval boundaries |
| [Growth Experiment and Performance Foundation v1.0](./architecture/GROWTH_EXPERIMENT_PERFORMANCE_FOUNDATION_V1_0.md) | Governed Growth experiments, distribution planning, supplied performance observations, and evidence-linked learning |
| [Revenue Conversation Intelligence Foundation v1.0](./architecture/REVENUE_CONVERSATION_INTELLIGENCE_FOUNDATION_V1_0.md) | Append-only journeys, evidence-backed intent, advisory sales/value intelligence, support learning, and read-only projections |
| [Closed-Loop Revenue Learning Foundation v1.0](./architecture/CLOSED_LOOP_REVENUE_LEARNING_FOUNDATION_V1_0.md) | Immutable cross-domain observations, hypotheses, conclusions, advisory improvements, priority, and feedback traceability |
| [Governed AI Provider Execution Runtime v1.0](./architecture/GOVERNED_AI_PROVIDER_EXECUTION_RUNTIME_V1_0.md) | Provider-neutral governed inference, authority/cost/rate gates, provenance, usage, and advisory output composition |
| [AI Research Analyst Operationalization Foundation v1.0](./architecture/AI_RESEARCH_ANALYST_OPERATIONALIZATION_FOUNDATION_V1_0.md) | Evidence-grounded Research Runs, governed AI execution, structured analysis, citations, and human review |
| [AI Opportunity Discovery Foundation v1.0](./architecture/AI_OPPORTUNITY_DISCOVERY_FOUNDATION_V1_0.md) | Governed evidence-to-candidate discovery, structured output, advisory confidence, and human review |
| [AI Creative Intelligence Foundation v1.0](./architecture/AI_CREATIVE_INTELLIGENCE_FOUNDATION_V1_0.md) | Evidence-grounded creative strategy, angle, and brief recommendations without production authority |
| [AI Listing and GEO Content Intelligence Foundation v1.0](./architecture/AI_LISTING_GEO_INTELLIGENCE_FOUNDATION_V1_0.md) | Evidence-grounded listing, GEO, and FAQ recommendations without Product Truth or publishing authority |
| [GrowthOS Revenue Engine Foundation v1.0](./architecture/GROWTH_OS_REVENUE_ENGINE_FOUNDATION_V1_0.md) | Founder-operated prospect, evidence, Growth Gift, outreach preparation, and Sales Copilot workflow without external execution |
| [GrowthOS Prospect Discovery Foundation v1.0](./architecture/GROWTH_OS_PROSPECT_DISCOVERY_FOUNDATION_V1_0.md) | Controlled prospect discovery, immutable research evidence, deterministic qualification, governed AI research, and Intelligence signal bridge |
| [GrowthOS Revenue Activation Foundation v1.0](./architecture/GROWTH_OS_REVENUE_ACTIVATION_FOUNDATION_V1_0.md) | Human-controlled experiments, evidence-backed Growth Gifts, reviewed outreach, outcome observations, and Sales Copilot advice |
| [GrowthOS Conversation Intelligence Foundation v1.0](./architecture/GROWTH_OS_CONVERSATION_INTELLIGENCE_FOUNDATION_V1_0.md) | Governed reply analysis, objection intelligence, Learning observations, message performance, and sales knowledge projections |
| [Demand Intelligence Bridge Foundation v1.0](./architecture/DEMAND_INTELLIGENCE_BRIDGE_FOUNDATION_V1_0.md) | Deterministic, evidence-only bridge from accepted GrowthOS conversation learning to reviewed CommerceOS demand signals |
| [Business Demand Intelligence Foundation v1.0](./architecture/BUSINESS_DEMAND_INTELLIGENCE_FOUNDATION_V1_0.md) | Shared GrowthOS, external market, research, and manual demand-source abstraction with traceable evidence |
| [Demand Intelligence Enhancement Foundation v1.0](./architecture/DEMAND_INTELLIGENCE_ENHANCEMENT_FOUNDATION_V1_0.md) | Observed, customer voice, marketplace, trend, and predictive evidence with explainable multi-source diversity |
| [Opportunity Discovery Engine Foundation v1.0](./architecture/OPPORTUNITY_DISCOVERY_FOUNDATION_V1_0.md) | Deterministic demand-to-opportunity candidates, append-only evidence, advisory assessment, and human review |
| [Product Opportunity Evaluation Foundation v1.0](./architecture/PRODUCT_OPPORTUNITY_EVALUATION_FOUNDATION_V1_0.md) | Accepted opportunity-to-product hypotheses, deterministic evaluation, append-only evidence, and human review |
| [GrowthOS Revenue Engine Foundation v2](./architecture/GROWTHOS_REVENUE_ENGINE_V2_FOUNDATION.md) | Independent GrowthOS and CommerceOS engines over shared evidence, AI, Sales Copilot, Demand, and Learning capabilities |
| [Industry Intelligence and AI Growth Service Foundation](./architecture/INDUSTRY_INTELLIGENCE_AI_GROWTH_SERVICE_FOUNDATION_V1_0.md) | Reusable vertical intelligence, GEO assessments, service recommendations, and governed industry learning |
| [Revenue Experiment Execution Layer](./architecture/REVENUE_EXPERIMENT_EXECUTION_LAYER_V1_0.md) | Daily evidence-backed prospect queue, controlled Growth Gift lifecycle, Revenue dashboard, and provider-neutral routing |
| [Tech Stack Decision v1.0](./architecture/TECH_STACK_DECISION_V1_0.md) | Frozen frontend, backend, data, queue, testing, CI, and container stack |
| [Repository Structure v1.0](./architecture/REPOSITORY_STRUCTURE_V1_0.md) | Target monorepo layout and dependency direction |
| [Module Boundary v1.0](./architecture/MODULE_BOUNDARY_V1_0.md) | Eight-domain modular-monolith ownership and prohibited dependencies |
| [Local Development v1.0](./engineering/LOCAL_DEVELOPMENT_V1_0.md) | Docker Compose services and environment rules |
| [Quality Gates v1.0](./engineering/QUALITY_GATES_V1_0.md) | Mandatory PR, test, migration, documentation, and security checks |
| [Mission 001A Runtime Validation Report](./engineering/RUNTIME_VALIDATION_REPORT_001A.md) | Docker, PostgreSQL/Redis, environment, CI, and GitHub publication status |
| [Sprint 002 Completion Notes](./planning/SPRINT_002_COMPLETION.md) | Governance/identity implementation, validation evidence, and known activation limits |
| [Sprint 003 Completion Notes](./planning/SPRINT_003_COMPLETION.md) | Customer intelligence implementation and acceptance evidence |
| [Sprint 004 Completion Notes](./planning/SPRINT_004_COMPLETION.md) | Opportunity intelligence implementation and acceptance evidence |
| [Sprint 005 Completion Notes](./planning/SPRINT_005_COMPLETION.md) | Product intelligence implementation and acceptance evidence |
| [Sprint 006 Completion Notes](./planning/SPRINT_006_COMPLETION.md) | Product Truth implementation and acceptance evidence |
| [Sprint 007 Completion Notes](./planning/SPRINT_007_COMPLETION.md) | Supplier intelligence implementation and acceptance evidence |
| [Sprint 008 Completion Notes](./planning/SPRINT_008_COMPLETION.md) | Listing intelligence and GEO implementation and acceptance evidence |
| [Sprint 009 Completion Notes](./planning/SPRINT_009_COMPLETION.md) | Creative strategy implementation and acceptance evidence |
| [Sprint 010 Completion Notes](./planning/SPRINT_010_COMPLETION.md) | Channel strategy and conversion-path implementation and acceptance evidence |
| [Sprint 011 Completion Notes](./planning/SPRINT_011_COMPLETION.md) | Conversation commerce implementation and acceptance evidence |
| [Sprint 012 Completion Notes](./planning/SPRINT_012_COMPLETION.md) | AI sales/support decision implementation and acceptance evidence |
| [Sprint 013 Completion Notes](./planning/SPRINT_013_COMPLETION.md) | Creative intelligence and router implementation and acceptance evidence |
| [Sprint 014 Completion Notes](./planning/SPRINT_014_COMPLETION.md) | CFO/revenue intelligence implementation and acceptance evidence |
| [Sprint 015 Completion Notes](./planning/SPRINT_015_COMPLETION.md) | Executive dashboard and operating committee implementation and acceptance evidence |
| [Sprint 016 Completion Notes](./planning/SPRINT_016_COMPLETION.md) | Commerce execution workflow implementation and acceptance evidence |
| [Sprint 017 Completion Notes](./planning/SPRINT_017_COMPLETION.md) | Market intelligence data-contract implementation and acceptance evidence |
| [Sprint 018 Completion Notes](./planning/SPRINT_018_COMPLETION.md) | Opportunity analysis implementation and acceptance evidence |
| [Sprint 019 Completion Notes](./planning/SPRINT_019_COMPLETION.md) | Market connector contract implementation and acceptance evidence |
| [Sprint 020 Completion Notes](./planning/SPRINT_020_COMPLETION.md) | Reddit connector implementation and validation evidence |
| [Sprint 021 Completion Notes](./planning/SPRINT_021_COMPLETION.md) | Customer voice intelligence implementation and validation evidence |
| [Sprint 022 Completion Notes](./planning/SPRINT_022_COMPLETION.md) | Customer need and product opportunity intelligence implementation evidence |
| [Sprint 023 Completion Notes](./planning/SPRINT_023_COMPLETION.md) | Product commercial risk intelligence implementation and validation evidence |
| [Sprint 024 Completion Notes](./planning/SPRINT_024_COMPLETION.md) | Product economics and margin intelligence implementation and validation evidence |
| [Sprint 025 Completion Notes](./planning/SPRINT_025_COMPLETION.md) | Product launch preparation implementation and validation evidence |
| [Sprint 026 Completion Notes](./planning/SPRINT_026_COMPLETION.md) | AI discovery listing intelligence implementation and validation evidence |
| [Sprint 027 Completion Notes](./planning/SPRINT_027_COMPLETION.md) | Creative asset intelligence implementation and validation evidence |
| [Sprint 028 Completion Notes](./planning/SPRINT_028_COMPLETION.md) | Creative generation workflow implementation and validation evidence |
| [Sprint 029 Completion Notes](./planning/SPRINT_029_COMPLETION.md) | Creative execution adapter implementation and validation evidence |
| [Sprint 030 Completion Notes](./planning/SPRINT_030_COMPLETION.md) | Channel execution and distribution workflow implementation evidence |
| [Sprint 031 Completion Notes](./planning/SPRINT_031_COMPLETION.md) | Customer identity, journey, Customer 360 projection, and advisory value implementation evidence |
| [Sprint 032 Completion Notes](./planning/SPRINT_032_COMPLETION.md) | Strategic account, replenishment, expansion, next-best action, and dashboard implementation evidence |
| [Sprint 033 Completion Notes](./planning/SPRINT_033_COMPLETION.md) | Opportunity-to-launch orchestration and architecture-integration evidence |
| [Sprint 034 Completion Notes](./planning/SPRINT_034_COMPLETION.md) | Production authentication, universal authorization, session revocation, and audit evidence |
| [Sprint 035 Completion Notes](./planning/SPRINT_035_COMPLETION.md) | Provider-neutral AI registry, request, prompt, output-governance, and cost foundation |
| [Sprint 036 Completion Notes](./planning/SPRINT_036_COMPLETION.md) | Secure connector registry, immutable evidence ingestion, normalization, and audit foundation |
| [Sprint 037 Completion Notes](./planning/SPRINT_037_COMPLETION.md) | Marketplace review evidence, normalized customer voice, evidence links, and competitive observations |
| [Sprint 038 Completion Notes](./planning/SPRINT_038_COMPLETION.md) | Evidence-cited research analysis, structured insights, and advisory opportunity briefs |
| [Sprint 039 Completion Notes](./planning/SPRINT_039_COMPLETION.md) | Creative production requests, work items, AI provenance, artifacts, and quality review |
| [Sprint 040 Completion Notes](./planning/SPRINT_040_COMPLETION.md) | Growth experiments, distribution campaigns, performance observations, and learning signals |
| [Sprint 041 Completion Notes](./planning/SPRINT_041_COMPLETION.md) | Customer journeys, intent stages, sales signals, value intelligence, support learning, and projections |
| [Sprint 042 Completion Notes](./planning/SPRINT_042_COMPLETION.md) | Closed-loop observations, hypotheses, conclusions, recommendations, priority, queue review, and projections |
| [Sprint 043 Completion Notes](./planning/SPRINT_043_COMPLETION.md) | Governed provider execution, controls, provenance, structured output, and Research composition |
| [Sprint 044 Completion Notes](./planning/SPRINT_044_COMPLETION.md) | Operational Research Runs, templates, evidence grounding, worker execution, results, and review |
| [MVP Boundary](./product/MVP_BOUNDARY_V1_0.md) | Phase 1 inclusions, exclusions, and scope-control rules |

## Planning and evidence

- [Architecture Gap Analysis](./architecture/ARCHITECTURE_GAP_ANALYSIS_V1_1.md)
- [Implementation Dependency Graph](./architecture/IMPLEMENTATION_DEPENDENCY_GRAPH_V1_1.md)
- [Repository Discovery and Drift](./architecture/REPOSITORY_DISCOVERY_AND_DRIFT.md)
- [Sprint 001 Plan](./planning/SPRINT_001_INTEGRATION_CONTRACTS_CUSTOMER_FOUNDATION.md)
- [Sprint 001 Completion Notes](./planning/SPRINT_001_COMPLETION.md)
- [Sprint 002 Completion Notes](./planning/SPRINT_002_COMPLETION.md)
- [Sprint 003 Completion Notes](./planning/SPRINT_003_COMPLETION.md)
- [Sprint 004 Completion Notes](./planning/SPRINT_004_COMPLETION.md)
- [Sprint 005 Completion Notes](./planning/SPRINT_005_COMPLETION.md)
- [Sprint 006 Completion Notes](./planning/SPRINT_006_COMPLETION.md)
- [Sprint 007 Completion Notes](./planning/SPRINT_007_COMPLETION.md)
- [Sprint 008 Completion Notes](./planning/SPRINT_008_COMPLETION.md)
- [Sprint 009 Completion Notes](./planning/SPRINT_009_COMPLETION.md)
- [Sprint 010 Completion Notes](./planning/SPRINT_010_COMPLETION.md)
- [Sprint 011 Completion Notes](./planning/SPRINT_011_COMPLETION.md)
- [Sprint 012 Completion Notes](./planning/SPRINT_012_COMPLETION.md)
- [Sprint 013 Completion Notes](./planning/SPRINT_013_COMPLETION.md)
- [Sprint 014 Completion Notes](./planning/SPRINT_014_COMPLETION.md)
- [Sprint 015 Completion Notes](./planning/SPRINT_015_COMPLETION.md)
- [Sprint 016 Completion Notes](./planning/SPRINT_016_COMPLETION.md)
- [Sprint 017 Completion Notes](./planning/SPRINT_017_COMPLETION.md)
- [Sprint 018 Completion Notes](./planning/SPRINT_018_COMPLETION.md)
- [Sprint 019 Completion Notes](./planning/SPRINT_019_COMPLETION.md)
- [Sprint 020 Completion Notes](./planning/SPRINT_020_COMPLETION.md)
- [Sprint 021 Completion Notes](./planning/SPRINT_021_COMPLETION.md)
- [Sprint 022 Completion Notes](./planning/SPRINT_022_COMPLETION.md)
- [Sprint 023 Completion Notes](./planning/SPRINT_023_COMPLETION.md)
- [Sprint 024 Completion Notes](./planning/SPRINT_024_COMPLETION.md)
- [Sprint 025 Completion Notes](./planning/SPRINT_025_COMPLETION.md)
- [Sprint 026 Completion Notes](./planning/SPRINT_026_COMPLETION.md)
- [Sprint 027 Completion Notes](./planning/SPRINT_027_COMPLETION.md)
- [Sprint 028 Completion Notes](./planning/SPRINT_028_COMPLETION.md)
- [Sprint 029 Completion Notes](./planning/SPRINT_029_COMPLETION.md)
- [Sprint 030 Completion Notes](./planning/SPRINT_030_COMPLETION.md)
- [Sprint 031 Completion Notes](./planning/SPRINT_031_COMPLETION.md)
- [Sprint 032 Completion Notes](./planning/SPRINT_032_COMPLETION.md)
- [Sprint 033 Completion Notes](./planning/SPRINT_033_COMPLETION.md)
- [Sprint 034 Completion Notes](./planning/SPRINT_034_COMPLETION.md)
- [Sprint 035 Completion Notes](./planning/SPRINT_035_COMPLETION.md)
- [Sprint 036 Completion Notes](./planning/SPRINT_036_COMPLETION.md)
- [Sprint 037 Completion Notes](./planning/SPRINT_037_COMPLETION.md)
- [Sprint 038 Completion Notes](./planning/SPRINT_038_COMPLETION.md)
- [Sprint 039 Completion Notes](./planning/SPRINT_039_COMPLETION.md)
- [Sprint 040 Completion Notes](./planning/SPRINT_040_COMPLETION.md)
- [Sprint 041 Completion Notes](./planning/SPRINT_041_COMPLETION.md)
- [Sprint 042 Completion Notes](./planning/SPRINT_042_COMPLETION.md)
- [Sprint 043 Completion Notes](./planning/SPRINT_043_COMPLETION.md)
- [Sprint 044 Completion Notes](./planning/SPRINT_044_COMPLETION.md)
- [Sprint 045 Completion Notes](./planning/SPRINT_045_COMPLETION.md)
- [Sprint 046 Completion Notes](./planning/SPRINT_046_COMPLETION.md)
- [Sprint 047 Completion Notes](./planning/SPRINT_047_COMPLETION.md)
- [Sprint 048 Completion Notes](./planning/SPRINT_048_COMPLETION.md)
- [Sprint 049 Completion Notes](./planning/SPRINT_049_COMPLETION.md)
- [Sprint 050 Completion Notes](./planning/SPRINT_050_COMPLETION.md)
- [Sprint 051 Completion Notes](./planning/SPRINT_051_COMPLETION.md)
- [Sprint 052 Completion Notes](./planning/SPRINT_052_COMPLETION.md)
- [Sprint 053 Completion Notes](./planning/SPRINT_053_COMPLETION.md)
- [Sprint 054 Completion Notes](./planning/SPRINT_054_COMPLETION.md)
- [Sprint 055 Completion Notes](./planning/SPRINT_055_COMPLETION.md)
- [Sprint 056 Completion Notes](./planning/SPRINT_056_COMPLETION.md)
- [Sprint 057 Completion Notes](./planning/SPRINT_057_COMPLETION.md)
- [Sprint 058 Completion Notes](./planning/SPRINT_058_COMPLETION.md)
- [Sprint 059 Completion Notes](./planning/SPRINT_059_COMPLETION.md)
- [Revenue Validation Experiment Foundation v1.0](./architecture/REVENUE_VALIDATION_EXPERIMENT_FOUNDATION_V1_0.md)
- [Sprint 060 Completion Notes](./planning/SPRINT_060_COMPLETION.md)
- [First Revenue Machine Prospect Discovery Foundation v1.0](./architecture/FIRST_REVENUE_MACHINE_PROSPECT_DISCOVERY_FOUNDATION_V1_0.md)
- [Sprint 061 Completion Notes](./planning/SPRINT_061_COMPLETION.md)
- [Discovery Automation Layer v1.0](./architecture/DISCOVERY_AUTOMATION_LAYER_V1_0.md)
- [Sprint 062 Completion Notes](./planning/SPRINT_062_COMPLETION.md)
- [GrowthOS Revenue Machine Completion v1.0](./architecture/GROWTHOS_REVENUE_MACHINE_COMPLETION_V1_0.md)
- [Sprint 063 Completion Notes](./planning/SPRINT_063_COMPLETION.md)
- [Revenue Launch Foundation v1.0](./architecture/REVENUE_LAUNCH_FOUNDATION_V1_0.md)
- [Sprint 064 Completion Notes](./planning/SPRINT_064_COMPLETION.md)
- [Revenue Experiment Operation Layer v1.0](./architecture/REVENUE_EXPERIMENT_OPERATION_LAYER_V1_0.md)
- [Sprint 065 Completion Notes](./planning/SPRINT_065_COMPLETION.md)
- [Live Revenue Experiment Support Foundation v1.0](./architecture/LIVE_REVENUE_EXPERIMENT_SUPPORT_FOUNDATION_V1_0.md)
- [Sprint 066 Completion Notes](./planning/SPRINT_066_COMPLETION.md)
- [Growth OS Founder Operability v1.0](./architecture/GROWTH_OS_FOUNDER_OPERABILITY_V1_0.md)
- [Growth OS Daily Discovery and Qualification v1.0](./architecture/GROWTH_OS_DAILY_DISCOVERY_QUALIFICATION_V1_0.md)
- [Sprint 069 Completion Notes](./planning/SPRINT_069_COMPLETION.md)
- [Commerce Intelligence Control Plane v1.0](./architecture/COMMERCE_INTELLIGENCE_CONTROL_PLANE_V1_0.md)
- [Sprint 070 Completion Notes](./planning/SPRINT_070_COMPLETION.md)
- [Intelligence Provenance and Committee Packet v1.0](./architecture/INTELLIGENCE_PROVENANCE_COMMITTEE_PACKET_V1_0.md)
- [Sprint 071 Completion Notes](./planning/SPRINT_071_COMPLETION.md)
- [Governed Product Promotion and Product Truth v1.0](./architecture/GOVERNED_PRODUCT_PROMOTION_PRODUCT_TRUTH_V1_0.md)
- [Sprint 072 Completion Notes](./planning/SPRINT_072_COMPLETION.md)

The architecture and governance documents remain controlling contracts. Sprint completion notes distinguish implemented foundations from production activation.
