import { notFound } from "next/navigation";
import { DashboardConfigurationState } from "../../../components/DashboardConfigurationState";
import { ProductHypothesisDetail } from "../../../components/ProductIntelligenceWorkspace";
import { getProductHypothesisDetail } from "../../../lib/api/commerce-intelligence";
import { resolveExecutiveContext } from "../../../lib/api/context";
const UUID =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
export default async function ProductPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  if (!UUID.test(id)) notFound();
  const context = await resolveExecutiveContext();
  if (!context.ok)
    return <DashboardConfigurationState message={context.error.message} />;
  const detail = await getProductHypothesisDetail(
    id,
    context.data.organization_id,
  );
  if (!detail.hypothesis.ok)
    return (
      <DashboardConfigurationState message={detail.hypothesis.error.message} />
    );
  if (
    !detail.readiness.ok ||
    !detail.promotion.ok ||
    !detail.brands.ok ||
    !detail.approvals.ok
  )
    return (
      <DashboardConfigurationState message="Product lifecycle contracts are unavailable." />
    );
  return (
    <ProductHypothesisDetail
      hypothesis={detail.hypothesis.data}
      economics={detail.economics}
      provenance={detail.provenance}
      suppliers={detail.suppliers}
      risks={detail.risks}
      scores={detail.scores}
      readiness={detail.readiness.data}
      promotion={detail.promotion.data}
      brands={detail.brands.data}
      approvals={detail.approvals.data}
      drafts={detail.drafts?.ok ? detail.drafts.data : []}
      comparison={detail.comparison?.ok ? detail.comparison.data : null}
      supplierComparison={detail.supplierComparison?.ok ? detail.supplierComparison.data : null}
      supplyReadiness={detail.supplyReadiness?.ok ? detail.supplyReadiness.data : null}
      buildPackage={detail.buildPackage?.ok ? detail.buildPackage.data : null}
    />
  );
}
