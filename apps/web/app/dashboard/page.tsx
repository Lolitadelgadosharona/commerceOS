import type { Metadata } from "next";
import { DashboardConfigurationState } from "../../components/DashboardConfigurationState";
import { ExecutiveDashboard } from "../../components/ExecutiveDashboard";
import { resolveExecutiveContext } from "../../lib/api/context";
import { getDashboardView } from "../../lib/api/executive";

export const metadata: Metadata = { title: "Executive Dashboard" };

export default async function DashboardPage() {
  const context = await resolveExecutiveContext();
  if (!context.ok) return <DashboardConfigurationState message={context.error.message} />;
  const organizationId = context.data.organization_id;
  const [overview, financial, opportunities, risks, decisions] = await Promise.all([
    getDashboardView("executive-overview", organizationId),
    getDashboardView("financial-health", organizationId),
    getDashboardView("product-opportunities", organizationId),
    getDashboardView("risk-overview", organizationId),
    getDashboardView("need-your-decision", organizationId),
  ]);
  return <ExecutiveDashboard overview={overview} financial={financial} opportunities={opportunities} risks={risks} decisions={decisions} />;
}
