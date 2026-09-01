import "server-only";
import { apiGet } from "./client";
import type { ApiResult, ReadModel } from "./types";

export type Supplier = ReadModel & { organization_id:string; name:string; source_type:string; country:string; capabilities:string[]; certifications:string[]; status:string };
export type SupplierMatch = ReadModel & { organization_id:string; product_id:string; supplier_id:string; match_score:number; recommended:boolean; reason:string };
export type SupplierEvidence = ReadModel & { organization_id:string; supplier_id:string; field_name:string; value:unknown; classification:string; source:string; confidence:number|null; as_of:string|null; evidence_reference:string|null; notes:string|null };
export type SupplierQuote = ReadModel & { organization_id:string; supplier_id:string; product_id:string; currency:string; unit_price:string|null; minimum_order_quantity:number|null; price_tiers:Array<Record<string,unknown>>; sample_cost:string|null; tooling_cost:string|null; packaging_cost:string|null; incoterm:string|null; payment_terms:string|null; lead_time:string|null; quote_date:string; valid_until:string|null; classification:string; source:string; confidence:number|null; evidence_reference:string|null; notes:string|null };
export type SupplierRisk = ReadModel & { organization_id:string; supplier_id:string; risk_type:string; severity:string; description:string; status:string };
export type Qualification = { organization_id:string; supplier_id:string; product_id:string; dimensions:Array<{dimension:string;status:"pass"|"conditional"|"fail"|"unknown";evidence:string[];confidence:number|null;gaps:string[];risk:string|null}>; readiness:Array<{code:string;severity:string;status:string;message:string;references:string[]}>;ready:boolean;next_action:string };
export type ApprovedRelationship = ReadModel & { organization_id:string;product_id:string;supplier_id:string;source_candidate_id:string|null;approval_request_id:string;role:string;status:string;approved_by:string|null;approved_at:string|null };
export type SupplierDetail = { supplier:Supplier; products:SupplierMatch[]; evidence:SupplierEvidence[]; quotes:SupplierQuote[]; evaluations:Array<ReadModel & {overall_score:number;quality_score:number;price_score:number;lead_time_score:number;communication_score:number;compliance_score:number;confidence_score:number}>; risks:SupplierRisk[]; approved_relationships:ApprovedRelationship[]; qualifications:Qualification[]; next_action:string };
export type SupplierComparison = { organization_id:string; product_id:string; rows:Array<{supplier:Supplier;match:SupplierMatch|null;evaluation:null|Record<string,unknown>;quote:SupplierQuote|null;risks:SupplierRisk[];qualification:Qualification}> };
export type SupplyReadiness = { organization_id:string;product_id:string;ready:boolean;approved_suppliers:ApprovedRelationship[];items:Array<{code:string;severity:"blocker"|"warning"|"info";status:string;message:string;references:string[]}>;next_action:string };

function list<T>(result: ApiResult<T[]>): ApiResult<T[]> { return result.ok && !Array.isArray(result.data) ? {ok:false,error:{kind:"contract",message:"Supplier API returned an invalid list."}} : result; }

export async function getSupplierWorkspace(organizationId:string){
  const query={organization_id:organizationId};
  const [suppliers,matches,quotes,evidence,relationships]=await Promise.all([
    apiGet<Supplier[]>("/api/v1/suppliers",query),
    apiGet<SupplierMatch[]>("/api/v1/product-supplier-matches",query),
    apiGet<SupplierQuote[]>("/api/v1/supplier-quotes",query),
    apiGet<SupplierEvidence[]>("/api/v1/supplier-evidence",query),
    apiGet<ApprovedRelationship[]>("/api/v1/approved-product-suppliers",query),
  ]);
  return {suppliers:list(suppliers),matches:list(matches),quotes:list(quotes),evidence:list(evidence),relationships:list(relationships)};
}

export function getSupplierDetail(id:string,organizationId:string){return apiGet<SupplierDetail>(`/api/v1/suppliers/${id}/intelligence`,{organization_id:organizationId});}
