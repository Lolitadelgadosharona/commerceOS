import { DashboardConfigurationState } from "../../../components/DashboardConfigurationState";
import { ShopifyControlCenter } from "../../../components/ShopifyWorkspace";
import { resolveExecutiveContext } from "../../../lib/api/context";
import { getShopifyWorkspace } from "../../../lib/api/shopify";

export default async function ShopifyPage(){const context=await resolveExecutiveContext();if(!context.ok)return <DashboardConfigurationState message={context.error.message}/>;return <ShopifyControlCenter result={await getShopifyWorkspace(context.data.organization_id)}/>}
