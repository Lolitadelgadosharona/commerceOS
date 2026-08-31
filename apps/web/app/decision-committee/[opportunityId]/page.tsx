import { notFound } from "next/navigation";
import { CommitteePacket } from "../../../components/CommitteePacket";
import { DashboardConfigurationState } from "../../../components/DashboardConfigurationState";
import { resolveExecutiveContext } from "../../../lib/api/context";
import { getCommitteePacket } from "../../../lib/api/opportunities";

const UUID =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
export default async function CommitteePacketPage({
  params,
}: {
  params: Promise<{ opportunityId: string }>;
}) {
  const { opportunityId } = await params;
  if (!UUID.test(opportunityId)) notFound();
  const context = await resolveExecutiveContext();
  if (!context.ok)
    return <DashboardConfigurationState message={context.error.message} />;
  const packet = await getCommitteePacket(
    opportunityId,
    context.data.organization_id,
  );
  if (!packet.ok) {
    if (packet.error.status === 404) notFound();
    return <DashboardConfigurationState message={packet.error.message} />;
  }
  return (
    <CommitteePacket packet={packet.data} currentUserId={context.data.user_id} />
  );
}
