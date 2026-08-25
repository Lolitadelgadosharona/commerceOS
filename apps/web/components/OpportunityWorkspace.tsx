import Link from "next/link";
import type { ApiResult } from "../lib/api/types";
import { isDiscoveryOpportunity, type ApprovalRequest, type DecisionQueueRecord, type Opportunity, type OpportunityRisk, type OpportunityScore } from "../lib/api/opportunities";

function statusMeaning(item:Opportunity,approval:ApprovalRequest|undefined):string {
  if(approval?.status==="pending") return "Waiting for human decision";
  if(approval?.status==="approved") return "Investment approved · readiness review next";
  if(approval?.status==="rejected") return "Investment rejected";
  if(isDiscoveryOpportunity(item)&&item.status==="accepted") return "Accepted intelligence candidate · not yet executable";
  return item.status.replaceAll("_"," ");
}

export function OpportunityWorkspace({opportunities,scores,risks,approvals,decisions,focusApproval}:{opportunities:ApiResult<Opportunity[]>;scores:ApiResult<OpportunityScore[]>;risks:ApiResult<OpportunityRisk[]>;approvals:ApiResult<ApprovalRequest[]>;decisions:ApiResult<DecisionQueueRecord[]>;focusApproval?:string}) {
  if(!opportunities.ok) return <div className="module-page"><section className="page-heading"><div><p className="eyebrow">Intelligence → Decision</p><h1>Opportunity workspace</h1></div></section><div className="dashboard-state state-error"><strong>Opportunity workspace unavailable</strong><span>{opportunities.error.message}</span></div></div>;
  const approvalRows=approvals.ok?approvals.data.filter((row)=>row.object_type==="market_opportunity"&&row.requested_action==="approve_investment"):[];
  const focus=focusApproval?approvalRows.find((row)=>row.id===focusApproval):undefined;
  const items=[...opportunities.data].sort((a,b)=>{
    const aScore=isDiscoveryOpportunity(a)?a.advisory_score:scores.ok?scores.data.find((score)=>score.opportunity_id===a.id)?.overall_score??-1:-1;
    const bScore=isDiscoveryOpportunity(b)?b.advisory_score:scores.ok?scores.data.find((score)=>score.opportunity_id===b.id)?.overall_score??-1:-1;
    return bScore-aScore;
  });
  return <div className="opportunity-workspace">
    <section className="page-heading"><div><p className="eyebrow">Sense → Decide → Human approval</p><h1>Opportunity workspace</h1><p className="page-description">Trace demand evidence into governed investment decisions without confusing intelligence candidates with execution-ready opportunities.</p></div><div className="live-contract"><span>Source of truth</span><strong>Commerce OS Opportunity APIs</strong></div></section>
    {focus&&<Link className="focus-approval" href={`/opportunities/${focus.object_id}?kind=market`}><span>Decision Queue context</span><strong>{focus.reason}</strong><small>Open the linked opportunity →</small></Link>}
    <section className="opportunity-summary" aria-label="Opportunity summary"><article><span>Total records</span><strong>{items.length}</strong></article><article><span>Needs research</span><strong>{items.filter((item)=>isDiscoveryOpportunity(item)&&item.missing_evidence.length>0).length}</strong></article><article><span>Waiting for decision</span><strong>{approvalRows.filter((row)=>row.status==="pending").length}</strong></article><article><span>Approved investments</span><strong>{approvalRows.filter((row)=>row.status==="approved").length}</strong></article></section>
    {!items.length?<div className="dashboard-state"><strong>No opportunities yet</strong><span>Demand and research evidence have not produced an Opportunity record for this organization.</span></div>:<section className="opportunity-list" aria-label="Opportunities">{items.map((item)=>{
      const discovery=isDiscoveryOpportunity(item), score=discovery?item.advisory_score:scores.ok?(scores.data.find((row)=>row.opportunity_id===item.id)?.overall_score??null):null;
      const approval=discovery?undefined:approvalRows.find((row)=>row.object_id===item.id), riskCount=discovery?item.risk_summary.length:risks.ok?risks.data.filter((row)=>row.opportunity_id===item.id&&row.status==="open").length:null;
      const queue=discovery&&item.decision_queue_item_id&&decisions.ok?decisions.data.find((row)=>row.id===item.decision_queue_item_id):approval&&decisions.ok?decisions.data.find((row)=>row.approval_request_id===approval.id):undefined;
      return <Link className="opportunity-row" href={`/opportunities/${item.id}?kind=${discovery?"candidate":"market"}`} key={item.id}><div className="opportunity-kind"><span>{discovery?"Demand candidate":"Market opportunity"}</span><i className={discovery?"candidate-dot":"market-dot"}/></div><div className="opportunity-main"><h2>{item.title}</h2><p>{discovery?item.problem_statement:item.description}</p><div className="opportunity-tags"><span>{item.category}</span><span>{Math.round(item.confidence_score*100)}% confidence</span>{queue&&<span>Decision Queue: {queue.status}</span>}</div></div><div className="opportunity-measures"><div><span>Score</span><strong>{score??"—"}</strong></div><div><span>Open risks</span><strong>{riskCount??"—"}</strong></div></div><div className="opportunity-status"><span>{statusMeaning(item,approval)}</span><strong>Evaluate →</strong></div></Link>;
    })}</section>}
    {(!scores.ok||!risks.ok||!approvals.ok||!decisions.ok)&&<div className="partial-data-note">Some supporting Opportunity sources are unavailable. Core records remain visible; unsupported values are shown as —.</div>}
  </div>;
}
