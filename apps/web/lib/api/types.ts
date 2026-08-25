export type ReadModel = {
  id: string;
  version: number;
  created_at: string;
  updated_at: string;
};

export type ExecutiveMetric = ReadModel & {
  organization_id: string;
  metric_type: "revenue" | "profit" | "customer" | "product" | "creative" | "channel" | "risk";
  metric_name: string;
  value: number;
  unit: string;
  source_domain: string;
  period_id: string;
};

export type OperatingSignal = ReadModel & {
  organization_id: string;
  domain: string;
  severity: "info" | "warning" | "critical";
  title: string;
  description: string;
  impact: string;
  recommendation: string;
  status: string;
};

export type DecisionQueueItem = ReadModel & {
  organization_id: string;
  title: string;
  domain: string;
  reason: string;
  priority: "low" | "medium" | "high" | "critical";
  required_action: "approve" | "review" | "reject";
  status: string;
  approval_request_id: string | null;
};

export type DashboardViewName =
  | "executive-overview"
  | "need-your-decision"
  | "financial-health"
  | "product-opportunities"
  | "customer-health"
  | "creative-performance"
  | "channel-performance"
  | "risk-overview";

export type DashboardView = {
  organization_id: string;
  view: DashboardViewName;
  metrics: ExecutiveMetric[];
  signals: OperatingSignal[];
  decisions: DecisionQueueItem[];
  strategic_account_indicators: Record<string, number>;
};

export type AuthenticatedActor = {
  user_id: string;
  organization_id: string;
  principal_type: string;
};

export type ApiFailureKind = "configuration" | "authentication" | "authorization" | "network" | "response" | "contract";

export type ApiFailure = {
  kind: ApiFailureKind;
  message: string;
  status?: number;
};

export type ApiResult<T> = { ok: true; data: T } | { ok: false; error: ApiFailure };
