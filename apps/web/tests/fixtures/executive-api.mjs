import { createServer } from "node:http";

const organizationId = "11111111-1111-4111-8111-111111111111";
const userId = "22222222-2222-4222-8222-222222222222";
const marketId = "77777777-7777-4777-8777-777777777777";
const candidateId = "88888888-8888-4888-8888-888888888888";
const approvalId = "99999999-9999-4999-8999-999999999999";
const growthExperimentId = "20202020-2020-4020-8020-202020202020";
const growthCandidateId = "21212121-2121-4121-8121-212121212121";
const growthProspectId = "22222222-3333-4222-8222-222222222222";
const marketSignalId = "30303030-3030-4030-8030-303030303030";
const productHypothesisId = "31313131-3131-4131-8131-313131313131";
const promotionId = "51515151-5151-4151-8151-515151515151";
const promotionApprovalId = "52525252-5252-4252-8252-525252525252";
const productRecordId = "53535353-5353-4353-8353-535353535353";
const brandId = "54545454-5454-4454-8454-545454545454";
let scenario = "success";
let approvalStatus = "pending";
let promotionRequested = false;
let promotionApproved = false;
let productCreated = false;
let buildRelationshipExecuted = false;
let supplierCandidatePromoted = false;

const base = {
  organization_id: organizationId,
  version: 1,
  created_at: "2026-08-24T12:00:00Z",
  updated_at: "2026-08-24T12:00:00Z",
};
const metric = (id, metric_type, metric_name, value, unit, source_domain) => ({
  ...base,
  id,
  metric_type,
  metric_name,
  value,
  unit,
  source_domain,
  period_id: "33333333-3333-4333-8333-333333333333",
});
const signal = (id, domain, severity, title, impact) => ({
  ...base,
  id,
  domain,
  severity,
  title,
  description: title,
  impact,
  recommendation: "Review the source evidence.",
  status: "open",
});
const decision = {
  ...base,
  id: "66666666-6666-4666-8666-666666666666",
  title: "Investment decision: Seasonal pet cooling mat",
  domain: "decision",
  reason: "Human review is required before action.",
  priority: "high",
  required_action: "approve",
  status: "pending",
  approval_request_id: approvalId,
};
const marketOpportunity = {
  ...base,
  id: marketId,
  title: "Seasonal pet cooling mat",
  description: "Owners report recurring heat discomfort during summer travel.",
  category: "pet",
  market: "consumer",
  geography: "US",
  trigger_type: "seasonal_event",
  timing_window: "summer",
  status: "qualified",
  confidence_score: 0.82,
};
const candidateOpportunity = {
  ...base,
  id: candidateId,
  discovery_run_id: null,
  title: "Travel hydration reminder",
  category: "pet",
  problem_statement: "Owners forget hydration during long journeys.",
  customer_segment: "Traveling pet owners",
  opportunity_description:
    "An evidence-backed product direction for travel hydration.",
  market_context: "Recurring customer voice signals.",
  evidence_summary: "Two reviewed demand signals.",
  evidence_references: [{ type: "customer_pain", id: "signal-1" }],
  solution_direction: "Portable reminder product",
  customer_language: ["I forget water on long drives"],
  confidence_score: 0.74,
  risk_summary: ["Adoption uncertainty"],
  open_questions: [],
  missing_evidence: ["Marketplace validation"],
  advisory_score: 74,
  status: "under_review",
  methodology_version: "deterministic-demand-opportunity-v1",
  decision_queue_item_id: null,
};
const approval = () => ({
  ...base,
  id: approvalId,
  project_id: null,
  requester_id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
  object_type: "market_opportunity",
  object_id: marketId,
  requested_action: "approve_investment",
  reason: "Evidence and economics require human investment review.",
  status: approvalStatus,
  approver_id: approvalStatus === "pending" ? null : userId,
  decision_time: approvalStatus === "pending" ? null : "2026-08-24T13:00:00Z",
  decision_reason:
    approvalStatus === "pending"
      ? null
      : "Evidence supports a controlled next step.",
});
const marketScore = {
  ...base,
  id: "12121212-1212-4212-8212-121212121212",
  opportunity_id: marketId,
  demand_score: 82,
  pain_score: 78,
  trend_score: 75,
  margin_score: 68,
  competition_score: 56,
  ip_risk_score: 22,
  dispute_risk_score: 18,
  overall_score: 72.4,
  formula_version: "opportunity-score-v1",
};
const marketRisk = {
  ...base,
  id: "13131313-1313-4313-8313-131313131313",
  opportunity_id: marketId,
  risk_type: "policy",
  severity: "medium",
  description: "Platform policy evidence requires validation.",
  status: "open",
};
const marketEvidence = {
  ...base,
  id: "14141414-1414-4414-8414-141414141414",
  opportunity_id: marketId,
  source_type: "customer_signal",
  source_reference: "customer-signal:heat-1",
  evidence_summary: "Owners report pet heat discomfort during summer travel.",
  confidence_score: 0.85,
};
const candidateEvidence = {
  ...base,
  id: "15151515-1515-4515-8515-151515151515",
  opportunity_candidate_id: candidateId,
  demand_signal_id: "16161616-1616-4616-8616-161616161616",
  evidence_type: "customer_pain",
  evidence_summary: "Hydration is forgotten during long journeys.",
  contribution: "12 observations; customer voice",
  confidence: 0.74,
};
const candidateAssessment = {
  ...base,
  id: "17171717-1717-4717-8717-171717171717",
  opportunity_candidate_id: candidateId,
  demand_strength: "medium",
  signal_diversity: 2,
  market_timing: "Travel season",
  confidence: 0.74,
  risks: ["Adoption uncertainty"],
  missing_information: ["Marketplace validation"],
  assumptions: ["Observed pain generalizes beyond the sample"],
};
const growthExperiment = {
  ...base,
  id: growthExperimentId,
  name: "Beauty Growth Experiment 001",
  description: "Validate a founder-led visibility offer.",
  target_segment: "Independent beauty studios",
  offer_type: "growth_visibility_audit",
  message_strategy: "Evidence first",
  status: "active",
  segment: "Beauty",
  target_count: 6,
  start_date: "2026-08-25",
};
const growthCandidate = {
  ...base,
  id: growthCandidateId,
  business_name: "Rose & Brow Studio",
  website: "https://example.test",
  location: "Los Angeles",
  category: "Beauty",
  source_reference: "https://example.test",
  confidence: 0.8,
  status: "qualified",
};
const growthProspect = {
  ...base,
  id: growthProspectId,
  business_name: "Rose & Brow Studio",
  website: "https://example.test",
  email: null,
  location: "Los Angeles",
  industry: "Beauty",
  business_type: "studio",
  source: "manual_import",
  status: "qualified",
  source_candidate_id: growthCandidateId,
};
const growthAssignment = {
  ...base,
  id: "23232323-2323-4323-8323-232323232323",
  experiment_id: growthExperimentId,
  prospect_id: growthProspectId,
  assigned_offer: "Visibility diagnosis",
  assigned_message: "Founder review",
  result_status: "pending",
};
const growthEvidence = {
  ...base,
  id: "24242424-2424-4424-8424-242424242424",
  prospect_id: growthProspectId,
  evidence_type: "website",
  source_url: "https://example.test/services",
  observation: "Booking action is not visible on the service page.",
  confidence: 0.85,
  collected_at: "2026-08-25T10:00:00Z",
};
const marketSource = {
  ...base,
  id: "32323232-3232-4232-8232-323232323232",
  name: "Reviewed customer research",
  platform: "reddit",
  source_type: "community",
  access_method: "manual",
  reliability_score: 0.8,
  status: "active",
};
const marketSignal = {
  ...base,
  id: marketSignalId,
  source_id: marketSource.id,
  region: "US",
  category: "pet",
  signal_type: "customer_pain",
  title: "Pet heat discomfort is rising",
  description:
    "Owners describe recurring heat discomfort during summer travel.",
  trend_direction: "rising",
  confidence_score: 0.82,
  observed_at: "2026-08-23T12:00:00Z",
  status: "validated",
};
const marketSignalEvidence = {
  ...base,
  id: "33333333-4444-4333-8333-333333333333",
  signal_id: marketSignalId,
  evidence_type: "reference",
  content_reference: "research:pet-heat-2026",
  strength_score: 0.86,
  captured_at: "2026-08-23T12:00:00Z",
};
const marketCluster = {
  ...base,
  id: "34343434-3434-4434-8434-343434343434",
  name: "Summer pet comfort",
  category: "pet",
  confidence: 0.78,
  impact_score: 72,
};
const demandSignal = {
  ...base,
  id: "35353535-3535-4535-8535-353535353535",
  source_domain: "intelligence",
  source_reference_id: marketSignalId,
  source_type: "research_analysis",
  source_reference: "research:pet-heat-2026",
  collection_method: "manual",
  evidence_origin: "reviewed research",
  confidence_basis: "Two corroborating observations",
  customer_segment: "Traveling pet owners",
  category: "pet comfort",
  problem_statement: "Pets experience heat discomfort during travel.",
  customer_language: "My dog overheats in the car",
  frequency: 12,
  confidence: 0.8,
  evidence_count: 2,
  status: "approved",
};
const demandEvidence = {
  ...base,
  id: "36363636-3636-4636-8636-363636363636",
  demand_signal_id: demandSignal.id,
  source_type: "research_analysis",
  source_id: marketSource.id,
  source_reference: "research:pet-heat-2026",
  evidence_text: "Owners report recurring summer heat discomfort.",
};
const demandDashboard = {
  organization_id: organizationId,
  draft_signals: 0,
  signals_in_review: 0,
  approved_signals: 1,
  source_overview: [
    {
      source_type: "research_analysis",
      signal_count: 1,
      evidence_count: 2,
      average_confidence: 0.8,
      signal_percentage: 100,
    },
  ],
  emerging_categories: [
    {
      category: "pet comfort",
      signal_count: 1,
      total_frequency: 12,
      average_confidence: 0.8,
    },
  ],
  customer_pain_clusters: [],
  emerging_demand_themes: [],
  predictive_indicators: [],
  emerging_customer_pains: [
    {
      demand_signal_id: demandSignal.id,
      category: "pet comfort",
      customer_segment: "Traveling pet owners",
      problem_statement: demandSignal.problem_statement,
      frequency: 12,
      confidence: 0.8,
      evidence_count: 2,
      source_type: "research_analysis",
      evidence_sources: ["research:pet-heat-2026"],
      source_conversation_ids: [],
    },
  ],
};
const productHypothesis = {
  ...base,
  id: productHypothesisId,
  opportunity_id: marketId,
  name: "Portable pet cooling mat",
  description:
    "A product hypothesis responding to observed travel heat discomfort.",
  customer_problem: "Pets overheat during summer travel.",
  solution_description: "A portable reusable cooling surface.",
  target_customer: "Traveling pet owners",
  target_market: "US pet accessories",
  status: "evaluating",
  confidence_score: 0.76,
};
const productEconomics = {
  ...base,
  id: "37373737-3737-4737-8737-373737373737",
  product_id: productHypothesisId,
  selling_price: "39.00",
  estimated_product_cost: "12.00",
  estimated_shipping_cost: "5.00",
  payment_cost: "1.20",
  estimated_marketing_cost: "8.00",
  contribution_margin: "12.80",
  margin_percentage: "32.82",
  currency: "USD",
};
const productSupplier = {
  ...base,
  id: "38383838-3838-4838-8838-383838383838",
  product_id: productHypothesisId,
  source_type: "manual",
  supplier_reference: "supplier-research:cooling-1",
  estimated_cost: "12.00",
  minimum_order_quantity: 100,
  lead_time: "30 days",
  quality_notes: "Material testing is still required.",
  risk_level: "medium",
};
const canonicalSupplierId = "63636363-6363-4363-8363-636363636363";
const canonicalSupplier = {
  ...base,
  id: canonicalSupplierId,
  name: "Atlantic Care Manufacturing",
  source_type: "manufacturer",
  country: "Portugal",
  capabilities: ["Cooling textiles", "Private label packaging"],
  certifications: ["ISO 9001"],
  status: "evaluating",
};
const canonicalSupplierMatch = {
  ...base,
  id: "54545454-5454-4454-8454-545454545454",
  product_id: productRecordId,
  supplier_id: canonicalSupplierId,
  match_score: 84,
  recommended: true,
  reason: "Material capability fits current Product Truth.",
};
const canonicalSupplierQuote = {
  ...base,
  id: "55555555-5555-4555-8555-555555555555",
  supplier_id: canonicalSupplierId,
  product_id: productRecordId,
  currency: "USD",
  unit_price: "11.5000",
  minimum_order_quantity: 100,
  price_tiers: [],
  sample_cost: "25.0000",
  tooling_cost: null,
  packaging_cost: "0.0000",
  incoterm: "EXW",
  payment_terms: "30% deposit; 70% before shipment",
  lead_time: "30 days",
  quote_date: "2026-08-30",
  valid_until: "2026-08-31",
  classification: "quoted",
  source: "supplier quotation",
  confidence: 0.86,
  evidence_reference: "quote:atlantic-1",
  notes: null,
};
const canonicalSupplierEvidence = {
  ...base,
  id: "56565656-5656-4656-8656-565656565656",
  supplier_id: canonicalSupplierId,
  field_name: "production_capacity",
  value: "5000 units / month",
  classification: "supplier_claimed",
  source: "supplier questionnaire",
  confidence: 0.68,
  as_of: "2026-08-30T12:00:00Z",
  evidence_reference: "questionnaire:atlantic-1",
  notes: "Verification required before purchase planning.",
};
const canonicalQualification = {
  organization_id: organizationId,
  supplier_id: canonicalSupplierId,
  product_id: productRecordId,
  ready: true,
  next_action: "Verify compliance evidence against current Product Truth.",
  readiness: [{ code: "unknown_compliance", severity: "warning", status: "unknown", message: "Verify compliance evidence.", references: [] }],
  dimensions: [
    { dimension: "product_fit", status: "pass", evidence: [canonicalSupplierMatch.id], confidence: 0.84, gaps: [], risk: null },
    { dimension: "commercial_fit", status: "pass", evidence: [canonicalSupplierQuote.id], confidence: 1, gaps: [], risk: null },
    { dimension: "compliance", status: "unknown", evidence: [], confidence: null, gaps: ["Verify compliance evidence against current Product Truth."], risk: null },
  ],
};
const canonicalSupplierDetail = {
  supplier: canonicalSupplier,
  products: [canonicalSupplierMatch],
  evidence: [canonicalSupplierEvidence],
  quotes: [canonicalSupplierQuote],
  evaluations: [],
  risks: [],
  approved_relationships: [],
  qualifications: [canonicalQualification],
  next_action: canonicalQualification.next_action,
};
const productRisk = {
  ...base,
  id: "39393939-3939-4939-8939-393939393939",
  product_id: productHypothesisId,
  risk_type: "quality",
  severity: "medium",
  description: "Cooling duration claims require evidence.",
  status: "open",
};
const productScore = {
  ...base,
  id: "40404040-4040-4040-8040-404040404040",
  product_id: productHypothesisId,
  opportunity_score: 72,
  margin_score: 64,
  risk_score: 58,
  competition_score: 55,
  confidence_score: 76,
  overall_score: 66.4,
  formula_version: "product-investment-v1",
};
const economicInputs = [
  {
    ...base,
    id: "65656565-6565-4565-8565-656565656565",
    product_economics_id: productEconomics.id,
    supplier_quote_id: canonicalSupplierQuote.id,
    metric: "estimated_product_cost",
    value: "11.5000",
    classification: "quoted",
    source: "supplier quotation",
    confidence: 0.86,
    as_of: "2026-08-30T12:00:00Z",
    evidence_reference: "quote:atlantic-1",
    notes: "Supplier quote evidence; not Finance actual.",
  },
  {
    ...base,
    id: "41414141-4141-4141-8141-414141414141",
    product_economics_id: productEconomics.id,
    supplier_quote_id: null,
    metric: "estimated_shipping_cost",
    value: "0.0000",
    classification: "quoted",
    source: "supplier quote",
    confidence: 0.9,
    as_of: "2026-08-23T12:00:00Z",
    evidence_reference: "supplier:shipping-1",
    notes: null,
  },
  {
    ...base,
    id: "42424242-4242-4242-8242-424242424242",
    product_economics_id: productEconomics.id,
    supplier_quote_id: null,
    metric: "customer_acquisition_cost",
    value: null,
    classification: "unknown",
    source: "not researched",
    confidence: null,
    as_of: null,
    evidence_reference: null,
    notes: "Missing before decision",
  },
];
const buildRelationship = () => ({
  id: "66666666-7777-4666-8666-666666666666",
  supplier_id: canonicalSupplierId,
  approval_request_id: promotionApprovalId,
  role: "primary",
  status: buildRelationshipExecuted ? "approved" : "pending",
});
const buildPackage = () => ({
  organization_id: organizationId,
  product_id: productRecordId,
  product_name: "Portable cooling mat",
  product_truth_id: "67676767-6767-4767-8767-676767676767",
  product_truth_version: 1,
  specifications: { material: "cooling textile", dimensions: "60 × 40 cm" },
  requirements: [],
  approved_suppliers: buildRelationshipExecuted ? [canonicalSupplierId] : [],
  supplier_relationships: [buildRelationship()],
  supplier_fit: [
    { requirement: "Material", required_value: "cooling textile", supplier_response: "cooling textile", evidence: [canonicalSupplierEvidence.id], status: "pass", gap: null },
    { requirement: "Dimensions", required_value: "60 × 40 cm", supplier_response: null, evidence: [], status: "unknown", gap: "Supplier dimension evidence is UNKNOWN." },
  ],
  samples: [{ ...base, id: "68686868-6868-4868-8868-686868686868", supplier_id: canonicalSupplierId, sample_identifier: "SAMPLE-001", status: "received", review_status: "unknown", review_dimensions: {}, evidence_reference: "photo:sample-001" }],
  validations: [{ ...base, id: "69696969-6969-4969-8969-696969696969", supplier_id: canonicalSupplierId, sample_id: "68686868-6868-4868-8868-686868686868", validation_type: "sample_observation", classification: "human_verified", result: "pass", observations: "Material matches the approved specification.", evidence_reference: "review:sample-001" }],
  quote_ids: [canonicalSupplierQuote.id],
  quote_economics_ids: [economicInputs[0].id],
  blockers: buildRelationshipExecuted ? [] : [{ code: "approved_supplier", severity: "blocker", message: "Execute the approved supplier relationship.", references: [buildRelationship().id] }],
  warnings: [
    { code: "expired_quote", severity: "warning", message: "A supplier quote has expired and should be refreshed.", references: [canonicalSupplierQuote.id] },
    { code: "single_supplier", severity: "warning", message: "Only one supplier is approved; this does not block Build Ready.", references: [] },
  ],
  status: buildRelationshipExecuted ? "conditional" : "not_ready",
  next_action: buildRelationshipExecuted ? "Review Build Package warnings." : "Complete governed supplier selection execution.",
  origin_opportunity_id: marketId,
  origin_hypothesis_id: productHypothesisId,
});
const listingVersion = {
  ...base,
  id: "75757575-7575-4575-8575-757575757575",
  product_id: productRecordId,
  product_truth_id: "67676767-6767-4767-8767-676767676767",
  product_truth_version: 1,
  listing_version: 1,
  status: "draft",
  title: "Portable cooling mat",
  subtitle: "Evidence-backed comfort for summer travel",
  summary: "A reusable cooling surface for traveling pets.",
  description: "A portable cooling mat based on approved Product Truth.",
  customer_problem: "Owners report recurring pet heat discomfort during summer travel.",
  solution: "A portable reusable cooling surface.",
  features: ["Cooling textile", "Reusable"],
  benefits: ["Supports a more comfortable travel setup"],
  specifications: { material: "cooling textile", dimensions: "60 × 40 cm" },
  use_cases: ["Summer travel"],
  whats_included: ["Cooling mat"],
  warnings: ["Use only as directed"],
  care_usage: "Follow approved care instructions.",
  shipping_facts: null,
  return_facts: null,
  risk_reversal: null,
  seo_title: "Portable pet cooling mat",
  meta_description: "Evidence-backed reusable cooling mat for pet travel.",
  slug_suggestion: "portable-pet-cooling-mat",
  primary_topic: "pet cooling mat",
  secondary_topics: ["summer pet travel"],
  structured_attributes: { material: "cooling textile", dimensions: "60 × 40 cm" },
  commercial_price: "39.00",
  currency: "USD",
  price_status: "approved",
  change_reason: "Initial governed draft",
  approval_request_id: null,
  created_by: userId,
  approved_by: null,
  approved_at: null,
};
const listingPackage = {
  organization_id: organizationId,
  product_id: productRecordId,
  product_name: "Portable cooling mat",
  product_truth_id: listingVersion.product_truth_id,
  product_truth_version: 1,
  listing: listingVersion,
  allowed_facts: [
    { fact: "Cooling textile", source: "ProductTruth v1", evidence: [listingVersion.product_truth_id], can_use: true, restrictions: [], notes: "Approved Product Truth feature." },
    { fact: "Guaranteed all-day cooling", source: "ProductTruth v1", evidence: [listingVersion.product_truth_id], can_use: false, restrictions: ["restricted_claim"], notes: "Must not be used." },
  ],
  claim_review: [
    { id: "76767676-7676-4676-8676-767676767676", claim: "Cooling textile", claim_type: "product_fact", support_status: "supported", sources: [`product_truth:${listingVersion.product_truth_id}`], risk_level: "standard", policy_requirement: null, human_review_needed: false, blocking: false },
    { id: "77777777-8888-4777-8777-777777777777", claim: "Clinically proven", claim_type: "health_or_safety", support_status: "unknown", sources: [], risk_level: "high", policy_requirement: "Explicit policy and strong evidence required.", human_review_needed: true, blocking: true },
  ],
  faqs: [{ ...base, id: "78787878-7878-4878-8878-787878787878", listing_version_id: listingVersion.id, question: "How should I care for it?", answer: "Follow approved care instructions.", answer_status: "supported_answer", evidence_reference: listingVersion.product_truth_id }],
  blockers: [{ code: "claim_unknown", severity: "blocker", message: "Claim is unknown: Clinically proven", references: ["77777777-8888-4777-8777-777777777777"] }],
  warnings: [{ code: "shipping_policy", severity: "warning", message: "Shipping policy is not yet recorded.", references: [] }],
  status: "not_ready",
  product_truth_fresh: true,
  build_status: "conditional",
  structured_data_ready: true,
  next_action: "Remove or support the unknown claim.",
  origin_opportunity_id: marketId,
  origin_hypothesis_id: productHypothesisId,
};
const shopifyProjection = { status: "draft_concept", external_id: null, title: listingVersion.title, description: listingVersion.description, product_type: "pet", vendor: "Commerce OS", price: "39.00", currency: "USD", seo_title: listingVersion.seo_title, seo_description: listingVersion.meta_description, metafield_candidates: listingVersion.structured_attributes, missing_fields: ["shipping"], publication_authorized: false };
const promotionReadiness = {
  organization_id: organizationId,
  product_hypothesis_id: productHypothesisId,
  opportunity_id: marketId,
  ready: true,
  items: [
    {
      code: "investment_approval",
      severity: "blocker",
      status: "ready",
      message: "Opportunity investment approval is recorded.",
      references: [approvalId],
    },
    {
      code: "critical_economics",
      severity: "blocker",
      status: "ready",
      message: "Critical economics inputs are present.",
      references: [productEconomics.id],
    },
    {
      code: "legacy_economics_provenance",
      severity: "warning",
      status: "warning",
      message:
        "Economic value exists but source provenance is not established.",
      references: [productEconomics.id],
    },
    {
      code: "supplier_assumptions",
      severity: "warning",
      status: "ready",
      message: "Supplier assumptions are recorded.",
      references: [productSupplier.id],
    },
  ],
};
const promotion = () =>
  promotionRequested
    ? {
        ...base,
        id: promotionId,
        product_hypothesis_id: productHypothesisId,
        opportunity_id: marketId,
        brand_id: brandId,
        approval_request_id: promotionApprovalId,
        product_id: productCreated ? productRecordId : null,
        requested_by: userId,
        promoted_by: productCreated ? userId : null,
        promoted_at: productCreated ? "2026-08-24T14:00:00Z" : null,
        status: productCreated ? "promoted" : "pending",
      }
    : null;
const promotionApproval = () => ({
  ...base,
  id: promotionApprovalId,
  project_id: null,
  requester_id: userId,
  object_type: "product_hypothesis",
  object_id: productHypothesisId,
  requested_action: "product.promote",
  reason: "Promote the evidence-backed hypothesis.",
  status: promotionApproved ? "approved" : "pending",
  approver_id: promotionApproved
    ? "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    : null,
  decision_time: promotionApproved ? "2026-08-24T13:30:00Z" : null,
  decision_reason: promotionApproved
    ? "Ready for governed Build ownership."
    : null,
});
const productRecord = {
  ...base,
  id: productRecordId,
  name: productHypothesis.name,
  description: productHypothesis.solution_description,
  category: "pet",
  brand_id: brandId,
  status: "draft",
};

const memo = {
  opportunity_id: marketId,
  organization_id: organizationId,
  summary: {
    title: marketOpportunity.title,
    description: marketOpportunity.description,
    why_now: "summer",
    assessment: {
      overall_score: 72.4,
      explanation: "Demand evidence is credible but incomplete.",
    },
    report: {
      status: "presented",
      summary: "Proceed only after policy and economics review.",
      risk_summary: "Platform policy evidence remains incomplete.",
    },
  },
  evidence: [marketEvidence],
  conclusions: {
    commercial_viability: {
      classification: "derived",
      value: { recommendation: "test", adjusted_score: 68 },
    },
    risk: {
      classification: "derived",
      value: { risk_level: "medium", risk_score: 32 },
    },
    economic_assumptions: {
      classification: "estimated",
      value: { product_cost: 12, shipping_cost: 5, currency: "USD" },
    },
    profit_scenarios: {
      classification: "estimated",
      value: { scenario: "base", margin: 0.35 },
    },
    risk_adjusted_profitability: {
      classification: "derived",
      value: { final_score: 64, recommendation: "review" },
    },
  },
  missing_evidence: ["Customer evidence is required"],
  confidence: 0.58,
  recommended_decision: "hold",
};
const readiness = {
  opportunity_id: marketId,
  overall_status: "missing",
  blocking_reasons: ["Customer evidence is required"],
  categories: [
    {
      category: "market_evidence",
      status: "ready",
      reason: "Available",
      references: [marketEvidence.id],
      blocking: true,
    },
    {
      category: "customer_evidence",
      status: "missing",
      reason: "Customer evidence is required",
      references: [],
      blocking: true,
    },
    {
      category: "economics",
      status: "ready",
      reason: "Available",
      references: [],
      blocking: true,
    },
    {
      category: "governance",
      status: "ready",
      reason: "Available",
      references: [],
      blocking: true,
    },
  ],
};
const committeePacket = {
  organization_id: organizationId,
  opportunity: marketOpportunity,
  market_evidence: [marketEvidence],
  market_signals: [{ signal: marketSignal, evidence: [marketSignalEvidence] }],
  source_diversity: 2,
  product_theses: [
    {
      hypothesis: productHypothesis,
      economics: productEconomics,
      economic_inputs: economicInputs,
      supplier_candidates: [productSupplier],
      risks: [productRisk],
      investment_score: productScore,
      product_truth_relationship_status: "no_canonical_relationship",
      promotion_readiness: promotionReadiness,
      promotion: null,
      promotion_approval: null,
    },
  ],
  investment_memo: memo,
  approval: approval(),
  decision_queue: decision,
  launch_readiness: readiness,
  supporting_case: [marketEvidence.evidence_summary, marketSignal.title],
  opposing_case: [productRisk.description, "Customer evidence is required"],
  missing_evidence: ["Customer evidence is required"],
  decision_quality_warnings: [
    {
      code: "critical_economics_unknown",
      severity: "blocking",
      message:
        "Critical economic inputs are missing or UNKNOWN: customer_acquisition_cost",
    },
    {
      code: "legacy_economics_provenance",
      severity: "warning",
      message:
        "Economic value exists but source provenance is not established.",
    },
  ],
  unavailable_sections: ["product_truth_comparison"],
};

function dashboard(view) {
  if (scenario === "empty")
    return {
      organization_id: organizationId,
      view,
      metrics: [],
      signals: [],
      decisions: [],
      strategic_account_indicators: {},
    };
  const views = {
    "executive-overview": {
      metrics: [
        metric(
          "44444444-4444-4444-8444-444444444441",
          "customer",
          "Active customer signals",
          7,
          "signals",
          "intelligence",
        ),
      ],
      signals: [
        signal(
          "55555555-5555-4555-8555-555555555551",
          "operations",
          "warning",
          "Delivery concerns rising",
          "Customer trust may decline.",
        ),
      ],
      decisions: [decision],
    },
    "financial-health": {
      metrics: [
        metric(
          "44444444-4444-4444-8444-444444444442",
          "revenue",
          "Observed revenue",
          12500,
          "USD",
          "finance",
        ),
        metric(
          "44444444-4444-4444-8444-444444444443",
          "profit",
          "Contribution profit",
          4100,
          "USD",
          "finance",
        ),
      ],
      signals: [],
      decisions: [],
    },
    "product-opportunities": {
      metrics: [
        metric(
          "44444444-4444-4444-8444-444444444444",
          "product",
          "Reviewed product opportunities",
          3,
          "candidates",
          "decision",
        ),
      ],
      signals: [
        signal(
          "55555555-5555-4555-8555-555555555552",
          "intelligence",
          "info",
          "Customer-backed opportunity ready",
          "Evidence is ready for human review.",
        ),
      ],
      decisions: [],
    },
    "risk-overview": {
      metrics: [
        metric(
          "44444444-4444-4444-8444-444444444445",
          "risk",
          "Open risk observations",
          2,
          "signals",
          "decision",
        ),
      ],
      signals: [
        signal(
          "55555555-5555-4555-8555-555555555553",
          "finance",
          "critical",
          "Margin compression",
          "Contribution profit is at risk.",
        ),
      ],
      decisions: [decision],
    },
    "need-your-decision": { metrics: [], signals: [], decisions: [decision] },
  };
  return {
    organization_id: organizationId,
    view,
    ...(views[view] ?? { metrics: [], signals: [], decisions: [] }),
    strategic_account_indicators: {},
  };
}

createServer((request, response) => {
  if (request.method === "POST" && request.url?.startsWith("/__scenario/")) {
    scenario = request.url.split("/").at(-1) ?? "success";
    approvalStatus = scenario === "promotion" ? "approved" : "pending";
    promotionRequested = false;
    promotionApproved = false;
    productCreated = false;
    buildRelationshipExecuted = false;
    supplierCandidatePromoted = false;
    response.writeHead(204).end();
    return;
  }
  if (request.method === "POST" && request.url === "/__promotion/approve") {
    promotionRequested = true;
    promotionApproved = true;
    response.writeHead(204).end();
    return;
  }
  if (
    request.method === "POST" &&
    request.url === "/__promotion/create-product"
  ) {
    promotionRequested = true;
    promotionApproved = true;
    productCreated = true;
    response.writeHead(204).end();
    return;
  }
  if (request.url === "/api/v1/health") {
    response
      .writeHead(200, { "content-type": "application/json" })
      .end(JSON.stringify({ status: "ok" }));
    return;
  }
  if (request.headers.authorization !== "Bearer test-dashboard-token") {
    response
      .writeHead(401, { "content-type": "application/json" })
      .end(JSON.stringify({ error: "unauthenticated" }));
    return;
  }
  if (request.url === "/api/v1/auth/me") {
    if (scenario === "unauthorized") {
      response
        .writeHead(403, { "content-type": "application/json" })
        .end(JSON.stringify({ error: "permission_denied" }));
      return;
    }
    response
      .writeHead(200, { "content-type": "application/json" })
      .end(
        JSON.stringify({
          user_id: userId,
          organization_id: organizationId,
          principal_type: "human",
        }),
      );
    return;
  }
  const match = request.url?.match(/^\/api\/v1\/dashboard\/([^?]+)/);
  if (match) {
    if (scenario === "partial" && match[1] === "financial-health") {
      response
        .writeHead(503, { "content-type": "application/json" })
        .end(JSON.stringify({ error: "unavailable" }));
      return;
    }
    response
      .writeHead(200, { "content-type": "application/json" })
      .end(JSON.stringify(dashboard(match[1])));
    return;
  }
  const url = new URL(request.url ?? "/", "http://127.0.0.1:4100");
  const json = (status, value) =>
    response
      .writeHead(status, { "content-type": "application/json" })
      .end(JSON.stringify(value));
  if (url.pathname === "/api/v1/opportunities" && request.method === "GET") {
    if (scenario === "opportunity-error")
      return json(503, { error: "unavailable" });
    return json(
      200,
      scenario === "empty" ? [] : [candidateOpportunity, marketOpportunity],
    );
  }
  if (
    url.pathname === `/api/v1/opportunities/${marketId}` &&
    request.method === "GET"
  )
    return json(200, marketOpportunity);
  if (url.pathname === `/api/v1/opportunities/${marketId}/committee-packet`)
    return json(200, {
      ...committeePacket,
      approval: approval(),
      product_theses: committeePacket.product_theses.map((item) => ({
        ...item,
        promotion: promotion(),
        promotion_approval: promotionRequested ? promotionApproval() : null,
      })),
    });
  if (
    url.pathname.startsWith("/api/v1/opportunities/") &&
    url.pathname.endsWith("/investment-memo")
  )
    return url.pathname.includes(marketId)
      ? json(200, memo)
      : json(404, { error: "not_found" });
  if (
    url.pathname.startsWith("/api/v1/opportunities/") &&
    url.pathname.endsWith("/launch-readiness")
  )
    return url.pathname.includes(marketId)
      ? json(200, readiness)
      : json(404, { error: "not_found" });
  if (url.pathname === `/api/v1/opportunity-candidates/${candidateId}`)
    return json(200, candidateOpportunity);
  if (url.pathname === `/api/v1/opportunities/${candidateId}/evidence`)
    return json(200, [candidateEvidence]);
  if (url.pathname === `/api/v1/opportunities/${candidateId}/assessment`)
    return json(200, candidateAssessment);
  if (
    url.pathname.match(/^\/api\/v1\/opportunities\/[0-9a-f-]+$/) &&
    request.method === "GET"
  )
    return json(404, { error: "not_found" });
  if (url.pathname === "/api/v1/opportunity-evidence")
    return json(200, scenario === "empty" ? [] : [marketEvidence]);
  if (url.pathname === "/api/v1/opportunity-scores")
    return json(200, scenario === "empty" ? [] : [marketScore]);
  if (url.pathname === "/api/v1/opportunity-risks")
    return json(200, scenario === "empty" ? [] : [marketRisk]);
  if (url.pathname === "/api/v1/approvals" && request.method === "GET")
    return json(
      200,
      scenario === "empty"
        ? []
        : [approval(), ...(promotionRequested ? [promotionApproval()] : [])],
    );
  const growthListRoutes = new Set([
    "/api/v1/revenue-experiments",
    "/api/v1/prospect-candidates",
    "/api/v1/growth-prospects",
    "/api/v1/revenue-observations",
    "/api/v1/cost-observations",
    "/api/v1/contribution-profit",
    "/api/v1/improvement-recommendations",
    "/api/v1/prospect-experiment-links",
    "/api/v1/growth-prospect-evidence",
    "/api/v1/prospect-research-evidence",
    "/api/v1/ranked-prospects",
    "/api/v1/growth-business-research-runs",
    "/api/v1/growth-opportunity-analyses",
    "/api/v1/growth-diagnoses",
    "/api/v1/growth-gifts",
    "/api/v1/growth-outreach-drafts",
    "/api/v1/outreach-tracking-events",
    "/api/v1/revenue-offers",
    "/api/v1/ai/model-capabilities",
  ]);
  if (growthListRoutes.has(url.pathname) && request.method === "GET") {
    if (scenario === "growth") {
      const records = {
        "/api/v1/revenue-experiments": [growthExperiment],
        "/api/v1/prospect-candidates": [growthCandidate],
        "/api/v1/growth-prospects": [growthProspect],
        "/api/v1/prospect-experiment-links": [growthAssignment],
        "/api/v1/growth-prospect-evidence": [growthEvidence],
      };
      return json(200, records[url.pathname] ?? []);
    }
    return json(200, []);
  }
  if (url.pathname === "/api/v1/growthos-dashboard")
    return json(200, {
      prospects_discovered: 0,
      qualified_prospects: 0,
      opportunities_found: 0,
      gifts_created: 0,
      outreach_drafts: 0,
      replies: 0,
      customers: 0,
      research_runs: 0,
      pending_human_review: 0,
      active_revenue_experiments: 0,
    });
  if (url.pathname === "/api/v1/growth-operational-readiness")
    return json(200, {
      organization_id: organizationId,
      growth_os: "ready",
      ai: "not_configured",
      worker: "ready",
      database: "ready",
      manual_send_mode: "active",
      external_connectors: "not_configured",
      queued_research: 0,
      failed_research: 0,
      guidance: [
        "Configure a tenant-scoped AI provider to enable governed research.",
        "External sending is manual; no connector is configured.",
      ],
    });
  if (url.pathname === "/api/v1/decision-queue")
    return json(200, scenario === "empty" ? [] : [decision]);
  if (url.pathname === `/api/v1/market-signals/${marketSignalId}/opportunities`)
    return json(200, [
      {
        link_id: "43434343-4343-4343-8343-434343434343",
        signal_id: marketSignalId,
        opportunity_id: marketId,
        linked_at: base.created_at,
        opportunity: marketOpportunity,
      },
    ]);
  if (url.pathname === `/api/v1/market-clusters/${marketCluster.id}/signals`)
    return json(200, [
      {
        membership_id: "44444444-5555-4444-8444-444444444444",
        cluster_id: marketCluster.id,
        signal: marketSignal,
        evidence: [marketSignalEvidence],
      },
    ]);
  if (url.pathname === `/api/v1/product-hypotheses/${productHypothesisId}`)
    return json(200, productHypothesis);
  if (
    url.pathname ===
    `/api/v1/product-hypotheses/${productHypothesisId}/promotion-readiness`
  )
    return json(
      200,
      scenario === "promotion"
        ? promotionReadiness
        : {
            ...promotionReadiness,
            ready: false,
            items: [
              {
                code: "investment_approval",
                severity: "blocker",
                status: "blocked",
                message:
                  "Opportunity investment approval is required before product promotion.",
                references: [],
              },
            ],
          },
    );
  if (
    url.pathname ===
      `/api/v1/product-hypotheses/${productHypothesisId}/promotion` &&
    request.method === "GET"
  )
    return json(200, promotion());
  if (
    url.pathname ===
      `/api/v1/product-hypotheses/${productHypothesisId}/promotion-request` &&
    request.method === "POST"
  ) {
    promotionRequested = true;
    return json(200, promotion());
  }
  if (
    url.pathname ===
      `/api/v1/product-hypotheses/${productHypothesisId}/promote` &&
    request.method === "POST"
  ) {
    productCreated = true;
    return json(200, promotion());
  }
  if (url.pathname === "/api/v1/product-promotion-brands")
    return json(200, [
      {
        id: brandId,
        organization_id: organizationId,
        name: "Commerce OS Labs",
        slug: "commerce-os-labs",
      },
    ]);
  if (url.pathname === "/api/v1/product-promotions")
    return json(200, promotionRequested ? [promotion()] : []);
  if (url.pathname === `/api/v1/products/${productRecordId}/origin`)
    return json(200, {
      product: productRecord,
      promotion: promotion(),
      hypothesis: productHypothesis,
    });
  if (
    url.pathname === `/api/v1/products/${productRecordId}/product-truth-drafts`
  )
    return json(200, []);
  if (url.pathname === `/api/v1/products/${productRecordId}/truth-comparison`)
    return json(200, {
      hypothesis_id: productHypothesisId,
      product_id: productRecordId,
      truth: null,
      comparable_fields: {
        product_name: { hypothesis: productHypothesis.name, truth: null },
        solution_summary: {
          hypothesis: productHypothesis.solution_description,
          truth: null,
        },
      },
      non_comparable_fields: [
        "customer_problem",
        "target_customer",
        "target_market",
        "economics",
        "supplier_candidates",
        "risks",
      ],
    });
  if (url.pathname === `/api/v1/products/${productRecordId}/supplier-comparison`)
    return json(200, {
      organization_id: organizationId,
      product_id: productRecordId,
      rows: [{ supplier: canonicalSupplier, match: canonicalSupplierMatch, evaluation: null, quote: canonicalSupplierQuote, risks: [], qualification: canonicalQualification }],
    });
  if (url.pathname === `/api/v1/products/${productRecordId}/supply-readiness`)
    return json(200, {
      organization_id: organizationId,
      product_id: productRecordId,
      ready: false,
      approved_suppliers: [],
      items: [
        { code: "governed_product_origin", severity: "blocker", status: "ready", message: "Governed Product promotion origin is recorded.", references: [] },
        { code: "product_truth", severity: "blocker", status: "blocked", message: "Approved Product Truth is required.", references: [] },
        { code: "approved_supplier", severity: "blocker", status: "blocked", message: "A qualified supplier must be approved for this Product.", references: [] },
      ],
      next_action: "Approved Product Truth is required.",
    });
  if (url.pathname === "/api/v1/build-packages" && request.method === "GET")
    return json(200, scenario === "empty" ? [] : [buildPackage()]);
  if (url.pathname === "/api/v1/listing-packages" && request.method === "GET")
    return json(200, scenario === "empty" ? [] : [listingPackage]);
  if (url.pathname === `/api/v1/products/${productRecordId}/listing-package` && request.method === "GET")
    return json(200, listingPackage);
  if (url.pathname === `/api/v1/products/${productRecordId}/shopify-readiness` && request.method === "GET")
    return json(200, shopifyProjection);
  if (url.pathname === `/api/v1/products/${productRecordId}/build-package` && request.method === "GET")
    return json(200, buildPackage());
  if (url.pathname === `/api/v1/suppliers/${canonicalSupplierId}/approve-for-product` && request.method === "POST") {
    buildRelationshipExecuted = true;
    return json(200, { ...base, ...buildRelationship(), organization_id: organizationId, product_id: productRecordId, source_candidate_id: null, approved_by: userId, approved_at: "2026-09-01T12:00:00Z" });
  }
  if (url.pathname === `/api/v1/supplier-candidates/${productSupplier.id}/promotion` && request.method === "GET")
    return json(200, supplierCandidatePromoted ? { ...base, id: "70707070-7070-4070-8070-707070707070", supplier_candidate_id: productSupplier.id, supplier_profile_id: canonicalSupplierId, confirmed_by: userId, confirmed_at: "2026-09-01T12:00:00Z" } : null);
  if (url.pathname === `/api/v1/supplier-candidates/${productSupplier.id}/promote` && request.method === "POST") {
    supplierCandidatePromoted = true;
    return json(201, { ...base, id: "70707070-7070-4070-8070-707070707070", supplier_candidate_id: productSupplier.id, supplier_profile_id: canonicalSupplierId, confirmed_by: userId, confirmed_at: "2026-09-01T12:00:00Z" });
  }
  const commerceLists = {
    "/api/v1/market-sources": [marketSource],
    "/api/v1/market-signals": [marketSignal],
    "/api/v1/market-evidence": [marketSignalEvidence],
    "/api/v1/market-clusters": [marketCluster],
    "/api/v1/demand-signals": [demandSignal],
    "/api/v1/demand-signal-evidence": [demandEvidence],
    "/api/v1/product-hypotheses": [productHypothesis],
    "/api/v1/product-economics": [productEconomics],
    "/api/v1/product-economic-inputs": economicInputs,
    "/api/v1/supplier-candidates": [productSupplier],
    "/api/v1/product-risks": [productRisk],
    "/api/v1/product-investment-scores": [productScore],
    "/api/v1/products": productCreated ? [productRecord] : [],
    "/api/v1/product-truth": [],
    "/api/v1/suppliers": [canonicalSupplier],
    "/api/v1/product-supplier-matches": [canonicalSupplierMatch],
    "/api/v1/supplier-quotes": [canonicalSupplierQuote],
    "/api/v1/supplier-evidence": [canonicalSupplierEvidence],
    "/api/v1/approved-product-suppliers": [],
  };
  if (url.pathname in commerceLists && request.method === "GET") {
    if (
      scenario === "commerce-partial" &&
      url.pathname === "/api/v1/market-evidence"
    )
      return json(503, { error: "evidence_unavailable" });
    return json(200, scenario === "empty" ? [] : commerceLists[url.pathname]);
  }
  if (url.pathname === "/api/v1/demand-intelligence-dashboard")
    return json(
      200,
      scenario === "empty"
        ? {
            ...demandDashboard,
            approved_signals: 0,
            source_overview: [],
            emerging_categories: [],
            emerging_customer_pains: [],
          }
        : demandDashboard,
    );
  if (url.pathname === `/api/v1/suppliers/${canonicalSupplierId}/intelligence`)
    return json(200, canonicalSupplierDetail);
  if (url.pathname === `/api/v1/suppliers/${canonicalSupplierId}/selection-request` && request.method === "POST")
    return json(201, { ...base, product_id: productRecordId, supplier_id: canonicalSupplierId, source_candidate_id: null, approval_request_id: promotionApprovalId, role: "primary", status: "pending", approved_by: null, approved_at: null });
  if (
    url.pathname === `/api/v1/approvals/${approvalId}/decision` &&
    request.method === "POST"
  ) {
    approvalStatus = "approved";
    return json(200, approval());
  }
  if (
    url.pathname === `/api/v1/approvals/${promotionApprovalId}/decision` &&
    request.method === "POST"
  ) {
    promotionApproved = true;
    return json(200, promotionApproval());
  }
  response.writeHead(404).end();
}).listen(4100, "127.0.0.1");
