"use client";

import { useActionState } from "react";
import { decideInvestmentReview, requestInvestmentReview, type DecisionActionState } from "../app/opportunities/actions";
import type { ApprovalRequest } from "../lib/api/opportunities";

function ActionMessage({kind,message}:{kind:string;message:string}) { return message?<p className={`action-message action-${kind}`} role="status">{message}</p>:null; }
const initialDecisionState:DecisionActionState={kind:"idle",message:""};

export function InvestmentDecisionPanel({opportunityId,approval,currentUserId,recommendation,readiness}:{opportunityId:string;approval:ApprovalRequest|null;currentUserId:string;recommendation:string;readiness:string}) {
  const [requestState,requestAction,requestPending]=useActionState(requestInvestmentReview,initialDecisionState);
  const [decisionState,decisionAction,decisionPending]=useActionState(decideInvestmentReview,initialDecisionState);
  if(!approval) return <section className="investment-action-panel"><p className="eyebrow">Human authority</p><h2>Request Investment Committee review</h2><p>The current committee recommendation is <strong>{recommendation}</strong>. Creating this request adds a real pending Approval Request and Decision Queue item.</p><form action={requestAction}><input type="hidden" name="opportunity_id" value={opportunityId}/><label>Reason for human review<textarea name="reason" required minLength={1} placeholder="Explain why this opportunity is ready for an investment decision."/></label><button className="primary-button" disabled={requestPending}>{requestPending?"Submitting…":"Request governed review"}</button></form><ActionMessage {...requestState}/></section>;
  if(approval.status!=="pending") return <section className="investment-action-panel"><p className="eyebrow">Human decision recorded</p><h2>{approval.status}</h2><p>{approval.decision_reason??"The governance record contains the authoritative decision."}</p><div className="decision-consequence"><span>Execution readiness</span><strong>{readiness}</strong></div></section>;
  const selfReview=approval.requester_id===currentUserId;
  return <section className="investment-action-panel"><p className="eyebrow">Pending human approval</p><h2>Investment decision required</h2><p>Review the evidence, committee recommendation <strong>{recommendation}</strong>, and readiness state <strong>{readiness}</strong> before deciding.</p>{selfReview?<div className="dashboard-state compact state-error"><strong>Separation of authority enforced</strong><span>The requester cannot decide their own approval. Another authorized human approver must review it.</span></div>:<form action={decisionAction}><input type="hidden" name="opportunity_id" value={opportunityId}/><input type="hidden" name="approval_id" value={approval.id}/><label>Decision reason<textarea name="reason" required placeholder="Record the evidence-based reason for this decision."/></label><div className="decision-buttons"><button className="primary-button" name="decision" value="approved" disabled={decisionPending}>Approve investment</button><button className="danger-button" name="decision" value="rejected" disabled={decisionPending}>Reject</button></div></form>}<ActionMessage {...decisionState}/></section>;
}
