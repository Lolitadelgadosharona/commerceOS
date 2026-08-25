import type { Metadata } from "next";
import { DashboardConfigurationState } from "../../components/DashboardConfigurationState";
import { OpportunityWorkspace } from "../../components/OpportunityWorkspace";
import { resolveExecutiveContext } from "../../lib/api/context";
import { getOpportunityWorkspace } from "../../lib/api/opportunities";

export const metadata: Metadata = { title: "Opportunities" };

export default async function OpportunitiesPage({searchParams}:{searchParams:Promise<{approval?:string}>}) {
  const context=await resolveExecutiveContext();
  if(!context.ok) return <DashboardConfigurationState message={context.error.message}/>;
  const workspace=await getOpportunityWorkspace(context.data.organization_id);
  const {approval}=await searchParams;
  return <OpportunityWorkspace {...workspace} focusApproval={approval}/>;
}
