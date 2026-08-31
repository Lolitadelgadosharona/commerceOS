import type { Metadata } from "next";
import { DashboardConfigurationState } from "../../components/DashboardConfigurationState";
import { ProductIntelligenceWorkspace } from "../../components/ProductIntelligenceWorkspace";
import { resolveExecutiveContext } from "../../lib/api/context";
import { getProductWorkspace } from "../../lib/api/commerce-intelligence";

export const metadata: Metadata = { title: "Products" };

export default async function ProductsPage() {
  const context=await resolveExecutiveContext();
  if(!context.ok)return <DashboardConfigurationState message={context.error.message}/>;
  return <ProductIntelligenceWorkspace {...await getProductWorkspace(context.data.organization_id)}/>;
}
