import "server-only";

import { apiGet } from "./client";
import type { ApiResult, ReadModel } from "./types";

export type ListingIssue = {
  code: string;
  severity: "blocker" | "warning";
  message: string;
  references: string[];
};
export type ListingVersion = ReadModel & {
  product_id: string;
  product_truth_id: string;
  product_truth_version: number;
  listing_version: number;
  status: string;
  title: string;
  subtitle: string | null;
  summary: string;
  description: string;
  customer_problem: string | null;
  solution: string | null;
  features: string[];
  benefits: string[];
  specifications: Record<string, unknown>;
  use_cases: string[];
  whats_included: string[];
  warnings: string[];
  care_usage: string | null;
  shipping_facts: string | null;
  return_facts: string | null;
  risk_reversal: string | null;
  seo_title: string | null;
  meta_description: string | null;
  slug_suggestion: string | null;
  primary_topic: string | null;
  secondary_topics: string[];
  structured_attributes: Record<string, unknown>;
  commercial_price: string | null;
  currency: string | null;
  price_status: string;
  change_reason: string;
  approval_request_id: string | null;
  created_by: string;
  approved_by: string | null;
  approved_at: string | null;
};
export type ListingPackage = {
  organization_id: string;
  product_id: string;
  product_name: string;
  product_truth_id: string | null;
  product_truth_version: number | null;
  listing: ListingVersion | null;
  allowed_facts: Array<{
    fact: string;
    source: string;
    evidence: string[];
    can_use: boolean;
    restrictions: string[];
    notes: string | null;
  }>;
  claim_review: Array<{
    id: string;
    claim: string;
    claim_type: string;
    support_status: string;
    sources: string[];
    risk_level: string;
    policy_requirement: string | null;
    human_review_needed: boolean;
    blocking: boolean;
  }>;
  faqs: Array<
    ReadModel & {
      question: string;
      answer: string | null;
      answer_status: string;
      evidence_reference: string | null;
    }
  >;
  blockers: ListingIssue[];
  warnings: ListingIssue[];
  status: "not_ready" | "conditional" | "ready";
  product_truth_fresh: boolean;
  build_status: string;
  structured_data_ready: boolean;
  next_action: string;
  origin_opportunity_id: string | null;
  origin_hypothesis_id: string | null;
};
export type ShopifyProjection = {
  status: "draft_concept";
  external_id: null;
  title: string;
  description: string;
  product_type: string;
  vendor: string | null;
  price: string | null;
  currency: string | null;
  seo_title: string | null;
  seo_description: string | null;
  metafield_candidates: Record<string, unknown>;
  missing_fields: string[];
  publication_authorized: false;
};

export async function getListings(organizationId: string): Promise<ApiResult<ListingPackage[]>> {
  return apiGet("/api/v1/listing-packages", { organization_id: organizationId });
}

export async function getListing(productId: string, organizationId: string) {
  const query = { organization_id: organizationId };
  const [listing, shopify] = await Promise.all([
    apiGet<ListingPackage>(`/api/v1/products/${productId}/listing-package`, query),
    apiGet<ShopifyProjection>(`/api/v1/products/${productId}/shopify-readiness`, query),
  ]);
  return { listing, shopify };
}
