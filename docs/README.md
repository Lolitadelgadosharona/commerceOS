# Commerce OS Architecture and Governance Index

Status: architecture/governance baseline with Sprint 013 creative intelligence router foundation

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

The architecture and governance documents remain controlling contracts. Sprint completion notes distinguish implemented foundations from production activation.
