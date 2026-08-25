import { createServer } from "node:http";

const organizationId = "11111111-1111-4111-8111-111111111111";
const userId = "22222222-2222-4222-8222-222222222222";
let scenario = "success";

const base = { organization_id: organizationId, version: 1, created_at: "2026-08-24T12:00:00Z", updated_at: "2026-08-24T12:00:00Z" };
const metric = (id, metric_type, metric_name, value, unit, source_domain) => ({ ...base, id, metric_type, metric_name, value, unit, source_domain, period_id: "33333333-3333-4333-8333-333333333333" });
const signal = (id, domain, severity, title, impact) => ({ ...base, id, domain, severity, title, description: title, impact, recommendation: "Review the source evidence.", status: "open" });
const decision = { ...base, id: "66666666-6666-4666-8666-666666666666", title: "Review contribution margin risk", domain: "finance", reason: "Human review is required before action.", priority: "high", required_action: "review", status: "pending", approval_request_id: null };

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
  response.writeHead(404).end();
}).listen(4100, "127.0.0.1");
