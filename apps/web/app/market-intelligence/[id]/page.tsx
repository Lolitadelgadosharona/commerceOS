import { notFound } from "next/navigation";
import { DashboardConfigurationState } from "../../../components/DashboardConfigurationState";
import { MarketSignalDetail } from "../../../components/MarketIntelligenceWorkspace";
import { getMarketSignalDetail } from "../../../lib/api/commerce-intelligence";
import { resolveExecutiveContext } from "../../../lib/api/context";
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
export default async function MarketSignalPage({params}:{params:Promise<{id:string}>}){const {id}=await params;if(!UUID.test(id))notFound();const context=await resolveExecutiveContext();if(!context.ok)return <DashboardConfigurationState message={context.error.message}/>;const detail=await getMarketSignalDetail(id,context.data.organization_id);if(!detail.signals.ok)return <DashboardConfigurationState message={detail.signals.error.message}/>;if(!detail.signal)notFound();return <MarketSignalDetail signal={detail.signal} evidence={detail.evidence} sources={detail.sources} opportunities={detail.opportunities}/>}
