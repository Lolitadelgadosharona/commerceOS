import { DashboardConfigurationState } from "../../components/DashboardConfigurationState";
import { ListingWorkspace } from "../../components/ListingWorkspace";
import { resolveExecutiveContext } from "../../lib/api/context";
import { getListings } from "../../lib/api/listings";

export default async function ListingsPage() {
  const context = await resolveExecutiveContext();
  if (!context.ok) return <DashboardConfigurationState message={context.error.message} />;
  return <ListingWorkspace result={await getListings(context.data.organization_id)} />;
}
