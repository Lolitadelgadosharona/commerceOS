"use server";

import { revalidatePath } from "next/cache";
import { apiPost } from "../../lib/api/client";
import { resolveExecutiveContext } from "../../lib/api/context";
import type { ApprovalRequest } from "../../lib/api/opportunities";

export type DecisionActionState = { kind:"idle"|"success"|"error"; message:string };
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

function value(form:FormData,key:string):string { return String(form.get(key)??"").trim(); }

export async function requestInvestmentReview(_:DecisionActionState,form:FormData):Promise<DecisionActionState> {
  const opportunityId=value(form,"opportunity_id"), reason=value(form,"reason");
  if(!UUID.test(opportunityId)||reason.length<1) return {kind:"error",message:"A valid opportunity and review reason are required."};
  const context=await resolveExecutiveContext();
  if(!context.ok) return {kind:"error",message:context.error.message};
  const result=await apiPost<{approval_request_id:string;decision_queue_item_id:string}>(`/api/v1/opportunities/${opportunityId}/request-investment-review`,{organization_id:context.data.organization_id,requester_id:context.data.user_id,project_id:null,reason});
  if(!result.ok) return {kind:"error",message:result.error.message};
  revalidatePath(`/opportunities/${opportunityId}`); revalidatePath("/dashboard");
  return {kind:"success",message:"Investment review entered the governed approval and Decision Queue workflow."};
}

export async function decideInvestmentReview(_:DecisionActionState,form:FormData):Promise<DecisionActionState> {
  const opportunityId=value(form,"opportunity_id"),approvalId=value(form,"approval_id"),decision=value(form,"decision"),reason=value(form,"reason");
  if(!UUID.test(opportunityId)||!UUID.test(approvalId)||!(["approved","rejected"].includes(decision))||reason.length<1) return {kind:"error",message:"A valid approval decision and reason are required."};
  const context=await resolveExecutiveContext();
  if(!context.ok) return {kind:"error",message:context.error.message};
  const result=await apiPost<ApprovalRequest>(`/api/v1/approvals/${approvalId}/decision`,{decision,reason});
  if(!result.ok) return {kind:"error",message:result.error.message};
  revalidatePath(`/opportunities/${opportunityId}`); revalidatePath("/dashboard");
  return {kind:"success",message:`Investment review ${decision}. Execution remains gated by launch readiness.`};
}
