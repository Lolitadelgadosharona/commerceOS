export type MetricContract = {
  label: string;
  value: string;
  change: string;
  tone?: "neutral" | "positive" | "warning";
};

export type QueueItemContract = {
  title: string;
  detail: string;
  status: "Ready" | "Review" | "Monitoring" | "Draft" | "Blocked";
};

export type ModuleContract = {
  eyebrow: string;
  title: string;
  description: string;
  endpoint: string;
  metrics: MetricContract[];
  queueTitle: string;
  queue: QueueItemContract[];
  insightTitle: string;
  insight: string;
};

export const moduleContracts: Record<string, ModuleContract> = {
  dashboard: {
    eyebrow: "Executive command",
    title: "Operating dashboard",
    description: "A governed view of the signals, decisions, and revenue work that need attention now.",
    endpoint: "GET /api/v1/executive-metrics",
    metrics: [
      { label: "Open signals", value: "12", change: "3 require review", tone: "warning" },
      { label: "Decision queue", value: "5", change: "2 high priority" },
      { label: "Active experiments", value: "4", change: "Across 2 markets", tone: "positive" },
      { label: "System confidence", value: "86%", change: "Evidence coverage" },
    ],
    queueTitle: "Need your decision",
    queue: [
      { title: "Review Beauty visibility opportunity", detail: "18 evidence records · confidence 84%", status: "Review" },
      { title: "Approve Growth Gift package", detail: "Luna Brow Studio · ready for founder review", status: "Ready" },
      { title: "Resolve supplier quality risk", detail: "Product candidate PC-104 · medium severity", status: "Blocked" },
    ],
    insightTitle: "Operating brief",
    insight: "Customer demand is strengthening in two validated clusters. Keep external execution paused until the related evidence and margin assumptions are reviewed.",
  },
  opportunities: {
    eyebrow: "Intelligence → Decision",
    title: "Opportunity pipeline",
    description: "Evaluate evidence-backed opportunities without turning demand signals into automatic business actions.",
    endpoint: "GET /api/v1/opportunity-candidates",
    metrics: [
      { label: "New candidates", value: "8", change: "This review cycle", tone: "positive" },
      { label: "In review", value: "6", change: "4 have complete evidence" },
      { label: "Missing evidence", value: "3", change: "Research required", tone: "warning" },
      { label: "Approved", value: "2", change: "Human governed" },
    ],
    queueTitle: "Priority opportunities",
    queue: [
      { title: "Heat-resilient pet travel", detail: "4 independent sources · strong demand diversity", status: "Review" },
      { title: "Pet memorial keepsake systems", detail: "Customer language and marketplace evidence linked", status: "Ready" },
      { title: "Beauty GEO optimization", detail: "GrowthOS signal bridge · advisory only", status: "Monitoring" },
    ],
    insightTitle: "Evidence rule",
    insight: "Demand is not an opportunity. Candidates remain advisory until market context, economics, risks, and missing evidence are explicitly reviewed.",
  },
  customers: {
    eyebrow: "Operations truth",
    title: "Customer intelligence",
    description: "Unify customer journeys, conversations, intent, value, and support signals without replacing source systems.",
    endpoint: "GET /api/v1/customer-360",
    metrics: [
      { label: "Known customers", value: "1,284", change: "Across verified identities" },
      { label: "High intent", value: "47", change: "Evidence-backed", tone: "positive" },
      { label: "Open handoffs", value: "9", change: "Human action required", tone: "warning" },
      { label: "Repeat potential", value: "31%", change: "Advisory projection" },
    ],
    queueTitle: "Customer signals",
    queue: [
      { title: "Delivery concern cluster", detail: "7 conversations · increasing frequency", status: "Review" },
      { title: "High-value account handoff", detail: "Complex negotiation · human authority required", status: "Ready" },
      { title: "Product usage questions", detail: "Knowledge coverage under review", status: "Monitoring" },
    ],
    insightTitle: "Projection boundary",
    insight: "Customer 360 is a read-only projection. Operations owns interaction truth, while Finance remains authoritative for actual revenue and lifetime value.",
  },
  "market-intelligence": {
    eyebrow: "Evidence first",
    title: "Market intelligence",
    description: "Monitor observed, customer voice, marketplace, trend, and predictive signals with complete provenance.",
    endpoint: "GET /api/v1/market-signals",
    metrics: [
      { label: "Signals captured", value: "2,418", change: "30-day window" },
      { label: "Rising themes", value: "14", change: "6 multi-source", tone: "positive" },
      { label: "Low confidence", value: "22", change: "Evidence review", tone: "warning" },
      { label: "Source diversity", value: "7", change: "Independent types" },
    ],
    queueTitle: "Emerging themes",
    queue: [
      { title: "Summer pet cooling demand", detail: "Search + social + weather evidence", status: "Monitoring" },
      { title: "Review-driven trust gaps", detail: "Marketplace complaints across 3 categories", status: "Review" },
      { title: "Beauty local discovery", detail: "Customer voice and research signals aligned", status: "Ready" },
    ],
    insightTitle: "Signal integrity",
    insight: "Every signal contributes evidence. No single forecast, review, social comment, or research summary can independently create an opportunity or action.",
  },
  growth: {
    eyebrow: "Founder-operated revenue",
    title: "Growth experiments",
    description: "Run evidence-backed prospect, Gift, outreach, conversation, delivery, and learning workflows with human control.",
    endpoint: "GET /api/v1/revenue-experiments/{id}/live-analytics",
    metrics: [
      { label: "Prospects reviewed", value: "28", change: "Beauty Experiment 001" },
      { label: "Gifts approved", value: "11", change: "Founder approved", tone: "positive" },
      { label: "Replies", value: "4", change: "2 positive" },
      { label: "Paid revenue", value: "$0", change: "Finance truth only" },
    ],
    queueTitle: "Founder action center",
    queue: [
      { title: "Review 6 ranked prospects", detail: "Los Angeles · Beauty · evidence attached", status: "Review" },
      { title: "Approve Luna Brow Growth Gift", detail: "GEO visibility diagnosis complete", status: "Ready" },
      { title: "Analyze customer reply", detail: "Timing objection · Sales Copilot draft available", status: "Draft" },
    ],
    insightTitle: "Human authority",
    insight: "GrowthOS prepares decisions and drafts. The founder approves and performs every external communication, commercial commitment, and customer action.",
  },
  products: {
    eyebrow: "Build truth",
    title: "Product foundation",
    description: "Move approved candidates into governed product truth, claims, knowledge, suppliers, and launch readiness.",
    endpoint: "GET /api/v1/products",
    metrics: [
      { label: "Product candidates", value: "9", change: "3 in evaluation" },
      { label: "Approved products", value: "4", change: "Product Truth active", tone: "positive" },
      { label: "Claim reviews", value: "6", change: "Evidence required", tone: "warning" },
      { label: "Launch ready", value: "2", change: "All gates satisfied" },
    ],
    queueTitle: "Product readiness",
    queue: [
      { title: "Review Product Truth v3", detail: "2 new approved claims · evidence linked", status: "Review" },
      { title: "Supplier match assessment", detail: "Quality and compliance checks complete", status: "Ready" },
      { title: "Listing evidence coverage", detail: "FAQ and limitation gaps remain", status: "Blocked" },
    ],
    insightTitle: "Truth boundary",
    insight: "Only approved, versioned Product Truth may support claims, listings, creative, or customer communication. Candidates and AI drafts are not product truth.",
  },
  decisions: {
    eyebrow: "Governance authority",
    title: "Decision committee",
    description: "Centralize high-impact reviews while keeping AI recommendations separate from human approval authority.",
    endpoint: "GET /api/v1/decision-queue",
    metrics: [
      { label: "Awaiting review", value: "5", change: "2 high priority", tone: "warning" },
      { label: "Approved today", value: "3", change: "All audited", tone: "positive" },
      { label: "Risk reviews", value: "4", change: "Cross-domain" },
      { label: "SLA health", value: "92%", change: "Within 24 hours" },
    ],
    queueTitle: "Committee queue",
    queue: [
      { title: "Opportunity GO / TEST decision", detail: "Demand 82 · risk 31 · margin evidence pending", status: "Review" },
      { title: "Product claim approval", detail: "Performance claim · supporting evidence attached", status: "Ready" },
      { title: "Pricing exception", detail: "Finance and Growth review required", status: "Blocked" },
    ],
    insightTitle: "Authority rule",
    insight: "AI may recommend, summarize, classify, and draft. It cannot approve itself, move money, publish, change prices, or bypass the assigned human authority.",
  },
  analytics: {
    eyebrow: "Measure → Learn",
    title: "Performance analytics",
    description: "Connect observations to explainable learning without allowing projections to overwrite domain truth.",
    endpoint: "GET /api/v1/executive-metrics",
    metrics: [
      { label: "Learning signals", value: "34", change: "12 accepted" },
      { label: "Experiments complete", value: "7", change: "This quarter", tone: "positive" },
      { label: "Evidence coverage", value: "81%", change: "+6 points" },
      { label: "Open anomalies", value: "3", change: "Needs review", tone: "warning" },
    ],
    queueTitle: "Learning observations",
    queue: [
      { title: "Gift-first outreach pattern", detail: "Positive across two Beauty segments", status: "Monitoring" },
      { title: "Price objection frequency", detail: "Insufficient evidence for conclusion", status: "Review" },
      { title: "Customer language update", detail: "Accepted feedback ready for reuse", status: "Ready" },
    ],
    insightTitle: "Learning boundary",
    insight: "Observations and recommendations stay traceable to source evidence. Learning can improve future decisions but cannot silently modify Product, Customer, or Finance truth.",
  },
};
