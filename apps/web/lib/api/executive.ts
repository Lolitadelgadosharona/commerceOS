import "server-only";
import { apiGet } from "./client";
import type { ApiResult, DashboardView, DashboardViewName } from "./types";

function isDashboardView(value: unknown, expectedView: DashboardViewName): value is DashboardView {
  if (!value || typeof value !== "object") return false;
  const view = value as Partial<DashboardView>;
  return view.view === expectedView && typeof view.organization_id === "string" && Array.isArray(view.metrics) && Array.isArray(view.signals) && Array.isArray(view.decisions) && typeof view.strategic_account_indicators === "object";
}

export async function getDashboardView(view: DashboardViewName, organizationId: string): Promise<ApiResult<DashboardView>> {
  const result = await apiGet<unknown>(`/api/v1/dashboard/${view}`, { organization_id: organizationId });
  if (!result.ok) return result;
  if (!isDashboardView(result.data, view) || result.data.organization_id !== organizationId) {
    return { ok: false, error: { kind: "contract", message: `The ${view} response did not match the Executive Dashboard contract.` } };
  }
  return { ok: true, data: result.data };
}
