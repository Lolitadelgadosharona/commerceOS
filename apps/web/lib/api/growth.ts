import "server-only";
import { apiGet } from "./client";
import type { ApiResult } from "./types";

export type Entity = { id:string; created_at:string; updated_at:string; organization_id:string };
export type RevenueExperiment = Entity & { name:string; description:string; target_segment:string; offer_type:string; message_strategy:string; status:string; segment:string; target_count:number; start_date:string|null };
export type Candidate = Entity & { business_name:string; website:string|null; location:string; category:string; source_reference:string; confidence:number; status:string };
export type GrowthProspect = Entity & { business_name:string; website:string|null; email:string|null; location:string|null; industry:string; business_type:string; source:string; status:string; source_candidate_id:string|null };
export type Evidence = Entity & { candidate_id?:string; prospect_id?:string; evidence_type:string; source_url:string|null; observation:string; confidence:number; collected_at:string };
export type Qualification = Entity & { candidate_id:string; score:number|null; missing_inputs:string[]; explanation:string };
export type ResearchRun = Entity & { candidate_id:string; status:string; failure_reason:string|null; completed_at:string|null; capability_id:string; ai_request_id:string|null };
export type ResearchResult = Entity & { research_run_id:string; summary:string; evidence_summary:Array<Record<string,unknown>>; potential_growth_issues:string[]; confidence:number; missing_information:string[]; risk:string[] };
export type GrowthOpportunity = Entity & { prospect_id:string; opportunity_type:string; problem_statement:string; evidence_reference:string[]; customer_impact:string; confidence:number; recommended_offer:string; risks:string[]; missing_information:string[] };
export type Diagnosis = Entity & { prospect_id:string; business_situation:string; growth_problems:string[]; evidence_references:string[]; customer_impact:string; recommended_improvements:string[]; confidence:number; risks:string[]; status:string };
export type Gift = Entity & { prospect_id:string; title:string; description:string; status:string; approval_request_id:string|null; evidence_reference:string[]; observed_issue:string; recommended_improvement:string; expected_value:string; personalized_diagnosis:string; customer_value_explanation:string };
export type Outreach = Entity & { prospect_id:string; growth_gift_id:string; channel:string; subject:string|null; body:string; status:string; approval_request_id:string|null; evidence_used:string[]; soft_cta:string };
export type Approval = Entity & { object_type:string; object_id:string; requested_action:string; reason:string; status:string; requester_id:string; approver_id:string|null; decision_reason:string|null };
export type Assignment = Entity & { experiment_id:string; prospect_id:string; assigned_offer:string; assigned_message:string; result_status:string };
export type OutreachEvent = Entity & { prospect_experiment_link_id:string; outreach_draft_id:string|null; event_type:string; occurred_at:string; event_metadata:Record<string,unknown> };
export type RevenueOffer = Entity & { prospect_id:string; recommended_offer_id:string|null; offer_type:string; price:string; currency:string; scope:string; status:string };
export type Revenue = Entity & { project_id:string; channel:string|null; amount:string; currency:string; source_type:string; observation_date:string };
export type Cost = Entity & { product_id:string; channel:string|null; category:string; amount:string; currency:string; observation_date:string };
export type Profit = Entity & { product_id:string; period_id:string; currency:string; revenue:string; cost:string; contribution_profit:string; margin_percentage:number; confidence:number };
export type Learning = Entity & { title?:string; recommendation?:string; status?:string; pattern?:string; confidence?:number; source_experiment_id?:string };
export type Capability = Entity & { model_identity:string; capability_type:string; available:boolean };
export type GrowthDashboard = { prospects_discovered:number; qualified_prospects:number; opportunities_found:number; gifts_created:number; outreach_drafts:number; replies:number; customers:number; research_runs:number; pending_human_review:number; active_revenue_experiments:number };
export type GrowthReadiness = { organization_id:string; growth_os:"ready"|"degraded"; ai:"ready"|"not_configured"|"error"; worker:"ready"|"degraded"|"offline"; database:"ready"|"error"; manual_send_mode:"active"; external_connectors:"not_configured"; queued_research:number; failed_research:number; guidance:string[] };

async function all<T>(path:string, organization_id:string):Promise<ApiResult<T[]>> { return apiGet<T[]>(path,{organization_id}); }

export async function loadGrowthHome(organization_id:string) {
  const [experiments,candidates,prospects,approvals,revenues,costs,profits,learning,dashboard,readiness] = await Promise.all([
    all<RevenueExperiment>("/api/v1/revenue-experiments",organization_id), all<Candidate>("/api/v1/prospect-candidates",organization_id), all<GrowthProspect>("/api/v1/growth-prospects",organization_id), all<Approval>("/api/v1/approvals",organization_id), all<Revenue>("/api/v1/revenue-observations",organization_id), all<Cost>("/api/v1/cost-observations",organization_id), all<Profit>("/api/v1/contribution-profit",organization_id), all<Learning>("/api/v1/improvement-recommendations",organization_id), apiGet<GrowthDashboard>("/api/v1/growthos-dashboard",{organization_id}), apiGet<GrowthReadiness>("/api/v1/growth-operational-readiness",{organization_id}),
  ]);
  return {experiments,candidates,prospects,approvals,revenues,costs,profits,learning,dashboard,readiness};
}

export async function loadGrowthWorkspace(organization_id:string, experimentId:string) {
  const home=await loadGrowthHome(organization_id);
  const [assignments,evidence,candidateEvidence,qualifications,runs,opportunities,diagnoses,gifts,outreach,events,offers,capabilities] = await Promise.all([
    all<Assignment>("/api/v1/prospect-experiment-links",organization_id), all<Evidence>("/api/v1/growth-prospect-evidence",organization_id), all<Evidence>("/api/v1/prospect-research-evidence",organization_id), all<Qualification>("/api/v1/ranked-prospects",organization_id), all<ResearchRun>("/api/v1/growth-business-research-runs",organization_id), all<GrowthOpportunity>("/api/v1/growth-opportunity-analyses",organization_id), all<Diagnosis>("/api/v1/growth-diagnoses",organization_id), all<Gift>("/api/v1/growth-gifts",organization_id), all<Outreach>("/api/v1/growth-outreach-drafts",organization_id), all<OutreachEvent>("/api/v1/outreach-tracking-events",organization_id), all<RevenueOffer>("/api/v1/revenue-offers",organization_id), all<Capability>("/api/v1/ai/model-capabilities",organization_id),
  ]);
  const resultEntries:ResearchResult[]=[];
  if(runs.ok) for(const run of runs.data.slice(0,20)){ const result=await apiGet<ResearchResult|null>(`/api/v1/growth-business-research-runs/${run.id}/results`,{organization_id}); if(result.ok&&result.data) resultEntries.push(result.data); }
  return {...home, assignments,evidence,candidateEvidence,qualifications,runs,opportunities,diagnoses,gifts,outreach,events,offers,capabilities,researchResults:resultEntries,experimentId};
}
