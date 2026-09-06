import "server-only";

import { apiGet } from "./client";
import type { ApiResult, ReadModel } from "./types";

export type ShopifyConnection = ReadModel & {
  store_domain: string;
  display_name: string;
  authentication_mode: string;
  credential_configured: boolean;
  required_scopes: string[];
  granted_scopes: string[];
  api_version: string;
  status: string;
  publication_policy: Record<string, unknown>;
  validated_at: string | null;
  last_error_category: string | null;
  last_error_message: string | null;
};
export type ShopifyIssue = { code: string; severity: "blocker" | "warning"; message: string };
export type ShopifyProjection = {
  title: string;
  description_html: string;
  vendor: string | null;
  product_type: string;
  handle: string | null;
  seo: Record<string, string | null>;
  options: Array<Record<string, unknown>>;
  variants: Array<Record<string, unknown>>;
  metafields: Record<string, unknown>;
  media: Array<Record<string, unknown>>;
  external_status: "draft";
  inventory_quantities: never[];
};
export type ShopifyReadiness = {
  organization_id: string;
  product_id: string;
  connection_id: string | null;
  product_truth_id: string | null;
  product_truth_version: number | null;
  listing_version_id: string | null;
  listing_version: number | null;
  projection: ShopifyProjection | null;
  projection_hash: string | null;
  status: "not_ready" | "conditional" | "ready";
  blockers: ShopifyIssue[];
  warnings: ShopifyIssue[];
  media_status: string;
  publication_status: string;
  authorization_status: string;
  external_resource_id: string | null;
  external_product_id: string | null;
  drift_status: string;
  operation: "create" | "update";
  next_action: string;
};
export type ShopifyPublication = ReadModel & {
  connection_id: string;
  product_id: string;
  product_truth_id: string;
  product_truth_version: number;
  listing_version_id: string;
  listing_version: number;
  operation: string;
  status: string;
  approval_request_id: string | null;
  attempts: number;
  last_error_category: string | null;
  last_error_message: string | null;
};
export type ShopifyResource = ReadModel & {
  connection_id: string;
  product_id: string;
  external_product_id: string;
  external_variant_ids: string[];
  external_status: string;
  source_listing_version_id: string;
  last_publication_id: string;
  last_synced_at: string;
};
export type ShopifyReconciliation = ReadModel & {
  product_id: string;
  status: string;
  differences: string[];
  checked_at: string;
};
export type ShopifyWorkspace = {
  connections: ShopifyConnection[];
  products: ShopifyReadiness[];
  publications: ShopifyPublication[];
  resources: ShopifyResource[];
  reconciliations: ShopifyReconciliation[];
};

export function getShopifyWorkspace(organizationId: string): Promise<ApiResult<ShopifyWorkspace>> {
  return apiGet("/api/v1/shopify/workspace", { organization_id: organizationId });
}

export function getShopifyReadiness(
  productId: string,
  organizationId: string,
  connectionId?: string,
): Promise<ApiResult<ShopifyReadiness>> {
  return apiGet(`/api/v1/shopify/products/${productId}/readiness`, {
    organization_id: organizationId,
    ...(connectionId ? { connection_id: connectionId } : {}),
  });
}
