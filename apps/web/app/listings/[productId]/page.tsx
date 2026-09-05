import { notFound } from "next/navigation";

import { DashboardConfigurationState } from "../../../components/DashboardConfigurationState";
import { ListingDetail } from "../../../components/ListingWorkspace";
import { resolveExecutiveContext } from "../../../lib/api/context";
import { getListing } from "../../../lib/api/listings";

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export default async function ListingDetailPage({
  params,
}: {
  params: Promise<{ productId: string }>;
}) {
  const { productId } = await params;
  if (!UUID.test(productId)) notFound();
  const context = await resolveExecutiveContext();
  if (!context.ok) return <DashboardConfigurationState message={context.error.message} />;
  const result = await getListing(productId, context.data.organization_id);
  if (!result.listing.ok)
    return <DashboardConfigurationState message={result.listing.error.message} />;
  return (
    <ListingDetail
      item={result.listing.data}
      shopify={result.shopify.ok ? result.shopify.data : null}
    />
  );
}
