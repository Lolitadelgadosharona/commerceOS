import type { Metadata } from "next";
import { DashboardConfigurationState } from "../../components/DashboardConfigurationState";
import { DecisionCommitteeWorkspace } from "../../components/DecisionCommitteeWorkspace";
import { resolveExecutiveContext } from "../../lib/api/context";
import { getOpportunityWorkspace } from "../../lib/api/opportunities";
export const metadata:Metadata={title:"Decision Committee"};
export default async function DecisionCommitteePage({searchParams}:{searchParams:Promise<{item?:string}>}){const context=await resolveExecutiveContext();if(!context.ok)return <DashboardConfigurationState message={context.error.message}/>;const workspace=await getOpportunityWorkspace(context.data.organization_id);const {item}=await searchParams;return <DecisionCommitteeWorkspace approvals={workspace.approvals} decisions={workspace.decisions} opportunities={workspace.opportunities} focusItem={item}/>}
