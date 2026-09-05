import "server-only";

import { apiGet } from "./client";
import type { ProductEconomicInput, SupplierCandidate } from "./commerce-intelligence";
import type { ApiResult, ReadModel } from "./types";
import type { SupplierQuote } from "./suppliers";

export type BuildItem = {
  code: string;
  severity: "blocker" | "warning" | "info";
  message: string;
  references: string[];
};
export type BuildPackage = {
  organization_id: string;
  product_id: string;
  product_name: string;
  product_truth_id: string | null;
  product_truth_version: number | null;
  specifications: Record<string, unknown>;
  requirements: Array<
    ReadModel & {
      attribute_key: string;
      display_label: string;
      value: unknown;
      unit: string | null;
      classification: string;
      evidence_reference: string | null;
      required_for_build: boolean;
      required_for_listing: boolean;
    }
  >;
  approved_suppliers: string[];
  supplier_relationships: Array<{
    id: string;
    supplier_id: string;
    approval_request_id: string;
    role: string;
    status: string;
  }>;
  supplier_fit: Array<{
    requirement: string;
    required_value: unknown;
    supplier_response: unknown;
    evidence: string[];
    status: "pass" | "conditional" | "fail" | "unknown";
    gap: string | null;
  }>;
  samples: Array<
    ReadModel & {
      supplier_id: string;
      sample_identifier: string;
      status: string;
      review_status: string;
      review_dimensions: Record<string, unknown>;
      evidence_reference: string | null;
    }
  >;
  validations: Array<
    ReadModel & {
      supplier_id: string;
      sample_id: string | null;
      validation_type: string;
      classification: string;
      result: string;
      observations: string;
      evidence_reference: string | null;
    }
  >;
  quote_ids: string[];
  quote_economics_ids: string[];
  blockers: BuildItem[];
  warnings: BuildItem[];
  status: "not_ready" | "conditional" | "ready";
  next_action: string;
  origin_opportunity_id: string | null;
  origin_hypothesis_id: string | null;
};

export type CandidatePromotion = ReadModel & {
  organization_id: string;
  supplier_candidate_id: string;
  supplier_profile_id: string;
  confirmed_by: string;
  confirmed_at: string;
};

function list<T>(result: ApiResult<T[]>): ApiResult<T[]> {
  return result.ok && !Array.isArray(result.data)
    ? { ok: false, error: { kind: "contract", message: "Build API returned an invalid list." } }
    : result;
}

export async function getBuildWorkspace(organizationId: string) {
  return list(
    await apiGet<BuildPackage[]>("/api/v1/build-packages", {
      organization_id: organizationId,
    }),
  );
}

export async function getBuildDetail(productId: string, organizationId: string) {
  const query = { organization_id: organizationId };
  const build = await apiGet<BuildPackage>(
    `/api/v1/products/${productId}/build-package`,
    query,
  );
  if (!build.ok) return { build, quotes: null, economics: null, candidates: null, promotions: [] };
  const [quotes, economics, allCandidates] = await Promise.all([
    apiGet<SupplierQuote[]>("/api/v1/supplier-quotes", {
      ...query,
      product_id: productId,
    }),
    build.data.origin_hypothesis_id
      ? apiGet<ProductEconomicInput[]>("/api/v1/product-economic-inputs", {
          ...query,
          product_id: build.data.origin_hypothesis_id,
        })
      : Promise.resolve({ ok: true, data: [] } as ApiResult<ProductEconomicInput[]>),
    apiGet<SupplierCandidate[]>("/api/v1/supplier-candidates", query),
  ]);
  const candidates = allCandidates.ok
    ? allCandidates.data.filter((item) => item.product_id === build.data.origin_hypothesis_id)
    : [];
  const promotions = await Promise.all(
    candidates.map((item) =>
      apiGet<CandidatePromotion | null>(
        `/api/v1/supplier-candidates/${item.id}/promotion`,
        query,
      ),
    ),
  );
  return { build, quotes, economics, candidates, promotions };
}
