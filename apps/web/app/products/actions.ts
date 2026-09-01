"use server";

import { revalidatePath } from "next/cache";
import { apiPost } from "../../lib/api/client";
import { resolveExecutiveContext } from "../../lib/api/context";

export type ProductActionState = {
  kind: "idle" | "success" | "error";
  message: string;
};
const UUID =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const value = (form: FormData, key: string) =>
  String(form.get(key) ?? "").trim();

export async function requestProductPromotion(
  _: ProductActionState,
  form: FormData,
): Promise<ProductActionState> {
  const hypothesisId = value(form, "hypothesis_id"),
    brandId = value(form, "brand_id"),
    reason = value(form, "reason");
  if (!UUID.test(hypothesisId) || !UUID.test(brandId) || !reason)
    return {
      kind: "error",
      message: "Brand and promotion reason are required.",
    };
  const context = await resolveExecutiveContext();
  if (!context.ok) return { kind: "error", message: context.error.message };
  const result = await apiPost(
    `/api/v1/product-hypotheses/${hypothesisId}/promotion-request`,
    {
      organization_id: context.data.organization_id,
      brand_id: brandId,
      reason,
    },
  );
  if (!result.ok) return { kind: "error", message: result.error.message };
  revalidatePath(`/products/${hypothesisId}`);
  revalidatePath("/decision-committee");
  return {
    kind: "success",
    message: "Product promotion entered its own governed approval workflow.",
  };
}

export async function executeProductPromotion(
  _: ProductActionState,
  form: FormData,
): Promise<ProductActionState> {
  const hypothesisId = value(form, "hypothesis_id"),
    approvalId = value(form, "approval_id");
  if (!UUID.test(hypothesisId) || !UUID.test(approvalId))
    return {
      kind: "error",
      message: "Approved promotion context is required.",
    };
  const context = await resolveExecutiveContext();
  if (!context.ok) return { kind: "error", message: context.error.message };
  const result = await apiPost(
    `/api/v1/product-hypotheses/${hypothesisId}/promote`,
    {
      organization_id: context.data.organization_id,
      approval_request_id: approvalId,
    },
  );
  if (!result.ok) return { kind: "error", message: result.error.message };
  revalidatePath(`/products/${hypothesisId}`);
  return {
    kind: "success",
    message:
      "Canonical Product created. Product Truth remains a separate governed step.",
  };
}

export async function createTruthDraft(
  _: ProductActionState,
  form: FormData,
): Promise<ProductActionState> {
  const productId = value(form, "product_id"),
    hypothesisId = value(form, "hypothesis_id"),
    summary = value(form, "summary"),
    reason = value(form, "change_reason");
  if (!UUID.test(productId) || !summary || !reason)
    return {
      kind: "error",
      message: "Product Truth summary and change reason are required.",
    };
  const context = await resolveExecutiveContext();
  if (!context.ok) return { kind: "error", message: context.error.message };
  const result = await apiPost(
    `/api/v1/products/${productId}/product-truth-drafts`,
    {
      organization_id: context.data.organization_id,
      summary,
      features: [],
      specifications: {},
      approved_claims: [],
      restricted_claims: [],
      usage_notes: "Draft requires human review before canonical publication.",
      change_reason: reason,
      supporting_evidence: [],
    },
  );
  if (!result.ok) return { kind: "error", message: result.error.message };
  revalidatePath(`/products/${hypothesisId}`);
  return {
    kind: "success",
    message: "Product Truth draft created; it is not approved truth.",
  };
}

export async function requestTruthReview(
  _: ProductActionState,
  form: FormData,
): Promise<ProductActionState> {
  const draftId = value(form, "draft_id"),
    hypothesisId = value(form, "hypothesis_id"),
    reason = value(form, "reason");
  if (!UUID.test(draftId) || !UUID.test(hypothesisId) || !reason)
    return { kind: "error", message: "A review reason is required." };
  const context = await resolveExecutiveContext();
  if (!context.ok) return { kind: "error", message: context.error.message };
  const result = await apiPost(
    `/api/v1/product-truth-drafts/${draftId}/request-review`,
    { organization_id: context.data.organization_id, reason },
  );
  if (!result.ok) return { kind: "error", message: result.error.message };
  revalidatePath(`/products/${hypothesisId}`);
  revalidatePath("/decision-committee");
  return {
    kind: "success",
    message: "Product Truth draft entered its separate review workflow.",
  };
}

export async function publishTruthDraft(
  _: ProductActionState,
  form: FormData,
): Promise<ProductActionState> {
  const draftId = value(form, "draft_id"),
    hypothesisId = value(form, "hypothesis_id"),
    approvalId = value(form, "approval_id");
  if (!UUID.test(draftId) || !UUID.test(hypothesisId) || !UUID.test(approvalId))
    return { kind: "error", message: "Approved Truth review is required." };
  const context = await resolveExecutiveContext();
  if (!context.ok) return { kind: "error", message: context.error.message };
  const result = await apiPost(
    `/api/v1/product-truth-drafts/${draftId}/publish`,
    {
      organization_id: context.data.organization_id,
      approval_request_id: approvalId,
    },
  );
  if (!result.ok) return { kind: "error", message: result.error.message };
  revalidatePath(`/products/${hypothesisId}`);
  return {
    kind: "success",
    message: "A new immutable Product Truth version was published.",
  };
}
