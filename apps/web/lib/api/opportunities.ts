import "server-only";
import { apiGet } from "./client";
import type { ApiResult, ReadModel } from "./types";

export type MarketOpportunity = ReadModel & { organization_id:string; title:string; description:string; category:string; market:string; geography:string; trigger_type:string; timing_window:string; status:"observed"|"evaluating"|"qualified"|"rejected"|"archived"; confidence_score:number };
export type DiscoveryOpportunity = ReadModel & { organization_id:string; discovery_run_id:string|null; title:string; category:string; problem_statement:string; customer_segment:string; opportunity_description:string; market_context:string; evidence_summary:string; evidence_references:Array<Record<string,unknown>>; solution_direction:string; customer_language:string[]; confidence_score:number; risk_summary:string[]; open_questions:string[]; missing_evidence:string[]; advisory_score:number; status:string; methodology_version:string; decision_queue_item_id:string|null };
export type Opportunity = MarketOpportunity | DiscoveryOpportunity;
export type OpportunityEvidence = ReadModel & { organization_id:string; opportunity_id:string; source_type:string; source_reference:string; evidence_summary:string; confidence_score:number };
export type CandidateEvidence = ReadModel & { organization_id:string; opportunity_candidate_id:string; demand_signal_id:string; evidence_type:string; evidence_summary:string; contribution:string; confidence:number };
export type CandidateAssessment = ReadModel & { organization_id:string; opportunity_candidate_id:string; demand_strength:string; signal_diversity:number; market_timing:string; confidence:number; risks:string[]; missing_information:string[]; assumptions:string[] };
export type OpportunityScore = ReadModel & { organization_id:string; opportunity_id:string; demand_score:number; pain_score:number; trend_score:number; margin_score:number; competition_score:number; ip_risk_score:number; dispute_risk_score:number; overall_score:number; formula_version:string };
export type OpportunityRisk = ReadModel & { organization_id:string; opportunity_id:string; risk_type:string; severity:string; description:string; status:string };
export type ApprovalRequest = ReadModel & { organization_id:string; project_id:string|null; requester_id:string; object_type:string; object_id:string; requested_action:string; reason:string; status:"pending"|"approved"|"rejected"|"cancelled"; approver_id:string|null; decision_time:string|null; decision_reason:string|null };
export type DecisionQueueRecord = ReadModel & { organization_id:string; title:string; domain:string; reason:string; priority:string; required_action:string; status:string; approval_request_id:string|null };
export type InvestmentMemo = { opportunity_id:string; organization_id:string; summary:{ title?:string; description?:string; why_now?:string; assessment?:Record<string,unknown>|null; report?:Record<string,unknown>|null }; evidence:Array<Record<string,unknown>>; conclusions:Record<string,{ classification:string; value:unknown }>; missing_evidence:string[]; confidence:number; recommended_decision:string };
export type ReadinessItem = { category:string; status:string; reason:string; references:string[]; blocking:boolean };
export type LaunchReadiness = { opportunity_id:string; categories:ReadinessItem[]; overall_status:string; blocking_reasons:string[] };

export function isDiscoveryOpportunity(item: Opportunity): item is DiscoveryOpportunity { return "problem_statement" in item; }
function arrayResult<T>(value: ApiResult<T[]>): ApiResult<T[]> { return value.ok && !Array.isArray(value.data) ? { ok:false,error:{kind:"contract",message:"Opportunity API returned an invalid list."} } : value; }

export async function getOpportunityWorkspace(organizationId:string) {
  const query={organization_id:organizationId};
  const [opportunities,scores,risks,approvals,decisions]=await Promise.all([
    apiGet<Opportunity[]>("/api/v1/opportunities",query), apiGet<OpportunityScore[]>("/api/v1/opportunity-scores",query), apiGet<OpportunityRisk[]>("/api/v1/opportunity-risks",query), apiGet<ApprovalRequest[]>("/api/v1/approvals",query), apiGet<DecisionQueueRecord[]>("/api/v1/decision-queue",query),
  ]);
  return {opportunities:arrayResult(opportunities),scores:arrayResult(scores),risks:arrayResult(risks),approvals:arrayResult(approvals),decisions:arrayResult(decisions)};
}

export async function getMarketOpportunityDetail(id:string,organizationId:string) {
  const query={organization_id:organizationId};
  const [opportunity,memo,readiness,evidence,scores,risks,approvals,decisions]=await Promise.all([
    apiGet<MarketOpportunity>(`/api/v1/opportunities/${id}`,query), apiGet<InvestmentMemo>(`/api/v1/opportunities/${id}/investment-memo`,query), apiGet<LaunchReadiness>(`/api/v1/opportunities/${id}/launch-readiness`,query), apiGet<OpportunityEvidence[]>("/api/v1/opportunity-evidence",query), apiGet<OpportunityScore[]>("/api/v1/opportunity-scores",query), apiGet<OpportunityRisk[]>("/api/v1/opportunity-risks",query), apiGet<ApprovalRequest[]>("/api/v1/approvals",query), apiGet<DecisionQueueRecord[]>("/api/v1/decision-queue",query),
  ]);
  return {opportunity,memo,readiness,evidence,scores,risks,approvals,decisions};
}

export async function getDiscoveryOpportunityDetail(id:string,organizationId:string) {
  const query={organization_id:organizationId};
  const [opportunity,evidence,assessment,decisions]=await Promise.all([
    apiGet<DiscoveryOpportunity>(`/api/v1/opportunity-candidates/${id}`,query), apiGet<CandidateEvidence[]>(`/api/v1/opportunities/${id}/evidence`,query), apiGet<CandidateAssessment>(`/api/v1/opportunities/${id}/assessment`,query), apiGet<DecisionQueueRecord[]>("/api/v1/decision-queue",query),
  ]);
  return {opportunity,evidence,assessment,decisions};
}
