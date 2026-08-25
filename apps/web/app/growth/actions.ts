"use server";

import { revalidatePath } from "next/cache";
import { apiPatch, apiPost } from "../../lib/api/client";
import { resolveExecutiveContext } from "../../lib/api/context";

export type GrowthActionState={kind:"idle"|"success"|"error";message:string};
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const value=(form:FormData,key:string)=>String(form.get(key)??"").trim();
const number=(form:FormData,key:string)=>{const raw=value(form,key);return raw===""?null:Number(raw)};
const ids=(form:FormData,key:string)=>form.getAll(key).flatMap(raw=>String(raw).split(",")).map(x=>x.trim()).filter(x=>UUID.test(x));

async function context(){const result=await resolveExecutiveContext();return result.ok?result.data:null;}
function refresh(id?:string){revalidatePath("/growth");if(id)revalidatePath(`/growth/${id}`);}

export async function createGrowthWorkspace(_:GrowthActionState,form:FormData):Promise<GrowthActionState>{
  const actor=await context();if(!actor)return {kind:"error",message:"A valid local founder session is required."};
  const name=value(form,"name"),description=value(form,"description"),segment=value(form,"segment");
  if(!name||!description||!segment)return {kind:"error",message:"Name, objective, and target segment are required."};
  const result=await apiPost<{id:string}>("/api/v1/revenue-experiments",{organization_id:actor.organization_id,name,description,target_segment:segment,offer_type:value(form,"offer_type")||"growth_visibility_audit",message_strategy:value(form,"message_strategy")||"Evidence-first founder outreach",segment,target_count:Number(value(form,"target_count")||0),start_date:new Date().toISOString().slice(0,10),success_metrics:{}});
  if(!result.ok)return {kind:"error",message:result.error.message};refresh(result.data.id);return {kind:"success",message:"Growth workspace created from the existing Revenue Experiment domain."};
}

export async function importGrowthProspect(_:GrowthActionState,form:FormData):Promise<GrowthActionState>{
  const actor=await context();if(!actor)return {kind:"error",message:"A valid local founder session is required."};
  const experimentId=value(form,"experiment_id"),business=value(form,"business_name"),observation=value(form,"observation"),source=value(form,"source_reference");
  if(!UUID.test(experimentId)||!business||!observation||!source)return {kind:"error",message:"Business, source, and evidence are required."};
  const result=await apiPost<{id:string}>("/api/v1/growth-prospect-imports",{organization_id:actor.organization_id,business_name:business,website:value(form,"website")||null,location:value(form,"location"),category:value(form,"category"),source_reference:source,evidence_type:value(form,"evidence_type"),observation,confidence:Number(value(form,"confidence")||0.7),collected_at:new Date().toISOString(),pain_signal:number(form,"pain_signal"),purchase_probability:number(form,"purchase_probability"),accessibility:number(form,"accessibility"),quick_win_potential:number(form,"quick_win_potential")});
  if(!result.ok)return {kind:"error",message:result.error.message};refresh(experimentId);return {kind:"success",message:"Prospect and traceable evidence imported. No external source was contacted."};
}

export async function addCandidateEvidence(_:GrowthActionState,form:FormData):Promise<GrowthActionState>{
  const actor=await context();if(!actor)return {kind:"error",message:"A valid local founder session is required."};
  const id=value(form,"candidate_id"),experimentId=value(form,"experiment_id");if(!UUID.test(id)||!value(form,"observation"))return {kind:"error",message:"Candidate and evidence are required."};
  const result=await apiPost("/api/v1/prospect-research-evidence",{organization_id:actor.organization_id,candidate_id:id,evidence_type:value(form,"evidence_type"),source_url:value(form,"source_reference")||null,observation:value(form,"observation"),confidence:Number(value(form,"confidence")||0.7),collected_at:new Date().toISOString()});
  if(!result.ok)return {kind:"error",message:result.error.message};refresh(experimentId);return {kind:"success",message:"Evidence added with provenance."};
}

export async function addProspectEvidence(_:GrowthActionState,form:FormData):Promise<GrowthActionState>{
  const actor=await context();if(!actor)return {kind:"error",message:"A valid local founder session is required."};
  const prospectId=value(form,"prospect_id"),experimentId=value(form,"experiment_id"),observation=value(form,"observation");
  if(!UUID.test(prospectId)||!observation)return {kind:"error",message:"Prospect and observation are required."};
  const result=await apiPost("/api/v1/growth-prospect-evidence",{organization_id:actor.organization_id,prospect_id:prospectId,evidence_type:value(form,"evidence_type")||"manual_observation",source_url:value(form,"source_reference")||null,observation,confidence:Number(value(form,"confidence")||0.7),collected_at:new Date().toISOString()});
  if(!result.ok)return {kind:"error",message:result.error.message};refresh(experimentId);return {kind:"success",message:"Prospect evidence saved with source, timestamp, and confidence."};
}

export async function requestGrowthResearch(_:GrowthActionState,form:FormData):Promise<GrowthActionState>{
  const actor=await context();if(!actor)return {kind:"error",message:"A valid local founder session is required."};
  const candidateId=value(form,"candidate_id"),capabilityId=value(form,"capability_id"),experimentId=value(form,"experiment_id");if(!UUID.test(candidateId)||!UUID.test(capabilityId))return {kind:"error",message:"An available AI capability is required."};
  const result=await apiPost(`/api/v1/prospect-candidates/${candidateId}/research`,{organization_id:actor.organization_id,capability_id:capabilityId});
  if(!result.ok)return {kind:"error",message:result.error.message};refresh(experimentId);return {kind:"success",message:"Research queued for durable worker execution."};
}

export async function activateGrowthProspect(_:GrowthActionState,form:FormData):Promise<GrowthActionState>{
  const actor=await context();if(!actor)return {kind:"error",message:"A valid local founder session is required."};
  const candidateId=value(form,"candidate_id"),experimentId=value(form,"experiment_id");
  const promoted=await apiPost<{id:string}>(`/api/v1/prospect-candidates/${candidateId}/activate`,{organization_id:actor.organization_id,email:value(form,"email")||null,social_links:{}});if(!promoted.ok)return {kind:"error",message:promoted.error.message};
  const assigned=await apiPost("/api/v1/prospect-experiment-links",{organization_id:actor.organization_id,experiment_id:experimentId,prospect_id:promoted.data.id,assigned_offer:"Evidence-backed Growth diagnosis",assigned_message:"Founder review required"});if(!assigned.ok)return {kind:"error",message:assigned.error.message};refresh(experimentId);return {kind:"success",message:"Qualified prospect activated and assigned to this workspace."};
}

export async function createGrowthOpportunity(_:GrowthActionState,form:FormData):Promise<GrowthActionState>{
  const actor=await context();if(!actor)return {kind:"error",message:"A valid local founder session is required."};const experimentId=value(form,"experiment_id"),evidence=ids(form,"evidence_ids");if(!evidence.length)return {kind:"error",message:"At least one traceable evidence ID is required."};
  const result=await apiPost("/api/v1/growth-opportunity-analyses",{organization_id:actor.organization_id,prospect_id:value(form,"prospect_id"),opportunity_type:value(form,"opportunity_type"),problem_statement:value(form,"problem_statement"),evidence_reference:evidence,customer_impact:value(form,"customer_impact"),purchase_probability:number(form,"purchase_probability"),confidence:Number(value(form,"confidence")||0.5),recommended_offer:value(form,"recommended_offer"),risks:value(form,"risks").split("\n").filter(Boolean),missing_information:value(form,"missing_information").split("\n").filter(Boolean),ai_request_id:null});if(!result.ok)return {kind:"error",message:result.error.message};refresh(experimentId);return {kind:"success",message:"Evidence-backed opportunity analysis created as an advisory record."};
}

export async function createGrowthDiagnosis(_:GrowthActionState,form:FormData):Promise<GrowthActionState>{
  const actor=await context();if(!actor)return {kind:"error",message:"A valid local founder session is required."};const experimentId=value(form,"experiment_id"),evidence=ids(form,"evidence_ids");if(!evidence.length)return {kind:"error",message:"Diagnosis requires traceable prospect evidence."};
  const result=await apiPost("/api/v1/growth-diagnoses",{organization_id:actor.organization_id,prospect_id:value(form,"prospect_id"),industry_profile_id:null,business_situation:value(form,"business_situation"),growth_problems:value(form,"growth_problems").split("\n").filter(Boolean),evidence_references:evidence,customer_impact:value(form,"customer_impact"),recommended_improvements:value(form,"recommended_improvements").split("\n").filter(Boolean),confidence:Number(value(form,"confidence")||0.5),risks:value(form,"risks").split("\n").filter(Boolean),ai_request_id:null});if(!result.ok)return {kind:"error",message:result.error.message};refresh(experimentId);return {kind:"success",message:"Evidence-backed diagnosis saved for founder review."};
}

export async function createGrowthGift(_:GrowthActionState,form:FormData):Promise<GrowthActionState>{
  const actor=await context();if(!actor)return {kind:"error",message:"A valid local founder session is required."};const experimentId=value(form,"experiment_id"),evidence=ids(form,"evidence_ids");
  const result=await apiPost("/api/v1/growth-gifts",{organization_id:actor.organization_id,prospect_id:value(form,"prospect_id"),opportunity_id:value(form,"opportunity_id"),title:value(form,"title"),description:value(form,"description"),before_state:value(form,"before_state"),after_state:value(form,"after_state"),asset_reference:null,evidence_reference:evidence,observed_issue:value(form,"observed_issue"),recommended_improvement:value(form,"recommended_improvement"),expected_value:value(form,"expected_value"),preview_type:"other",preview_status:"draft",gift_type:"other",before_asset_reference:null,after_asset_reference:null,customer_rationale:value(form,"customer_rationale"),growth_diagnosis_id:value(form,"diagnosis_id")||null,personalized_diagnosis:value(form,"personalized_diagnosis"),implementation_scope:value(form,"implementation_scope"),customer_value_explanation:value(form,"customer_value_explanation")});if(!result.ok)return {kind:"error",message:result.error.message};refresh(experimentId);return {kind:"success",message:"Growth Gift draft created. It cannot be delivered before approval."};
}

export async function createGrowthOutreach(_:GrowthActionState,form:FormData):Promise<GrowthActionState>{
  const actor=await context();if(!actor)return {kind:"error",message:"A valid local founder session is required."};const experimentId=value(form,"experiment_id"),body=value(form,"body"),subject=value(form,"subject"),evidence=ids(form,"evidence_ids"),aiRequest=value(form,"ai_request_id");if(!UUID.test(aiRequest))return {kind:"error",message:"A completed governed AI research request is required for outreach provenance."};
  const result=await apiPost("/api/v1/growth-outreach-drafts",{organization_id:actor.organization_id,prospect_id:value(form,"prospect_id"),growth_gift_id:value(form,"gift_id"),channel:value(form,"channel"),subject,body,tone:"founder_evidence_first",evidence_used:evidence,ai_request_id:aiRequest,industry_profile_id:null,industry_context:"",subject_options:[subject],opening_sentence:value(form,"opening_sentence"),personalized_context:value(form,"personalized_context"),problem_observation:value(form,"problem_observation"),gift_explanation:value(form,"gift_explanation"),soft_cta:value(form,"soft_cta"),growth_diagnosis_id:value(form,"diagnosis_id")||null,message_versions:{founder_friendly:body,consultant:body,gift_first:body}});if(!result.ok)return {kind:"error",message:result.error.message};refresh(experimentId);return {kind:"success",message:"Outreach draft created for human review. Nothing was sent."};
}

export async function requestGrowthApproval(_:GrowthActionState,form:FormData):Promise<GrowthActionState>{
  const actor=await context();if(!actor)return {kind:"error",message:"A valid local founder session is required."};
  const objectId=value(form,"object_id"),objectType=value(form,"object_type"),experimentId=value(form,"experiment_id");
  const action=objectType==="growth_gift"?"approve_growth_gift":"approve_outreach";
  const result=await apiPost("/api/v1/approvals",{organization_id:actor.organization_id,project_id:null,object_type:objectType,object_id:objectId,requested_action:action,reason:value(form,"reason")||"Founder requests evidence-backed review."});if(!result.ok)return {kind:"error",message:result.error.message};refresh(experimentId);return {kind:"success",message:"Approval requested. A different authorized human must decide when self-approval is prohibited."};
}

export async function decideGrowthApproval(_:GrowthActionState,form:FormData):Promise<GrowthActionState>{
  const id=value(form,"approval_id"),decision=value(form,"decision"),experimentId=value(form,"experiment_id");const result=await apiPost(`/api/v1/approvals/${id}/decision`,{decision,reason:value(form,"reason")});if(!result.ok)return {kind:"error",message:result.error.message};refresh(experimentId);return {kind:"success",message:`Approval ${decision}.`};
}

export async function advanceApprovedArtifact(_:GrowthActionState,form:FormData):Promise<GrowthActionState>{
  const actor=await context();if(!actor)return {kind:"error",message:"A valid local founder session is required."};const type=value(form,"object_type"),id=value(form,"object_id"),approval=value(form,"approval_id"),experimentId=value(form,"experiment_id");
  const path=type==="growth_gift"?`/api/v1/growth-gifts/${id}`:`/api/v1/growth-outreach-drafts/${id}`;
  const review=await apiPatch(path,{status:type==="growth_gift"?"review":"human_review",approval_request_id:null},{organization_id:actor.organization_id});if(!review.ok)return {kind:"error",message:review.error.message};
  const result=await apiPatch(path,{status:"approved",approval_request_id:approval},{organization_id:actor.organization_id});if(!result.ok)return {kind:"error",message:result.error.message};refresh(experimentId);return {kind:"success",message:"Artifact marked approved for controlled manual execution."};
}

export async function recordManualOutcome(_:GrowthActionState,form:FormData):Promise<GrowthActionState>{
  const actor=await context();if(!actor)return {kind:"error",message:"A valid local founder session is required."};const experimentId=value(form,"experiment_id"),eventType=value(form,"event_type"),outreachId=value(form,"outreach_id");
  if(eventType==="sent_manually"){if(!UUID.test(outreachId))return {kind:"error",message:"Manual send requires an approved outreach draft."};const sent=await apiPatch(`/api/v1/growth-outreach-drafts/${outreachId}`,{status:"sent",approval_request_id:null},{organization_id:actor.organization_id});if(!sent.ok)return {kind:"error",message:sent.error.message};}
  const result=await apiPost("/api/v1/outreach-tracking-events",{organization_id:actor.organization_id,prospect_experiment_link_id:value(form,"assignment_id"),outreach_draft_id:outreachId||null,event_type:eventType,occurred_at:new Date().toISOString(),metadata:{channel:value(form,"channel")||"manual",external_reference:value(form,"external_reference")||null,note:value(form,"note")||null}});if(!result.ok)return {kind:"error",message:result.error.message};refresh(experimentId);return {kind:"success",message:"External action recorded as an observed manual fact."};
}
