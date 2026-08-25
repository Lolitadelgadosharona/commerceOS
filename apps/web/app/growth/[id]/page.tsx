import type { Metadata } from "next";
import { GrowthWorkspace } from "../../../components/GrowthWorkspace";
import { resolveExecutiveContext } from "../../../lib/api/context";
import { loadGrowthWorkspace } from "../../../lib/api/growth";

export const metadata:Metadata={title:"Growth workspace"};
export default async function GrowthWorkspacePage({params}:{params:Promise<{id:string}>}){
  const {id}=await params;
  const actor=await resolveExecutiveContext();
  if(!actor.ok)return <section className="configuration-state"><span>G</span><div><h2>Workspace unavailable</h2><p>{actor.error.message}</p></div></section>;
  return <GrowthWorkspace results={await loadGrowthWorkspace(actor.data.organization_id,id)}/>;
}
