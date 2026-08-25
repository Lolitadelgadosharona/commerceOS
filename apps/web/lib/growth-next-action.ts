export type ProspectState = {
  evidence: number;
  research: "missing" | "queued" | "running" | "completed" | "failed";
  opportunity: boolean;
  diagnosis: boolean;
  gift: "missing" | "draft" | "pending" | "approved";
  outreach: "missing" | "draft" | "pending" | "approved" | "sent";
  outcome: boolean;
};

export type NextAction = { label: string; detail: string; anchor: string; state: "ready" | "waiting" | "blocked" };

export function nextFounderAction(state: ProspectState): NextAction {
  if (!state.evidence) return { label: "Add evidence", detail: "At least one traceable observation is required.", anchor: "evidence", state: "blocked" };
  if (state.research === "failed") return { label: "Review failed research", detail: "Keep the evidence, inspect the failure, then retry intentionally.", anchor: "evidence", state: "blocked" };
  if (["queued", "running"].includes(state.research)) return { label: "Research in progress", detail: "The durable worker is processing the governed request.", anchor: "evidence", state: "waiting" };
  if (!state.opportunity || !state.diagnosis) return { label: "Create diagnosis", detail: "Compose an evidence-backed opportunity and diagnosis.", anchor: "diagnosis", state: "ready" };
  if (state.gift === "missing") return { label: "Create Growth Gift", detail: "Turn the reviewed diagnosis into a customer-specific useful artifact.", anchor: "growth-gift", state: "ready" };
  if (state.gift === "draft") return { label: "Request Gift approval", detail: "A human approval is required before delivery preparation.", anchor: "approvals", state: "ready" };
  if (state.gift === "pending") return { label: "Await Gift decision", detail: "Approval does not send or publish anything.", anchor: "approvals", state: "waiting" };
  if (state.outreach === "missing") return { label: "Create outreach draft", detail: "Use the approved Gift and evidence; nothing will be sent.", anchor: "outreach", state: "ready" };
  if (state.outreach === "draft") return { label: "Request outreach approval", detail: "A separate authorized human reviews the message.", anchor: "approvals", state: "ready" };
  if (state.outreach === "pending") return { label: "Await outreach decision", detail: "The draft remains blocked from manual execution.", anchor: "approvals", state: "waiting" };
  if (state.outreach === "approved") return { label: "Send manually", detail: "Copy the approved draft, send outside Commerce OS, then record the fact.", anchor: "outcomes", state: "ready" };
  if (!state.outcome) return { label: "Record outcome", detail: "Record the observed reply, follow-up, or conversion.", anchor: "outcomes", state: "ready" };
  return { label: "Review learning", detail: "Turn the observed result into evidence for the next experiment.", anchor: "learning", state: "ready" };
}
