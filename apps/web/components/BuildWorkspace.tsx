import Link from "next/link";

import type { BuildPackage, CandidatePromotion } from "../lib/api/build-readiness";
import type { ProductEconomicInput, SupplierCandidate } from "../lib/api/commerce-intelligence";
import type { ApiResult } from "../lib/api/types";
import type { SupplierQuote } from "../lib/api/suppliers";
import { CandidatePromotionAction, RelationshipExecutionAction } from "./BuildGovernanceActions";

const label = (value: string) => value.replaceAll("_", " ");
const value = (input: unknown) => (input === null || input === undefined ? "UNKNOWN" : typeof input === "string" ? input : JSON.stringify(input));

export function BuildWorkspace({ result }: { result: ApiResult<BuildPackage[]> }) {
  if (!result.ok)
    return <div className="dashboard-state state-error"><strong>Build workspace unavailable</strong><span>{result.error.message}</span></div>;
  return (
    <div className="commerce-workspace build-workspace">
      <section className="page-heading">
        <div><p className="eyebrow">Supply Ready → validation → governed package</p><h1>Product Build Control Center</h1><p className="page-description">Determine whether canonical Product and supplier truth is complete enough for commercialization preparation. This workspace never purchases, manufactures, or publishes.</p></div>
        <div className="live-contract"><span>Authority boundary</span><strong>Readiness, not execution</strong></div>
      </section>
      <section className="intelligence-metrics" aria-label="Build readiness overview">
        <article><span>Products</span><strong>{result.data.length}</strong><small>canonical Build records</small></article>
        <article><span>Ready</span><strong>{result.data.filter((item) => item.status === "ready").length}</strong><small>no blockers or warnings</small></article>
        <article><span>Conditional</span><strong>{result.data.filter((item) => item.status === "conditional").length}</strong><small>warnings require review</small></article>
        <article><span>Blocked</span><strong>{result.data.filter((item) => item.status === "not_ready").length}</strong><small>persisted blockers</small></article>
      </section>
      {!result.data.length ? <div className="dashboard-state"><strong>No governed Products</strong><span>Build Packages appear only for canonical Product records.</span></div> : <section className="product-catalog">{result.data.map((item) => <Link href={`/build/${item.product_id}`} key={item.product_id}><div className="product-catalog-main"><span>Product Truth v{item.product_truth_version ?? "UNKNOWN"}</span><h2>{item.product_name}</h2><p>{item.next_action}</p><small>{item.approved_suppliers.length} approved supplier(s)</small></div><div className="product-catalog-facts"><div><span>Build status</span><strong>{label(item.status)}</strong></div><div><span>Blockers</span><strong>{item.blockers.length}</strong></div><div><span>Warnings</span><strong>{item.warnings.length}</strong></div><div><span>Samples</span><strong>{item.samples.length}</strong></div></div><aside><b>{item.status.toUpperCase()}</b><span>Open package →</span></aside></Link>)}</section>}
    </div>
  );
}

export function BuildDetail({
  build,
  quotes,
  economics,
  candidates,
  promotions,
}: {
  build: BuildPackage;
  quotes: SupplierQuote[];
  economics: ProductEconomicInput[];
  candidates: SupplierCandidate[];
  promotions: Array<CandidatePromotion | null>;
}) {
  const quoteById = new Map(quotes.map((item) => [item.id, item]));
  return (
    <div className="commerce-workspace build-workspace">
      <Link className="back-link" href="/build">← Product Build Control Center</Link>
      <section className="commerce-hero"><div><p className="eyebrow">Product {build.product_id}</p><h1>{build.product_name}</h1><p>Build Package composed from canonical Product Truth, governed suppliers, validation evidence, and quote provenance.</p><div className="opportunity-tags"><span>{build.status}</span><span>{build.blockers.length} blockers</span><span>{build.warnings.length} warnings</span></div></div><aside><span>Next governed action</span><strong>→</strong><small>{build.next_action}</small></aside></section>
      <section className="commerce-grid commerce-grid-wide">
        <section className="commerce-panel"><header><div><p className="eyebrow">Canonical truth</p><h2>Product Truth & Build Specifications</h2></div><span>v{build.product_truth_version ?? "UNKNOWN"}</span></header><div className="evidence-compact">{Object.entries(build.specifications).map(([key, item]) => <article key={key}><span>required fact</span><p><strong>{label(key)}</strong><br />{value(item)}</p><b>Product Truth</b></article>)}</div>{!Object.keys(build.specifications).length && <p className="panel-footnote">No structured Product Truth specifications exist.</p>}</section>
        <section className="commerce-panel"><header><div><p className="eyebrow">Truth versus supplier facts</p><h2>Supplier Fit</h2></div><span>{build.supplier_fit.length}</span></header><div className="readiness-list">{build.supplier_fit.map((item) => <article key={item.requirement} className={`readiness-${item.status === "pass" ? "info" : item.status === "conditional" ? "warning" : "blocker"}`}><span>{item.requirement}</span><strong>{item.status}</strong><p>Required: {value(item.required_value)} · Supplier: {value(item.supplier_response)}</p>{item.gap && <small>{item.gap}</small>}</article>)}</div></section>
      </section>
      <section className="commerce-grid commerce-grid-wide">
        <section className="commerce-panel"><header><div><p className="eyebrow">Human-governed selection</p><h2>Approved Suppliers</h2></div><span>{build.approved_suppliers.length}</span></header>{build.supplier_relationships.map((item) => <article className="build-relationship" key={item.id}><div><strong>Supplier {item.supplier_id}</strong><p>{item.role} · {item.status}</p></div>{item.status !== "approved" && <RelationshipExecutionAction productId={build.product_id} supplierId={item.supplier_id} approvalId={item.approval_request_id} role={item.role} />}</article>)}{!build.supplier_relationships.length && <p className="panel-footnote">No Product-specific supplier selection exists.</p>}</section>
        <section className="commerce-panel"><header><div><p className="eyebrow">Intelligence → canonical identity</p><h2>Supplier Candidates</h2></div><span>{candidates.length}</span></header>{candidates.map((item, index) => <article className="build-candidate" key={item.id}><div><strong>{item.supplier_reference}</strong><p>{item.quality_notes}</p><small>{item.source_type} · MOQ {item.minimum_order_quantity} · {item.lead_time}</small></div>{promotions[index] ? <Link href={`/suppliers/${promotions[index]?.supplier_profile_id}`}>Canonical Supplier Profile →</Link> : <CandidatePromotionAction productId={build.product_id} candidateId={item.id} />}</article>)}</section>
      </section>
      <section className="commerce-grid commerce-grid-wide">
        <section className="commerce-panel"><header><div><p className="eyebrow">Physical evidence only</p><h2>Samples & Reviews</h2></div><span>{build.samples.length}</span></header>{build.samples.length ? <div className="evidence-compact">{build.samples.map((item) => <article key={item.id}><span>{item.status}</span><p><strong>{item.sample_identifier}</strong><br />Review: {item.review_status}</p><b>{item.evidence_reference ?? "Evidence UNKNOWN"}</b></article>)}</div> : <p className="panel-footnote">No sample has been recorded. This is UNKNOWN, not PASS.</p>}</section>
        <section className="commerce-panel"><header><div><p className="eyebrow">Document / sample / inspection provenance</p><h2>Supplier Validation</h2></div><span>{build.validations.length}</span></header>{build.validations.length ? <div className="risk-list">{build.validations.map((item) => <article key={item.id}><span className={`priority-mark priority-${item.result === "fail" ? "critical" : "low"}`}>{item.result}</span><div><strong>{label(item.validation_type)}</strong><p>{item.observations}</p><small>{label(item.classification)} · {item.evidence_reference ?? "evidence UNKNOWN"}</small></div></article>)}</div> : <p className="panel-footnote">No documented validation artifact exists.</p>}</section>
      </section>
      <section className="commerce-grid commerce-grid-wide">
        <section className="commerce-panel"><header><div><p className="eyebrow">Quoted, never actual</p><h2>Economics Provenance</h2></div><span>{economics.length}</span></header><div className="economic-ledger">{economics.map((item) => { const quote = item.supplier_quote_id ? quoteById.get(item.supplier_quote_id) : undefined; const expired = quote?.valid_until ? new Date(`${quote.valid_until}T00:00:00Z`) < new Date() : false; return <article key={item.id}><span>{item.classification}</span><strong>{label(item.metric)} = {item.value ?? "UNKNOWN"}</strong><small>Supplier {quote?.supplier_id ?? "UNKNOWN"}</small><small>Quote {item.supplier_quote_id ?? "UNLINKED"} · {quote?.quote_date ?? "date unknown"}</small>{expired && <b>EXPIRED QUOTE</b>}<small>{item.evidence_reference ?? "Evidence UNKNOWN"}</small></article>; })}</div></section>
        <section className="commerce-panel"><header><div><p className="eyebrow">Canonical decision</p><h2>Build Readiness</h2></div><span>{build.status}</span></header><div className="readiness-list">{build.blockers.map((item) => <article className="readiness-blocker" key={item.code}><span>BLOCKER · {label(item.code)}</span><strong>NOT READY</strong><p>{item.message}</p></article>)}{build.warnings.map((item) => <article className="readiness-warning" key={item.code}><span>WARNING · {label(item.code)}</span><strong>REVIEW</strong><p>{item.message}</p></article>)}</div><p className="panel-footnote"><strong>Next:</strong> {build.next_action}</p></section>
      </section>
      <section className="boundary-panel"><p className="eyebrow">Why this Product exists</p><h2>Backward traceability preserved</h2><p>Build → Product → Hypothesis {build.origin_hypothesis_id ?? "UNKNOWN"} → Opportunity {build.origin_opportunity_id ?? "UNKNOWN"} → Market Evidence.</p>{build.origin_opportunity_id && <Link href={`/opportunities/${build.origin_opportunity_id}`}>Open originating Opportunity →</Link>}</section>
      <section className="boundary-panel"><p className="eyebrow">Next commercialization boundary</p><h2>Proceed to Listing Intelligence</h2><p>{build.blockers.length ? "A Listing draft may be prepared, but approval remains blocked until Build blockers are resolved." : "Build has no blockers. Review claim support and Listing readiness before human approval."}</p><Link href={`/listings/${build.product_id}`}>Open Listing workspace →</Link></section>
    </div>
  );
}
