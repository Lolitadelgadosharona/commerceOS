import { notFound } from "next/navigation";
import { DashboardConfigurationState } from "../../../components/DashboardConfigurationState";
import { ProductHypothesisDetail } from "../../../components/ProductIntelligenceWorkspace";
import { getProductHypothesisDetail } from "../../../lib/api/commerce-intelligence";
import { resolveExecutiveContext } from "../../../lib/api/context";
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
export default async function ProductPage({params}:{params:Promise<{id:string}>}){const {id}=await params;if(!UUID.test(id))notFound();const context=await resolveExecutiveContext();if(!context.ok)return <DashboardConfigurationState message={context.error.message}/>;const detail=await getProductHypothesisDetail(id,context.data.organization_id);if(!detail.hypothesis.ok)return <DashboardConfigurationState message={detail.hypothesis.error.message}/>;return <ProductHypothesisDetail hypothesis={detail.hypothesis.data} economics={detail.economics} provenance={detail.provenance} suppliers={detail.suppliers} risks={detail.risks} scores={detail.scores}/>}
