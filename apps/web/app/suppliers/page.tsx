import type { Metadata } from "next";
import { DashboardConfigurationState } from "../../components/DashboardConfigurationState";
import { SupplierIntelligenceWorkspace } from "../../components/SupplierIntelligenceWorkspace";
import { resolveExecutiveContext } from "../../lib/api/context";
import { getSupplierWorkspace } from "../../lib/api/suppliers";

export const metadata:Metadata={title:"Supplier Intelligence"};
export default async function SuppliersPage(){const context=await resolveExecutiveContext();if(!context.ok)return <DashboardConfigurationState message={context.error.message}/>;return <SupplierIntelligenceWorkspace {...await getSupplierWorkspace(context.data.organization_id)}/>;}
