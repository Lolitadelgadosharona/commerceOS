import { notFound } from "next/navigation";

import { DashboardConfigurationState } from "../../../../components/DashboardConfigurationState";
import { ShopifyProductDetail } from "../../../../components/ShopifyWorkspace";
import { resolveExecutiveContext } from "../../../../lib/api/context";
import { getShopifyReadiness, getShopifyWorkspace } from "../../../../lib/api/shopify";

const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
export default async function ShopifyProductPage({params}:{params:Promise<{productId:string}>}){const {productId}=await params;if(!UUID.test(productId))notFound();const context=await resolveExecutiveContext();if(!context.ok)return <DashboardConfigurationState message={context.error.message}/>;const workspace=await getShopifyWorkspace(context.data.organization_id);if(!workspace.ok)return <DashboardConfigurationState message={workspace.error.message}/>;const connection=workspace.data.connections[0]??null;const result=await getShopifyReadiness(productId,context.data.organization_id,connection?.id);if(!result.ok)return <DashboardConfigurationState message={result.error.message}/>;const publication=workspace.data.publications.find(x=>x.product_id===productId)??null;const execution=publication?workspace.data.executions.find(x=>x.publication_id===publication.id)??null:null;return <ShopifyProductDetail item={result.data} connection={connection} publication={publication} execution={execution}/>}
