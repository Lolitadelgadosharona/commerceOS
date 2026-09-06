"use server";

import { revalidatePath } from "next/cache";

import { apiPost } from "../../../lib/api/client";
import { resolveExecutiveContext } from "../../../lib/api/context";

export type ShopifyActionState = { kind: "idle" | "success" | "error"; message: string };
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
async function context() { return resolveExecutiveContext(); }

export async function requestShopifyPublication(_: ShopifyActionState, form: FormData): Promise<ShopifyActionState> {
  const productId=String(form.get("product_id")??""),connectionId=String(form.get("connection_id")??""),reason=String(form.get("reason")??"").trim();
  if(!UUID.test(productId)||!UUID.test(connectionId)||reason.length<3)return {kind:"error",message:"Product, connection, and an evidence-based reason are required."};
  const ctx=await context();if(!ctx.ok)return {kind:"error",message:ctx.error.message};
  const result=await apiPost(`/api/v1/shopify/products/${productId}/publication-requests`,{organization_id:ctx.data.organization_id,connection_id:connectionId,reason});
  if(!result.ok)return {kind:"error",message:result.error.message};
  revalidatePath(`/channels/shopify/${productId}`);revalidatePath("/channels/shopify");revalidatePath("/decision-committee");
  return {kind:"success",message:"Publication review requested. No external write occurred."};
}

export async function authorizeShopifyPublication(_: ShopifyActionState, form: FormData): Promise<ShopifyActionState> {
  const publicationId=String(form.get("publication_id")??""),approvalId=String(form.get("approval_request_id")??""),productId=String(form.get("product_id")??"");
  if(![publicationId,approvalId,productId].every(x=>UUID.test(x)))return {kind:"error",message:"Valid publication and approved decision references are required."};
  const ctx=await context();if(!ctx.ok)return {kind:"error",message:ctx.error.message};
  const result=await apiPost(`/api/v1/shopify/publications/${publicationId}/authorize`,{organization_id:ctx.data.organization_id,approval_request_id:approvalId});
  if(!result.ok)return {kind:"error",message:result.error.message};
  revalidatePath(`/channels/shopify/${productId}`);return {kind:"success",message:"Publication authorized. Explicit execution is still required."};
}

export async function executeShopifyPublication(_: ShopifyActionState, form: FormData): Promise<ShopifyActionState> {
  const publicationId=String(form.get("publication_id")??""),productId=String(form.get("product_id")??"");
  if(!UUID.test(publicationId)||!UUID.test(productId))return {kind:"error",message:"Valid publication reference is required."};
  const ctx=await context();if(!ctx.ok)return {kind:"error",message:ctx.error.message};
  const result=await apiPost(`/api/v1/shopify/publications/${publicationId}/execute`,{organization_id:ctx.data.organization_id});
  if(!result.ok)return {kind:"error",message:result.error.message};
  revalidatePath(`/channels/shopify/${productId}`);return {kind:"success",message:"Governed execution queued for the Worker."};
}

export async function decideShopifyPublication(_: ShopifyActionState, form: FormData): Promise<ShopifyActionState> {
  const publicationId=String(form.get("publication_id")??""),approvalId=String(form.get("approval_request_id")??""),decision=String(form.get("decision")??""),reason=String(form.get("reason")??"").trim();
  if(!UUID.test(publicationId)||!UUID.test(approvalId)||!["approved","rejected"].includes(decision)||reason.length<3)return {kind:"error",message:"A valid human decision and evidence-based reason are required."};
  const ctx=await context();if(!ctx.ok)return {kind:"error",message:ctx.error.message};
  const result=await apiPost(`/api/v1/approvals/${approvalId}/decision`,{decision,reason});
  if(!result.ok)return {kind:"error",message:result.error.message};
  revalidatePath(`/channels/shopify/publications/${publicationId}`);revalidatePath("/decision-committee");
  return {kind:"success",message:`Publication ${decision}. No Shopify execution occurred.`};
}
