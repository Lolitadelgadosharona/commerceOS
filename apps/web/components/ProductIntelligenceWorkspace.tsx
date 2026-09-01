import Link from "next/link";
import type { ApiResult } from "../lib/api/types";
import type {
  Product,
  ProductEconomicInput,
  ProductEconomics,
  ProductHypothesis,
  ProductInvestmentScore,
  ProductPromotion,
  ProductRisk,
  ProductTruth,
  ProductTruthDraft,
  PromotionBrand,
  PromotionReadiness,
  SupplierCandidate,
  TruthComparison,
} from "../lib/api/commerce-intelligence";
import type { ApprovalRequest } from "../lib/api/opportunities";
import { ProductLifecyclePanel } from "./ProductLifecyclePanel";

const pct = (value: number) => `${Math.round(value * 100)}%`;
const label = (value: string) => value.replaceAll("_", " ");
function Failed({ message }: { message: string }) {
  return (
    <div className="dashboard-state compact state-error">
      <strong>Section unavailable</strong>
      <span>{message}</span>
    </div>
  );
}
const state = (kind: string) =>
  kind === "actual"
    ? "ACTUAL"
    : kind === "estimated"
      ? "ASSUMPTION"
      : "UNKNOWN";

export function ProductIntelligenceWorkspace({
  hypotheses,
  economics,
  suppliers,
  risks,
  scores,
  products,
  truth,
  promotions,
}: {
  hypotheses: ApiResult<ProductHypothesis[]>;
  economics: ApiResult<ProductEconomics[]>;
  suppliers: ApiResult<SupplierCandidate[]>;
  risks: ApiResult<ProductRisk[]>;
  scores: ApiResult<ProductInvestmentScore[]>;
  products: ApiResult<Product[]>;
  truth: ApiResult<ProductTruth[]>;
  promotions: ApiResult<ProductPromotion[]>;
}) {
  const rows = hypotheses.ok ? hypotheses.data : [];
  return (
    <div className="commerce-workspace">
      <section className="page-heading">
        <div>
          <p className="eyebrow">
            Hypothesis → economics → risk → governed product
          </p>
          <h1>Product Intelligence</h1>
          <p className="page-description">
            Evaluate product hypotheses without confusing assumptions with
            financial truth or approved Product Truth.
          </p>
        </div>
        <div className="live-contract">
          <span>Source of truth</span>
          <strong>Intelligence + Build APIs</strong>
        </div>
      </section>
      <section className="intelligence-metrics" aria-label="Product overview">
        <article>
          <span>Hypotheses</span>
          <strong>{rows.length}</strong>
          <small>advisory product directions</small>
        </article>
        <article>
          <span>Economics records</span>
          <strong>{economics.ok ? economics.data.length : "—"}</strong>
          <small>estimated inputs</small>
        </article>
        <article>
          <span>Open risks</span>
          <strong>
            {risks.ok
              ? risks.data.filter((item) => item.status === "open").length
              : "—"}
          </strong>
          <small>requires review</small>
        </article>
        <article>
          <span>Approved products</span>
          <strong>
            {products.ok
              ? products.data.filter((item) => item.status === "active").length
              : "—"}
          </strong>
          <small>
            {truth.ok
              ? `${truth.data.length} truth versions`
              : "truth unavailable"}
          </small>
        </article>
      </section>
      {!hypotheses.ok ? (
        <Failed message={hypotheses.error.message} />
      ) : !rows.length ? (
        <div className="dashboard-state">
          <strong>No product hypotheses yet</strong>
          <span>
            Opportunity evaluation has not produced persisted product hypotheses
            for this organization.
          </span>
        </div>
      ) : (
        <section className="product-catalog">
          {rows.map((item) => {
            const economic = economics.ok
              ? economics.data.find((x) => x.product_id === item.id)
              : undefined;
            const score = scores.ok
              ? scores.data.find((x) => x.product_id === item.id)
              : undefined;
            const riskCount = risks.ok
              ? risks.data.filter(
                  (x) => x.product_id === item.id && x.status === "open",
                ).length
              : 0;
            const promotion = promotions.ok
              ? promotions.data.find(
                  (candidate) => candidate.product_hypothesis_id === item.id,
                )
              : undefined;
            const hasTruth =
              promotion?.product_id && truth.ok
                ? truth.data.some(
                    (candidate) =>
                      candidate.product_id === promotion.product_id,
                  )
                : false;
            return (
              <Link href={`/products/${item.id}`} key={item.id}>
                <div className="product-catalog-main">
                  <span>{item.target_market}</span>
                  <h2>{item.name}</h2>
                  <p>{item.solution_description}</p>
                  <small>Opportunity {item.opportunity_id}</small>
                </div>
                <div className="product-catalog-facts">
                  <div>
                    <span>Confidence</span>
                    <strong>{pct(item.confidence_score)}</strong>
                  </div>
                  <div>
                    <span>Investment score</span>
                    <strong>
                      {score ? Math.round(score.overall_score) : "—"}
                    </strong>
                  </div>
                  <div>
                    <span>Margin</span>
                    <strong>
                      {economic ? `${economic.margin_percentage}%` : "—"}
                    </strong>
                  </div>
                  <div>
                    <span>Risks</span>
                    <strong>{riskCount}</strong>
                  </div>
                </div>
                <aside>
                  <b>
                    {hasTruth
                      ? "TRUTH APPROVED"
                      : promotion?.product_id
                        ? "PRODUCT CREATED"
                        : promotion
                          ? "PROMOTION REVIEW"
                          : "HYPOTHESIS"}
                  </b>
                  <span>Evaluate →</span>
                </aside>
              </Link>
            );
          })}
        </section>
      )}
      {products.ok && products.data.length > 0 && (
        <section className="commerce-panel">
          <header>
            <div>
              <p className="eyebrow">Build domain</p>
              <h2>Approved sellable product records</h2>
            </div>
          </header>
          <div className="evidence-compact">
            {products.data.map((item) => (
              <article key={item.id}>
                <span>{item.status}</span>
                <p>
                  <strong>{item.name}</strong>
                  <br />
                  {item.description}
                </p>
                <b>
                  {truth.ok && truth.data.some((x) => x.product_id === item.id)
                    ? "Product Truth recorded"
                    : "Truth not recorded"}
                </b>
              </article>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

export function ProductHypothesisDetail({
  hypothesis,
  economics,
  provenance,
  suppliers,
  risks,
  scores,
  readiness,
  promotion,
  brands,
  approvals,
  drafts,
  comparison,
}: {
  hypothesis: ProductHypothesis;
  economics: ApiResult<ProductEconomics[]>;
  provenance: ApiResult<ProductEconomicInput[]>;
  suppliers: ApiResult<SupplierCandidate[]>;
  risks: ApiResult<ProductRisk[]>;
  scores: ApiResult<ProductInvestmentScore[]>;
  readiness: PromotionReadiness;
  promotion: ProductPromotion | null;
  brands: PromotionBrand[];
  approvals: ApprovalRequest[];
  drafts: ProductTruthDraft[];
  comparison: TruthComparison | null;
}) {
  const economic = economics.ok
    ? economics.data.find((item) => item.product_id === hypothesis.id)
    : undefined;
  const supplierRows = suppliers.ok
    ? suppliers.data.filter((item) => item.product_id === hypothesis.id)
    : [];
  const riskRows = risks.ok
    ? risks.data.filter((item) => item.product_id === hypothesis.id)
    : [];
  const score = scores.ok
    ? scores.data.find((item) => item.product_id === hypothesis.id)
    : undefined;
  const metricRows = provenance.ok ? provenance.data : [];
  return (
    <div className="commerce-workspace">
      <Link className="back-link" href="/products">
        ← Product Intelligence
      </Link>
      <section className="commerce-hero">
        <div>
          <p className="eyebrow">
            Product hypothesis · {hypothesis.target_market}
          </p>
          <h1>{hypothesis.name}</h1>
          <p>{hypothesis.description}</p>
          <div className="opportunity-tags">
            <span>{hypothesis.status}</span>
            <span>{hypothesis.target_customer}</span>
            <Link
              href={`/opportunities/${hypothesis.opportunity_id}?kind=market`}
            >
              Source opportunity →
            </Link>
          </div>
        </div>
        <aside>
          <span>Hypothesis confidence</span>
          <strong>{pct(hypothesis.confidence_score)}</strong>
          <small>Advisory value</small>
        </aside>
      </section>
      <section className="investment-thesis">
        <div>
          <p className="section-number">01</p>
          <h2>Problem → solution thesis</h2>
        </div>
        <div className="thesis-grid">
          <article>
            <span>Customer problem</span>
            <p>{hypothesis.customer_problem}</p>
          </article>
          <article>
            <span>Proposed solution</span>
            <p>{hypothesis.solution_description}</p>
          </article>
        </div>
      </section>
      <div className="commerce-grid">
        <section className="commerce-panel">
          <header>
            <div>
              <p className="eyebrow">Economics provenance</p>
              <h2>Inputs, sources, and confidence</h2>
            </div>
            <span className="data-classification">
              {metricRows.length ? "TRACEABLE" : "UNKNOWN"}
            </span>
          </header>
          {!provenance.ok ? (
            <Failed message={provenance.error.message} />
          ) : !metricRows.length ? (
            <div className="dashboard-state compact">
              <strong>Economic provenance unavailable</strong>
              <span>
                {economic
                  ? "A legacy calculation exists, but its field-level sources are not recorded."
                  : "No economics have been recorded."}
              </span>
            </div>
          ) : (
            <div className="economic-ledger">
              {metricRows.map((item) => (
                <article key={item.metric}>
                  <span>{label(item.metric)}</span>
                  <strong>
                    {item.value === null
                      ? "UNKNOWN"
                      : `${item.value} ${economic?.currency ?? ""}`}
                  </strong>
                  <small>
                    {item.classification.toUpperCase()} · {item.source} ·{" "}
                    {item.confidence === null
                      ? "confidence unknown"
                      : pct(item.confidence)}
                  </small>
                  {item.evidence_reference && (
                    <small>{item.evidence_reference}</small>
                  )}
                </article>
              ))}
            </div>
          )}
        </section>
        <section className="commerce-panel">
          <header>
            <div>
              <p className="eyebrow">Investment assessment</p>
              <h2>Deterministic score</h2>
            </div>
          </header>
          {!scores.ok ? (
            <Failed message={scores.error.message} />
          ) : score ? (
            <div className="score-grid">
              {[
                ["Opportunity", score.opportunity_score],
                ["Margin", score.margin_score],
                ["Risk", score.risk_score],
                ["Competition", score.competition_score],
                ["Confidence", score.confidence_score],
                ["Overall", score.overall_score],
              ].map(([name, value]) => (
                <div key={name}>
                  <span>{name}</span>
                  <strong>{Math.round(Number(value))}</strong>
                </div>
              ))}
            </div>
          ) : (
            <div className="dashboard-state compact">
              <strong>No investment score recorded</strong>
            </div>
          )}
        </section>
      </div>
      <div className="commerce-grid">
        <section className="commerce-panel">
          <header>
            <div>
              <p className="eyebrow">Commercial risk</p>
              <h2>What can invalidate this hypothesis?</h2>
            </div>
          </header>
          {!risks.ok ? (
            <Failed message={risks.error.message} />
          ) : !riskRows.length ? (
            <div className="dashboard-state compact">
              <strong>No ProductRisk records</strong>
              <span>
                This means risk evidence is missing, not that risk is zero.
              </span>
            </div>
          ) : (
            <div className="risk-list">
              {riskRows.map((item) => (
                <article key={item.id}>
                  <span className={`priority-mark priority-${item.severity}`}>
                    {item.severity}
                  </span>
                  <div>
                    <strong>{label(item.risk_type)}</strong>
                    <p>{item.description}</p>
                    <small>{item.status}</small>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
        <section className="commerce-panel">
          <header>
            <div>
              <p className="eyebrow">Supply assumptions</p>
              <h2>Supplier candidates</h2>
            </div>
          </header>
          {!suppliers.ok ? (
            <Failed message={suppliers.error.message} />
          ) : !supplierRows.length ? (
            <div className="dashboard-state compact">
              <strong>No supplier candidates recorded</strong>
            </div>
          ) : (
            <div className="demand-list">
              {supplierRows.map((item) => (
                <article key={item.id}>
                  <div>
                    <span>{label(item.source_type)}</span>
                    <b>{item.risk_level} risk</b>
                  </div>
                  <h3>{item.supplier_reference}</h3>
                  <p>{item.quality_notes}</p>
                  <small>
                    {item.estimated_cost} · MOQ {item.minimum_order_quantity} ·{" "}
                    {item.lead_time}
                  </small>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>
      <ProductLifecyclePanel
        hypothesisId={hypothesis.id}
        readiness={readiness}
        promotion={promotion}
        brands={brands}
        approvals={approvals}
        drafts={drafts}
        comparison={comparison}
      />
      <section className="boundary-panel">
        <p className="eyebrow">Product Truth comparison</p>
        <h2>
          {comparison?.truth
            ? `Approved Product Truth v${comparison.truth.version}`
            : "No approved Product Truth yet."}
        </h2>
        <p>
          {promotion?.product_id
            ? "The canonical Product relationship is recorded through the governed promotion. Product Truth remains separately versioned and approved."
            : "No canonical relationship exists between this ProductHypothesis and a Build-owned Product. The system will not infer one from similar names."}
        </p>
      </section>
    </div>
  );
}
