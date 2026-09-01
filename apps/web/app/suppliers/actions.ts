"use server";

import { revalidatePath } from "next/cache";
import { apiPost } from "../../lib/api/client";
import { resolveExecutiveContext } from "../../lib/api/context";

export type SupplierActionState={kind:"idle"|"success"|"error";message:string};
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
export async function requestSupplierSelection(_:SupplierActionState,form:FormData):Promise<SupplierActionState>{
  const supplierId=String(form.get("supplier_id")??""),productId=String(form.get("product_id")??""),reason=String(form.get("reason")??"").trim();
  if(!UUID.test(supplierId)||!UUID.test(productId)||!reason)return {kind:"error",message:"Supplier, Product, and decision reason are required."};
  const context=await resolveExecutiveContext();if(!context.ok)return {kind:"error",message:context.error.message};
  const result=await apiPost(`/api/v1/suppliers/${supplierId}/selection-request`,{organization_id:context.data.organization_id,product_id:productId,role:"primary",reason});
  if(!result.ok)return {kind:"error",message:result.error.message};
  revalidatePath(`/suppliers/${supplierId}`);revalidatePath("/decision-committee");
  return {kind:"success",message:"Supplier selection entered human review. No purchase, payment, or contact occurred."};
}
