"use server";

import { revalidatePath } from "next/cache";

import { apiPost } from "../../lib/api/client";
import { resolveExecutiveContext } from "../../lib/api/context";

export type BuildActionState = { kind: "idle" | "success" | "error"; message: string };
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export async function executeSupplierRelationship(
  _: BuildActionState,
  form: FormData,
): Promise<BuildActionState> {
  const supplierId = String(form.get("supplier_id") ?? "");
  const productId = String(form.get("product_id") ?? "");
  const approvalId = String(form.get("approval_request_id") ?? "");
  const role = String(form.get("role") ?? "primary");
  if (![supplierId, productId, approvalId].every((value) => UUID.test(value)))
    return { kind: "error", message: "Valid Product, Supplier, and approval references are required." };
  const context = await resolveExecutiveContext();
  if (!context.ok) return { kind: "error", message: context.error.message };
  const result = await apiPost(`/api/v1/suppliers/${supplierId}/approve-for-product`, {
    organization_id: context.data.organization_id,
    product_id: productId,
    approval_request_id: approvalId,
    role,
  });
  if (!result.ok) return { kind: "error", message: result.error.message };
  revalidatePath(`/build/${productId}`);
  revalidatePath(`/products/${productId}`);
  return {
    kind: "success",
    message: "Approved relationship executed. No contact, purchase, payment, or order occurred.",
  };
}

export async function promoteSupplierCandidate(
  _: BuildActionState,
  form: FormData,
): Promise<BuildActionState> {
  const candidateId = String(form.get("candidate_id") ?? "");
  const productId = String(form.get("product_id") ?? "");
  const name = String(form.get("name") ?? "").trim();
  const country = String(form.get("country") ?? "").trim();
  if (!UUID.test(candidateId) || !UUID.test(productId) || !name || !country)
    return { kind: "error", message: "Verified supplier name and country are required." };
  const context = await resolveExecutiveContext();
  if (!context.ok) return { kind: "error", message: context.error.message };
  const result = await apiPost(`/api/v1/supplier-candidates/${candidateId}/promote`, {
    organization_id: context.data.organization_id,
    name,
    country,
  });
  if (!result.ok) return { kind: "error", message: result.error.message };
  revalidatePath(`/build/${productId}`);
  revalidatePath("/suppliers");
  return {
    kind: "success",
    message: "Canonical Supplier Profile confirmed. Candidate history was preserved.",
  };
}
