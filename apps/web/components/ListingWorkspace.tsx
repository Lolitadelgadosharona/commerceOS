import Link from "next/link";
import type { ReactNode } from "react";

import type { ListingPackage, ShopifyProjection } from "../lib/api/listings";
import type { ApiResult } from "../lib/api/types";
import type { ShopifyReadiness } from "../lib/api/shopify";

const label = (input: string) => input.replaceAll("_", " ");
const value = (input: unknown) =>
  input === null || input === undefined
    ? "UNKNOWN"
    : typeof input === "string"
      ? input
      : JSON.stringify(input);

export function ListingWorkspace({ result }: { result: ApiResult<ListingPackage[]> }) {
  if (!result.ok)
    return (
      <div className="dashboard-state state-error">
        <strong>Listing Intelligence unavailable</strong>
        <span>{result.error.message}</span>
      </div>
    );
  return (
    <div className="commerce-workspace listing-workspace">
      <section className="page-heading">
        <div>
          <p className="eyebrow">Build Ready → governed commercial truth</p>
          <h1>Listing Intelligence Control Center</h1>
          <p className="page-description">
            Review what may be said, why it is supportable, and whether channel-neutral Listing
            Truth is ready. Listing Ready never means published.
          </p>
        </div>
        <div className="live-contract"><span>External execution</span><strong>Not authorized</strong></div>
      </section>
      <section className="intelligence-metrics" aria-label="Listing readiness overview">
        <Metric title="Products" value={result.data.length} note="governed products" />
        <Metric title="Listing Ready" value={result.data.filter((x) => x.status === "ready").length} note="no warnings" />
        <Metric title="Conditional" value={result.data.filter((x) => x.status === "conditional").length} note="warnings remain" />
        <Metric title="Claim blockers" value={result.data.reduce((n, x) => n + x.claim_review.filter((c) => c.blocking).length, 0)} note="evidence or policy required" />
      </section>
      <section className="product-catalog">
        {result.data.map((item) => (
          <Link href={`/listings/${item.product_id}`} key={item.product_id}>
            <div className="product-catalog-main"><span>Product Truth v{item.product_truth_version ?? "UNKNOWN"}</span><h2>{item.product_name}</h2><p>{item.next_action}</p><small>{item.product_truth_fresh ? "Truth current" : "Truth review required"}</small></div>
            <div className="product-catalog-facts"><div><span>Listing</span><strong>{item.listing?.status ?? "missing"}</strong></div><div><span>Readiness</span><strong>{label(item.status)}</strong></div><div><span>Claims</span><strong>{item.claim_review.length}</strong></div><div><span>Build</span><strong>{label(item.build_status)}</strong></div></div>
            <aside><b>{item.status.toUpperCase()}</b><span>Open Listing →</span></aside>
          </Link>
        ))}
      </section>
    </div>
  );
}

export function ListingDetail({ item, shopify, channel }: { item: ListingPackage; shopify: ShopifyProjection | null; channel: ShopifyReadiness | null }) {
  const listing = item.listing;
  return (
    <div className="commerce-workspace listing-workspace">
      <Link className="back-link" href="/listings">← Listing Intelligence</Link>
      <section className="commerce-hero"><div><p className="eyebrow">Channel-neutral Listing Truth</p><h1>{item.product_name}</h1><p>{listing?.summary ?? "No Listing draft exists yet."}</p><div className="opportunity-tags"><span>{item.status}</span><span>Build {item.build_status}</span><span>{item.product_truth_fresh ? "Truth current" : "Product Truth changed"}</span></div></div><aside><span>Next governed action</span><strong>→</strong><small>{item.next_action}</small></aside></section>
      <section className="commerce-grid commerce-grid-wide">
        <Panel title="Source Product Truth" eyebrow="Allowed facts"><div className="readiness-list">{item.allowed_facts.map((fact) => <article className={fact.can_use ? "readiness-info" : "readiness-blocker"} key={fact.fact}><span>{fact.can_use ? "ALLOWED" : "RESTRICTED"}</span><strong>{fact.fact}</strong><p>{fact.source}</p><small>{fact.notes}</small></article>)}</div></Panel>
        <Panel title="Customer Problem & Positioning" eyebrow="Market context, not product proof"><h3>{listing?.customer_problem ?? "Customer language UNKNOWN"}</h3><p>{listing?.solution ?? "Solution framing not drafted."}</p><small>Origin: Opportunity {item.origin_opportunity_id ?? "UNKNOWN"}. Customer evidence may guide wording but never proves a Product claim.</small></Panel>
      </section>
      <section className="commerce-grid commerce-grid-wide">
        <Panel title="Commercial Content" eyebrow="Feature ≠ benefit"><Content name="Title" text={listing?.title}/><Content name="Description" text={listing?.description}/><Content name="Features" text={listing?.features.join(" · ")}/><Content name="Benefits" text={listing?.benefits.join(" · ")}/><Content name="Use cases" text={listing?.use_cases.join(" · ")}/><Content name="What's included" text={listing?.whats_included.join(" · ")}/></Panel>
        <Panel title="Claim Review" eyebrow="Evidence before persuasion"><div className="readiness-list">{item.claim_review.map((claim) => <article className={claim.blocking ? "readiness-blocker" : "readiness-info"} key={claim.id}><span>{label(claim.claim_type)} · {claim.risk_level} risk</span><strong>{claim.claim}</strong><p>{claim.support_status.toUpperCase()} · {claim.human_review_needed ? "human review required" : "standard review"}</p><small>{claim.sources.join(" · ") || "No evidence source"}</small>{claim.policy_requirement && <small>{claim.policy_requirement}</small>}</article>)}</div>{!item.claim_review.length && <p>No proposed claims yet.</p>}</Panel>
      </section>
      <section className="commerce-grid commerce-grid-wide">
        <Panel title="FAQ & Trust" eyebrow="No unsupported answers"><div className="readiness-list">{item.faqs.map((faq) => <article className={faq.answer_status === "supported_answer" ? "readiness-info" : "readiness-warning"} key={faq.id}><span>{label(faq.answer_status)}</span><strong>{faq.question}</strong><p>{faq.answer ?? "Answer UNKNOWN"}</p><small>{faq.evidence_reference ?? "Evidence or policy required"}</small></article>)}</div><Content name="Shipping" text={listing?.shipping_facts}/><Content name="Returns" text={listing?.return_facts}/><Content name="Risk reversal" text={listing?.risk_reversal}/></Panel>
        <Panel title="SEO & GEO Product Data" eyebrow="Factual and extractable"><Content name="SEO title" text={listing?.seo_title}/><Content name="Meta description" text={listing?.meta_description}/><Content name="Primary topic" text={listing?.primary_topic}/><div className="evidence-compact">{Object.entries(listing?.structured_attributes ?? {}).map(([key, entry]) => <article key={key}><span>structured attribute</span><p><strong>{label(key)}</strong><br />{value(entry)}</p><b>Product data</b></article>)}</div><p className="panel-footnote">Internal structured-data readiness: <strong>{item.structured_data_ready ? "READY" : "INCOMPLETE"}</strong>. No Google or channel validity is claimed.</p></Panel>
      </section>
      <section className="commerce-grid commerce-grid-wide">
        <Panel title="Listing Readiness" eyebrow="Backend-owned decision"><div className="readiness-list">{item.blockers.map((issue) => <article className="readiness-blocker" key={issue.code}><span>BLOCKER</span><strong>{label(issue.code)}</strong><p>{issue.message}</p></article>)}{item.warnings.map((issue) => <article className="readiness-warning" key={issue.code}><span>WARNING — non-blocking</span><strong>{label(issue.code)}</strong><p>{issue.message}</p></article>)}</div><p className="panel-footnote"><strong>{item.status.toUpperCase()}</strong> · Approval is human-governed and does not publish.</p></Panel>
        <Panel title="Shopify Readiness Projection" eyebrow="Governed channel adapter · no automatic publishing"><Content name="Projection status" text={channel?.status ?? shopify?.status}/><Content name="Authorization" text={channel?.authorization_status ?? (shopify?.publication_authorized ? "AUTHORIZED" : "NOT REQUESTED")}/><Content name="External Shopify ID" text={channel?.external_product_id ?? shopify?.external_id}/><Content name="Drift" text={channel?.drift_status}/><Content name="Approved price" text={shopify?.price ? `${shopify.price} ${shopify.currency ?? ""}` : "UNKNOWN — assumptions are not copied"}/><p>{channel?.blockers.length ? `Blocked: ${channel.blockers.map((x) => x.message).join(" · ")}` : "Current approved Listing can enter governed Shopify review."}</p><Link className="primary-button" href={`/channels/shopify/${item.product_id}`}>Open governed Shopify workspace →</Link></Panel>
      </section>
      <section className="boundary-panel"><p className="eyebrow">Governance & version history</p><h2>Listing v{listing?.listing_version ?? "—"} · {listing?.status ?? "missing"}</h2><p>Derived from Product Truth v{listing?.product_truth_version ?? "—"}. Approved versions are immutable; changes create a new version and supersede the prior approved representation.</p><strong>LISTING READY ≠ PUBLISH AUTHORIZATION</strong></section>
    </div>
  );
}

function Panel({ title, eyebrow, children }: { title: string; eyebrow: string; children: ReactNode }) {
  return <section className="commerce-panel"><header><div><p className="eyebrow">{eyebrow}</p><h2>{title}</h2></div></header>{children}</section>;
}
function Content({ name, text }: { name: string; text: string | null | undefined }) {
  return <div className="listing-content-row"><span>{name}</span><p>{text || "UNKNOWN / not provided"}</p></div>;
}
function Metric({ title, value: amount, note }: { title: string; value: number; note: string }) {
  return <article><span>{title}</span><strong>{amount}</strong><small>{note}</small></article>;
}
