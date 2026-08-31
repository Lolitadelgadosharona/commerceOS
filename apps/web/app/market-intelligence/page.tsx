import type { Metadata } from "next";
import { DashboardConfigurationState } from "../../components/DashboardConfigurationState";
import { MarketIntelligenceWorkspace } from "../../components/MarketIntelligenceWorkspace";
import { resolveExecutiveContext } from "../../lib/api/context";
import { getMarketIntelligenceWorkspace } from "../../lib/api/commerce-intelligence";

export const metadata: Metadata = { title: "Market Intelligence" };

export default async function MarketIntelligencePage() {
  const context=await resolveExecutiveContext();
  if(!context.ok)return <DashboardConfigurationState message={context.error.message}/>;
  return <MarketIntelligenceWorkspace {...await getMarketIntelligenceWorkspace(context.data.organization_id)}/>;
}
