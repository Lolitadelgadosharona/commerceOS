import { notFound } from "next/navigation";
import { DashboardConfigurationState } from "../../../components/DashboardConfigurationState";
import {
  DiscoveryOpportunityDetail,
  MarketOpportunityDetail,
} from "../../../components/OpportunityDetail";
import { resolveExecutiveContext } from "../../../lib/api/context";
import {
  getDiscoveryOpportunityDetail,
  getMarketOpportunityDetail,
} from "../../../lib/api/opportunities";

const UUID =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export default async function OpportunityDetailPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ kind?: string }>;
}) {
  const { id } = await params,
    { kind } = await searchParams;
  if (!UUID.test(id)) notFound();
  const context = await resolveExecutiveContext();
  if (!context.ok)
    return <DashboardConfigurationState message={context.error.message} />;
  const organizationId = context.data.organization_id;
  if (kind === "candidate") {
    const detail = await getDiscoveryOpportunityDetail(id, organizationId);
    if (!detail.opportunity.ok && detail.opportunity.error.status === 404)
      notFound();
    if (!detail.opportunity.ok)
      return (
        <DashboardConfigurationState
          message={detail.opportunity.error.message}
        />
      );
    return (
      <DiscoveryOpportunityDetail
        opportunity={detail.opportunity.data}
        evidence={detail.evidence}
        assessment={detail.assessment}
        decisions={detail.decisions}
      />
    );
  }
  const detail = await getMarketOpportunityDetail(id, organizationId);
  if (!detail.opportunity.ok && detail.opportunity.error.status === 404) {
    if (kind === "market") notFound();
    const candidate = await getDiscoveryOpportunityDetail(id, organizationId);
    if (!candidate.opportunity.ok) notFound();
    return (
      <DiscoveryOpportunityDetail
        opportunity={candidate.opportunity.data}
        evidence={candidate.evidence}
        assessment={candidate.assessment}
        decisions={candidate.decisions}
      />
    );
  }
  if (!detail.opportunity.ok)
    return (
      <DashboardConfigurationState message={detail.opportunity.error.message} />
    );
  return (
    <MarketOpportunityDetail
      opportunity={detail.opportunity.data}
      memo={detail.memo}
      readiness={detail.readiness}
      evidence={detail.evidence}
      scores={detail.scores}
      risks={detail.risks}
      approvals={detail.approvals}
      decisions={detail.decisions}
      productPromotions={detail.productPromotions}
      currentUserId={context.data.user_id}
    />
  );
}
