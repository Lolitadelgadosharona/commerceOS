import { BuildWorkspace } from "../../components/BuildWorkspace";
import { DashboardConfigurationState } from "../../components/DashboardConfigurationState";
import { getBuildWorkspace } from "../../lib/api/build-readiness";
import { resolveExecutiveContext } from "../../lib/api/context";

export default async function BuildPage() {
  const context = await resolveExecutiveContext();
  if (!context.ok) return <DashboardConfigurationState message={context.error.message} />;
  return <BuildWorkspace result={await getBuildWorkspace(context.data.organization_id)} />;
}
