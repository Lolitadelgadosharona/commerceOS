import { notFound } from "next/navigation";

import { DashboardConfigurationState } from "../../../../../components/DashboardConfigurationState";
import { ShopifyDecisionDetail } from "../../../../../components/ShopifyDecisionDetail";
import { resolveExecutiveContext } from "../../../../../lib/api/context";
import { getShopifyDecisionDetail } from "../../../../../lib/api/shopify";

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export default async function ShopifyPublicationDecisionPage({
  params,
}: {
  params: Promise<{ publicationId: string }>;
}) {
  const { publicationId } = await params;
  if (!UUID.test(publicationId)) notFound();
  const context = await resolveExecutiveContext();
  if (!context.ok) return <DashboardConfigurationState message={context.error.message} />;
  const result = await getShopifyDecisionDetail(
    publicationId,
    context.data.organization_id,
  );
  if (!result.ok) return <DashboardConfigurationState message={result.error.message} />;
  return <ShopifyDecisionDetail detail={result.data} />;
}
