import { notFound } from "next/navigation";
import { DashboardConfigurationState } from "../../../components/DashboardConfigurationState";
import { SupplierDetailWorkspace } from "../../../components/SupplierDetailWorkspace";
import { resolveExecutiveContext } from "../../../lib/api/context";
import { getSupplierDetail } from "../../../lib/api/suppliers";

export default async function SupplierPage({params}:{params:Promise<{id:string}>}){const context=await resolveExecutiveContext();if(!context.ok)return <DashboardConfigurationState message={context.error.message}/>;const {id}=await params;const result=await getSupplierDetail(id,context.data.organization_id);if(!result.ok){if(result.error.status===404)notFound();return <DashboardConfigurationState message={result.error.message}/>;}return <SupplierDetailWorkspace detail={result.data}/>;}
