import "server-only";
import { apiGet } from "./client";
import type { ApiResult, ReadModel } from "./types";
import type { ApprovalRequest } from "./opportunities";
import type { SupplierComparison, SupplyReadiness } from "./suppliers";

export type MarketSource = ReadModel & {
  organization_id: string;
  name: string;
  platform: string;
  source_type: string;
  access_method: string;
  reliability_score: number;
  status: string;
};
export type MarketSignal = ReadModel & {
  organization_id: string;
  source_id: string;
  region: string;
  category: string;
  signal_type: string;
  title: string;
  description: string;
  trend_direction: string;
  confidence_score: number;
  observed_at: string;
  status: string;
};
export type MarketEvidence = ReadModel & {
  organization_id: string;
  signal_id: string;
  evidence_type: string;
  content_reference: string;
  strength_score: number;
  captured_at: string;
};
export type MarketCluster = ReadModel & {
  organization_id: string;
  name: string;
  category: string;
  confidence: number;
  impact_score: number;
};
export type SignalOpportunityProjection = {
  link_id: string;
  signal_id: string;
  opportunity_id: string;
  linked_at: string;
  opportunity: {
    id: string;
    title: string;
    status: string;
    confidence_score: number;
    category: string;
    market: string;
    geography: string;
  };
};
export type DemandSignal = ReadModel & {
  organization_id: string;
  source_domain: string;
  source_reference_id: string;
  source_type: string;
  source_reference: string;
  collection_method: string;
  evidence_origin: string;
  confidence_basis: string;
  customer_segment: string;
  category: string;
  problem_statement: string;
  customer_language: string;
  frequency: number;
  confidence: number;
  evidence_count: number;
  status: string;
};
export type DemandEvidence = ReadModel & {
  organization_id: string;
  demand_signal_id: string;
  source_type: string;
  source_id: string;
  source_reference: string;
  evidence_text: string;
};
export type DemandDashboard = {
  organization_id: string;
  draft_signals: number;
  signals_in_review: number;
  approved_signals: number;
  source_overview: Array<{
    source_type: string;
    signal_count: number;
    evidence_count: number;
    average_confidence: number;
    signal_percentage: number;
  }>;
  emerging_categories: Array<{
    category: string;
    signal_count: number;
    total_frequency: number;
    average_confidence: number;
  }>;
  customer_pain_clusters: Array<{
    cluster_id: string;
    name: string;
    category: string;
    severity_score: number;
    confidence_score: number;
    status: string;
  }>;
  emerging_demand_themes: Array<{
    theme_analysis_id: string;
    name: string;
    category: string;
    evidence_count: number;
    signal_diversity: number;
    confidence: number;
    evidence_strength: string;
  }>;
  predictive_indicators: Array<{
    demand_signal_id: string;
    upcoming_trend: string;
    timeframe: string;
    evidence_sources: string[];
    confidence: number;
    uncertainty: string;
  }>;
  emerging_customer_pains: Array<{
    demand_signal_id: string;
    category: string;
    customer_segment: string;
    problem_statement: string;
    frequency: number;
    confidence: number;
    evidence_count: number;
    source_type: string;
    evidence_sources: string[];
    source_conversation_ids: string[];
  }>;
};
export type ProductHypothesis = ReadModel & {
  organization_id: string;
  opportunity_id: string;
  name: string;
  description: string;
  customer_problem: string;
  solution_description: string;
  target_customer: string;
  target_market: string;
  status: string;
  confidence_score: number;
};
export type ProductEconomics = ReadModel & {
  organization_id: string;
  product_id: string;
  selling_price: string;
  estimated_product_cost: string;
  estimated_shipping_cost: string;
  payment_cost: string;
  estimated_marketing_cost: string;
  contribution_margin: string;
  margin_percentage: string;
  currency: string;
};
export type ProductEconomicInput = ReadModel & {
  organization_id: string;
  product_economics_id: string;
  metric: string;
  value: string | null;
  classification: string;
  source: string;
  confidence: number | null;
  as_of: string | null;
  evidence_reference: string | null;
  notes: string | null;
};
export type SupplierCandidate = ReadModel & {
  organization_id: string;
  product_id: string;
  source_type: string;
  supplier_reference: string;
  estimated_cost: string;
  minimum_order_quantity: number;
  lead_time: string;
  quality_notes: string;
  risk_level: string;
};
export type ProductRisk = ReadModel & {
  organization_id: string;
  product_id: string;
  risk_type: string;
  severity: string;
  description: string;
  status: string;
};
export type ProductInvestmentScore = ReadModel & {
  organization_id: string;
  product_id: string;
  opportunity_score: number;
  margin_score: number;
  risk_score: number;
  competition_score: number;
  confidence_score: number;
  overall_score: number;
  formula_version: string;
};
export type Product = ReadModel & {
  organization_id: string;
  name: string;
  description: string;
  category: string;
  brand_id: string;
  status: string;
};
export type ProductTruth = {
  id: string;
  organization_id: string;
  product_id: string;
  version: number;
  summary: string;
  features: string[];
  specifications: Record<string, unknown>;
  approved_claims: string[];
  restricted_claims: string[];
  usage_notes: string;
  created_by: string;
  approval_id: string;
  created_at: string;
  updated_at: string;
};
export type PromotionReadiness = {
  organization_id: string;
  product_hypothesis_id: string;
  opportunity_id: string;
  ready: boolean;
  items: Array<{
    code: string;
    severity: "blocker" | "warning" | "info";
    status: string;
    message: string;
    references: string[];
  }>;
};
export type ProductPromotion = ReadModel & {
  organization_id: string;
  product_hypothesis_id: string;
  opportunity_id: string;
  brand_id: string;
  approval_request_id: string;
  product_id: string | null;
  requested_by: string;
  promoted_by: string | null;
  promoted_at: string | null;
  status: string;
};
export type ProductTruthDraft = ReadModel & {
  organization_id: string;
  product_id: string;
  summary: string;
  features: string[];
  specifications: Record<string, unknown>;
  approved_claims: string[];
  restricted_claims: string[];
  usage_notes: string;
  change_reason: string;
  supporting_evidence: string[];
  created_by: string;
  approval_request_id: string | null;
  truth_id: string | null;
  status: string;
};
export type TruthComparison = {
  hypothesis_id: string;
  product_id: string;
  truth: ProductTruth | null;
  comparable_fields: Record<string, { hypothesis: unknown; truth: unknown }>;
  non_comparable_fields: string[];
};
export type PromotionBrand = {
  id: string;
  organization_id: string;
  name: string;
  slug: string;
};

function list<T>(result: ApiResult<T[]>): ApiResult<T[]> {
  return result.ok && !Array.isArray(result.data)
    ? {
        ok: false,
        error: {
          kind: "contract",
          message: "Commerce intelligence API returned an invalid list.",
        },
      }
    : result;
}

export async function getMarketIntelligenceWorkspace(organizationId: string) {
  const query = { organization_id: organizationId };
  const [
    sources,
    signals,
    evidence,
    clusters,
    demandSignals,
    demandEvidence,
    dashboard,
  ] = await Promise.all([
    apiGet<MarketSource[]>("/api/v1/market-sources", query),
    apiGet<MarketSignal[]>("/api/v1/market-signals", query),
    apiGet<MarketEvidence[]>("/api/v1/market-evidence", query),
    apiGet<MarketCluster[]>("/api/v1/market-clusters", query),
    apiGet<DemandSignal[]>("/api/v1/demand-signals", query),
    apiGet<DemandEvidence[]>("/api/v1/demand-signal-evidence", query),
    apiGet<DemandDashboard>("/api/v1/demand-intelligence-dashboard", query),
  ]);
  return {
    sources: list(sources),
    signals: list(signals),
    evidence: list(evidence),
    clusters: list(clusters),
    demandSignals: list(demandSignals),
    demandEvidence: list(demandEvidence),
    dashboard,
  };
}

export async function getMarketSignalDetail(
  id: string,
  organizationId: string,
) {
  const [data, opportunities] = await Promise.all([
    getMarketIntelligenceWorkspace(organizationId),
    apiGet<SignalOpportunityProjection[]>(
      `/api/v1/market-signals/${id}/opportunities`,
      { organization_id: organizationId },
    ),
  ]);
  const signal = data.signals.ok
    ? data.signals.data.find((item) => item.id === id)
    : undefined;
  return { ...data, signal, opportunities: list(opportunities) };
}

export async function getProductWorkspace(organizationId: string) {
  const query = { organization_id: organizationId };
  const [
    hypotheses,
    economics,
    suppliers,
    risks,
    scores,
    products,
    truth,
    promotions,
  ] = await Promise.all([
    apiGet<ProductHypothesis[]>("/api/v1/product-hypotheses", query),
    apiGet<ProductEconomics[]>("/api/v1/product-economics", query),
    apiGet<SupplierCandidate[]>("/api/v1/supplier-candidates", query),
    apiGet<ProductRisk[]>("/api/v1/product-risks", query),
    apiGet<ProductInvestmentScore[]>(
      "/api/v1/product-investment-scores",
      query,
    ),
    apiGet<Product[]>("/api/v1/products", query),
    apiGet<ProductTruth[]>("/api/v1/product-truth", query),
    apiGet<ProductPromotion[]>("/api/v1/product-promotions", query),
  ]);
  return {
    hypotheses: list(hypotheses),
    economics: list(economics),
    suppliers: list(suppliers),
    risks: list(risks),
    scores: list(scores),
    products: list(products),
    truth: list(truth),
    promotions: list(promotions),
  };
}

export async function getProductHypothesisDetail(
  id: string,
  organizationId: string,
) {
  const query = { organization_id: organizationId };
  const [
    workspace,
    hypothesis,
    provenance,
    readiness,
    promotion,
    brands,
    approvals,
  ] = await Promise.all([
    getProductWorkspace(organizationId),
    apiGet<ProductHypothesis>(`/api/v1/product-hypotheses/${id}`, query),
    apiGet<ProductEconomicInput[]>("/api/v1/product-economic-inputs", {
      ...query,
      product_id: id,
    }),
    apiGet<PromotionReadiness>(
      `/api/v1/product-hypotheses/${id}/promotion-readiness`,
      query,
    ),
    apiGet<ProductPromotion | null>(
      `/api/v1/product-hypotheses/${id}/promotion`,
      query,
    ),
    apiGet<PromotionBrand[]>("/api/v1/product-promotion-brands", query),
    apiGet<ApprovalRequest[]>("/api/v1/approvals", query),
  ]);
  let origin = null,
    drafts = null,
    comparison = null,
    supplierComparison = null,
    supplyReadiness = null;
  if (promotion.ok && promotion.data?.product_id) {
    [origin, drafts, comparison, supplierComparison, supplyReadiness] = await Promise.all([
      apiGet<{
        product: Product;
        promotion: ProductPromotion;
        hypothesis: ProductHypothesis;
      }>(`/api/v1/products/${promotion.data.product_id}/origin`, query),
      apiGet<ProductTruthDraft[]>(
        `/api/v1/products/${promotion.data.product_id}/product-truth-drafts`,
        query,
      ),
      apiGet<TruthComparison>(
        `/api/v1/products/${promotion.data.product_id}/truth-comparison`,
        query,
      ),
      apiGet<SupplierComparison>(
        `/api/v1/products/${promotion.data.product_id}/supplier-comparison`,
        query,
      ),
      apiGet<SupplyReadiness>(
        `/api/v1/products/${promotion.data.product_id}/supply-readiness`,
        query,
      ),
    ]);
  }
  return {
    ...workspace,
    hypothesis,
    provenance: list(provenance),
    readiness,
    promotion,
    brands: list(brands),
    approvals: list(approvals),
    origin,
    drafts,
    comparison,
    supplierComparison,
    supplyReadiness,
  };
}
