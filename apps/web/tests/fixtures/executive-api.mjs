import { createServer } from "node:http";

const organizationId = "11111111-1111-4111-8111-111111111111";
const userId = "22222222-2222-4222-8222-222222222222";
const marketId = "77777777-7777-4777-8777-777777777777";
const candidateId = "88888888-8888-4888-8888-888888888888";
const approvalId = "99999999-9999-4999-8999-999999999999";
let scenario = "success";
let approvalStatus = "pending";

const base = { organization_id: organizationId, version: 1, created_at: "2026-08-24T12:00:00Z", updated_at: "2026-08-24T12:00:00Z" };
const metric = (id, metric_type, metric_name, value, unit, source_domain) => ({ ...base, id, metric_type, metric_name, value, unit, source_domain, period_id: "33333333-3333-4333-8333-333333333333" });
const signal = (id, domain, severity, title, impact) => ({ ...base, id, domain, severity, title, description: title, impact, recommendation: "Review the source evidence.", status: "open" });
const decision = { ...base, id: "66666666-6666-4666-8666-666666666666", title: "Investment decision: Seasonal pet cooling mat", domain: "decision", reason: "Human review is required before action.", priority: "high", required_action: "approve", status: "pending", approval_request_id: approvalId };
const marketOpportunity = { ...base, id:marketId, title:"Seasonal pet cooling mat", description:"Owners report recurring heat discomfort during summer travel.", category:"pet", market:"consumer", geography:"US", trigger_type:"seasonal_event", timing_window:"summer", status:"qualified", confidence_score:.82 };
const candidateOpportunity = { ...base, id:candidateId, discovery_run_id:null, title:"Travel hydration reminder", category:"pet", problem_statement:"Owners forget hydration during long journeys.", customer_segment:"Traveling pet owners", opportunity_description:"An evidence-backed product direction for travel hydration.", market_context:"Recurring customer voice signals.", evidence_summary:"Two reviewed demand signals.", evidence_references:[{type:"customer_pain",id:"signal-1"}], solution_direction:"Portable reminder product", customer_language:["I forget water on long drives"], confidence_score:.74, risk_summary:["Adoption uncertainty"], open_questions:[], missing_evidence:["Marketplace validation"], advisory_score:74, status:"under_review", methodology_version:"deterministic-demand-opportunity-v1", decision_queue_item_id:null };
const approval = () => ({ ...base, id:approvalId, project_id:null, requester_id:"aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa", object_type:"market_opportunity", object_id:marketId, requested_action:"approve_investment", reason:"Evidence and economics require human investment review.", status:approvalStatus, approver_id:approvalStatus==="pending"?null:userId, decision_time:approvalStatus==="pending"?null:"2026-08-24T13:00:00Z", decision_reason:approvalStatus==="pending"?null:"Evidence supports a controlled next step." });
const marketScore = { ...base, id:"12121212-1212-4212-8212-121212121212", opportunity_id:marketId, demand_score:82, pain_score:78, trend_score:75, margin_score:68, competition_score:56, ip_risk_score:22, dispute_risk_score:18, overall_score:72.4, formula_version:"opportunity-score-v1" };
const marketRisk = { ...base, id:"13131313-1313-4313-8313-131313131313", opportunity_id:marketId, risk_type:"policy", severity:"medium", description:"Platform policy evidence requires validation.", status:"open" };
const marketEvidence = { ...base, id:"14141414-1414-4414-8414-141414141414", opportunity_id:marketId, source_type:"customer_signal", source_reference:"customer-signal:heat-1", evidence_summary:"Owners report pet heat discomfort during summer travel.", confidence_score:.85 };
const candidateEvidence = { ...base, id:"15151515-1515-4515-8515-151515151515", opportunity_candidate_id:candidateId, demand_signal_id:"16161616-1616-4616-8616-161616161616", evidence_type:"customer_pain", evidence_summary:"Hydration is forgotten during long journeys.", contribution:"12 observations; customer voice", confidence:.74 };
const candidateAssessment = { ...base, id:"17171717-1717-4717-8717-171717171717", opportunity_candidate_id:candidateId, demand_strength:"medium", signal_diversity:2, market_timing:"Travel season", confidence:.74, risks:["Adoption uncertainty"], missing_information:["Marketplace validation"], assumptions:["Observed pain generalizes beyond the sample"] };

const memo = { opportunity_id:marketId, organization_id:organizationId, summary:{title:marketOpportunity.title,description:marketOpportunity.description,why_now:"summer",assessment:{overall_score:72.4,explanation:"Demand evidence is credible but incomplete."},report:{status:"presented",summary:"Proceed only after policy and economics review.",risk_summary:"Platform policy evidence remains incomplete."}}, evidence:[marketEvidence], conclusions:{commercial_viability:{classification:"derived",value:{recommendation:"test",adjusted_score:68}},risk:{classification:"derived",value:{risk_level:"medium",risk_score:32}},economic_assumptions:{classification:"estimated",value:{product_cost:12,shipping_cost:5,currency:"USD"}},profit_scenarios:{classification:"estimated",value:{scenario:"base",margin:0.35}},risk_adjusted_profitability:{classification:"derived",value:{final_score:64,recommendation:"review"}}}, missing_evidence:["Customer evidence is required"], confidence:.58, recommended_decision:"hold" };
const readiness = { opportunity_id:marketId, overall_status:"missing", blocking_reasons:["Customer evidence is required"], categories:[{category:"market_evidence",status:"ready",reason:"Available",references:[marketEvidence.id],blocking:true},{category:"customer_evidence",status:"missing",reason:"Customer evidence is required",references:[],blocking:true},{category:"economics",status:"ready",reason:"Available",references:[],blocking:true},{category:"governance",status:"ready",reason:"Available",references:[],blocking:true}] };

function dashboard(view) {
  if (scenario === "empty") return { organization_id: organizationId, view, metrics: [], signals: [], decisions: [], strategic_account_indicators: {} };
  const views = {
    "executive-overview": { metrics: [metric("44444444-4444-4444-8444-444444444441", "customer", "Active customer signals", 7, "signals", "intelligence")], signals: [signal("55555555-5555-4555-8555-555555555551", "operations", "warning", "Delivery concerns rising", "Customer trust may decline.")], decisions: [decision] },
    "financial-health": { metrics: [metric("44444444-4444-4444-8444-444444444442", "revenue", "Observed revenue", 12500, "USD", "finance"), metric("44444444-4444-4444-8444-444444444443", "profit", "Contribution profit", 4100, "USD", "finance")], signals: [], decisions: [] },
    "product-opportunities": { metrics: [metric("44444444-4444-4444-8444-444444444444", "product", "Reviewed product opportunities", 3, "candidates", "decision")], signals: [signal("55555555-5555-4555-8555-555555555552", "intelligence", "info", "Customer-backed opportunity ready", "Evidence is ready for human review.")], decisions: [] },
    "risk-overview": { metrics: [metric("44444444-4444-4444-8444-444444444445", "risk", "Open risk observations", 2, "signals", "decision")], signals: [signal("55555555-5555-4555-8555-555555555553", "finance", "critical", "Margin compression", "Contribution profit is at risk.")], decisions: [decision] },
    "need-your-decision": { metrics: [], signals: [], decisions: [decision] },
  };
  return { organization_id: organizationId, view, ...(views[view] ?? { metrics: [], signals: [], decisions: [] }), strategic_account_indicators: {} };
}

createServer((request, response) => {
  if (request.method === "POST" && request.url?.startsWith("/__scenario/")) {
    scenario = request.url.split("/").at(-1) ?? "success";
    approvalStatus = "pending";
    response.writeHead(204).end();
    return;
  }
  if (request.url === "/api/v1/health") {
    response.writeHead(200, { "content-type": "application/json" }).end(JSON.stringify({ status: "ok" }));
    return;
  }
  if (request.headers.authorization !== "Bearer test-dashboard-token") {
    response.writeHead(401, { "content-type": "application/json" }).end(JSON.stringify({ error: "unauthenticated" }));
    return;
  }
  if (request.url === "/api/v1/auth/me") {
    if (scenario === "unauthorized") { response.writeHead(403, { "content-type":"application/json" }).end(JSON.stringify({error:"permission_denied"})); return; }
    response.writeHead(200, { "content-type": "application/json" }).end(JSON.stringify({ user_id: userId, organization_id: organizationId, principal_type: "human" }));
    return;
  }
  const match = request.url?.match(/^\/api\/v1\/dashboard\/([^?]+)/);
  if (match) {
    if (scenario === "partial" && match[1] === "financial-health") {
      response.writeHead(503, { "content-type": "application/json" }).end(JSON.stringify({ error: "unavailable" }));
      return;
    }
    response.writeHead(200, { "content-type": "application/json" }).end(JSON.stringify(dashboard(match[1])));
    return;
  }
  const url = new URL(request.url ?? "/", "http://127.0.0.1:4100");
  const json = (status, value) => response.writeHead(status, { "content-type":"application/json" }).end(JSON.stringify(value));
  if (url.pathname === "/api/v1/opportunities" && request.method === "GET") {
    if (scenario === "opportunity-error") return json(503,{error:"unavailable"});
    return json(200,scenario === "empty"?[]:[candidateOpportunity,marketOpportunity]);
  }
  if (url.pathname === `/api/v1/opportunities/${marketId}` && request.method === "GET") return json(200,marketOpportunity);
  if (url.pathname.startsWith("/api/v1/opportunities/") && url.pathname.endsWith("/investment-memo")) return url.pathname.includes(marketId)?json(200,memo):json(404,{error:"not_found"});
  if (url.pathname.startsWith("/api/v1/opportunities/") && url.pathname.endsWith("/launch-readiness")) return url.pathname.includes(marketId)?json(200,readiness):json(404,{error:"not_found"});
  if (url.pathname === `/api/v1/opportunity-candidates/${candidateId}`) return json(200,candidateOpportunity);
  if (url.pathname === `/api/v1/opportunities/${candidateId}/evidence`) return json(200,[candidateEvidence]);
  if (url.pathname === `/api/v1/opportunities/${candidateId}/assessment`) return json(200,candidateAssessment);
  if (url.pathname.match(/^\/api\/v1\/opportunities\/[0-9a-f-]+$/) && request.method === "GET") return json(404,{error:"not_found"});
  if (url.pathname === "/api/v1/opportunity-evidence") return json(200,scenario === "empty"?[]:[marketEvidence]);
  if (url.pathname === "/api/v1/opportunity-scores") return json(200,scenario === "empty"?[]:[marketScore]);
  if (url.pathname === "/api/v1/opportunity-risks") return json(200,scenario === "empty"?[]:[marketRisk]);
  if (url.pathname === "/api/v1/approvals" && request.method === "GET") return json(200,scenario === "empty"?[]:[approval()]);
  if (url.pathname === "/api/v1/decision-queue") return json(200,scenario === "empty"?[]:[decision]);
  if (url.pathname === `/api/v1/approvals/${approvalId}/decision` && request.method === "POST") { approvalStatus="approved"; return json(200,approval()); }
  response.writeHead(404).end();
}).listen(4100, "127.0.0.1");
