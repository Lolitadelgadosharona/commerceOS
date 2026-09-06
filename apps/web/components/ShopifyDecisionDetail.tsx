"use client";

import Link from "next/link";
import { useActionState } from "react";

import { decideShopifyPublication, type ShopifyActionState } from "../app/channels/shopify/actions";
import type { ShopifyDecisionDetail as Detail } from "../lib/api/shopify";

const initial: ShopifyActionState = { kind: "idle", message: "" };
const label = (value: string) => value.replaceAll("_", " ");

export function ShopifyDecisionDetail({ detail }: { detail: Detail }) {
  const [state, action, pending] = useActionState(decideShopifyPublication, initial);
  const publication = detail.publication;
  return <div className="commerce-workspace shopify-workspace">
    <Link className="back-link" href="/decision-committee">← Decision Committee</Link>
    <section className="page-heading"><div><p className="eyebrow">Governance-owned publication decision</p><h1>{detail.product_name}</h1><p className="page-description">Review the immutable projection and risks. Approval authorizes a later explicit execution; it does not write to Shopify.</p></div><div className="live-contract"><span>Approval state</span><strong>{label(detail.approval_status ?? "not requested")}</strong></div></section>
    <section className="commerce-grid commerce-grid-wide">
      <section className="commerce-panel"><header><div><p className="eyebrow">Pinned source</p><h2>Publication contract</h2></div></header><Fact name="Store" value={detail.store_domain}/><Fact name="Merchant" value={detail.merchant_name ?? "Not validated"}/><Fact name="Development store" value={detail.partner_development === null ? "Unknown" : detail.partner_development ? "Yes" : "No"}/><Fact name="Product Truth" value={`v${publication.product_truth_version}`}/><Fact name="Approved Listing" value={`v${publication.listing_version}`}/><Fact name="Operation" value={publication.operation}/></section>
      <section className="commerce-panel"><header><div><p className="eyebrow">Safe draft mapping</p><h2>Projection summary</h2></div></header>{Object.entries(detail.projection_summary).map(([key,value])=><Fact key={key} name={label(key)} value={Array.isArray(value) ? value.length ? JSON.stringify(value) : "NONE" : String(value ?? "NONE")}/>)}</section>
    </section>
    <section className="commerce-grid commerce-grid-wide"><section className="commerce-panel"><header><div><p className="eyebrow">Review evidence</p><h2>Warnings</h2></div></header>{detail.warnings.length ? detail.warnings.map(item=><article className="readiness-warning" key={item.code}><strong>{label(item.code)}</strong><p>{item.message}</p></article>) : <p>No non-blocking warnings.</p>}</section><section className="commerce-panel"><header><div><p className="eyebrow">Do not authorize blindly</p><h2>Risks and blockers</h2></div></header>{detail.risks.length ? detail.risks.map(item=><p className="inline-alert" key={item}>{item}</p>) : <p>No current readiness blockers.</p>}</section></section>
    {detail.approval_status === "pending" && publication.approval_request_id ? <section className="investment-action-panel"><p className="eyebrow">Human authority required</p><h2>Record publication decision</h2><p>{detail.approval_reason}</p><form action={action}><input type="hidden" name="publication_id" value={publication.id}/><input type="hidden" name="approval_request_id" value={publication.approval_request_id}/><label>Decision reason<textarea name="reason" required minLength={3} placeholder="Record the evidence and risks considered."/></label><div className="decision-buttons"><button className="primary-button" name="decision" value="approved" disabled={pending}>Approve safe draft publication</button><button className="danger-button" name="decision" value="rejected" disabled={pending}>Reject</button></div></form>{state.message ? <p className={state.kind === "error" ? "inline-alert" : "panel-footnote"}>{state.message}</p> : null}</section> : <section className="boundary-panel"><p className="eyebrow">Decision recorded</p><h2>{label(detail.approval_status ?? "not requested")}</h2><p>{detail.approval_reason ?? "The Governance approval record remains authoritative."}</p></section>}
    <section className="boundary-panel"><p className="eyebrow">Authority boundary</p><strong>APPROVAL ≠ AUTHORIZATION FINALIZATION ≠ EXTERNAL EXECUTION</strong><p>Every later step is explicit, tenant-scoped, audited, and idempotent.</p></section>
  </div>;
}

function Fact({ name, value }: { name: string; value: string }) { return <div className="listing-content-row"><span>{name}</span><p>{value}</p></div>; }
