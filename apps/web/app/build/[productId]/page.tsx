import { notFound } from "next/navigation";

import { BuildDetail } from "../../../components/BuildWorkspace";
import { DashboardConfigurationState } from "../../../components/DashboardConfigurationState";
import { getBuildDetail } from "../../../lib/api/build-readiness";
import { resolveExecutiveContext } from "../../../lib/api/context";

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export default async function BuildDetailPage({
  params,
}: {
  params: Promise<{ productId: string }>;
}) {
  const { productId } = await params;
  if (!UUID.test(productId)) notFound();
  const context = await resolveExecutiveContext();
  if (!context.ok) return <DashboardConfigurationState message={context.error.message} />;
  const detail = await getBuildDetail(productId, context.data.organization_id);
  if (!detail.build.ok) return <DashboardConfigurationState message={detail.build.error.message} />;
  return (
    <BuildDetail
      build={detail.build.data}
      quotes={detail.quotes?.ok ? detail.quotes.data : []}
      economics={detail.economics?.ok ? detail.economics.data : []}
      candidates={detail.candidates ?? []}
      promotions={detail.promotions.map((item) => (item.ok ? item.data : null))}
    />
  );
}
