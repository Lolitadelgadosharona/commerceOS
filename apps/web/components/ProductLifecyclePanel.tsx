"use client";

import { useActionState } from "react";
import {
  createTruthDraft,
  executeProductPromotion,
  publishTruthDraft,
  requestProductPromotion,
  requestTruthReview,
  type ProductActionState,
} from "../app/products/actions";
import type { ApprovalRequest } from "../lib/api/opportunities";
import type {
  ProductPromotion,
  ProductTruthDraft,
  PromotionBrand,
  PromotionReadiness,
  TruthComparison,
} from "../lib/api/commerce-intelligence";

const initial: ProductActionState = { kind: "idle", message: "" };
function Message({ state }: { state: ProductActionState }) {
  return state.message ? (
    <p className={`action-message action-${state.kind}`} role="status">
      {state.message}
    </p>
  ) : null;
}

export function ProductLifecyclePanel({
  hypothesisId,
  readiness,
  promotion,
  brands,
  approvals,
  drafts,
  comparison,
}: {
  hypothesisId: string;
  readiness: PromotionReadiness;
  promotion: ProductPromotion | null;
  brands: PromotionBrand[];
  approvals: ApprovalRequest[];
  drafts: ProductTruthDraft[];
  comparison: TruthComparison | null;
}) {
  const [requestState, requestAction, requestPending] = useActionState(
    requestProductPromotion,
    initial,
  );
  const [executeState, executeAction, executePending] = useActionState(
    executeProductPromotion,
    initial,
  );
  const [draftState, draftAction, draftPending] = useActionState(
    createTruthDraft,
    initial,
  );
  const [reviewState, reviewAction, reviewPending] = useActionState(
    requestTruthReview,
    initial,
  );
  const [publishState, publishAction, publishPending] = useActionState(
    publishTruthDraft,
    initial,
  );
  const approval = promotion
    ? approvals.find((item) => item.id === promotion.approval_request_id)
    : undefined;
  const currentDraft = drafts[0];
  const truthApproval = currentDraft?.approval_request_id
    ? approvals.find((item) => item.id === currentDraft.approval_request_id)
    : undefined;
  const stages = [
    { name: "Product Hypothesis", state: "COMPLETE" },
    {
      name: "Investment Decision",
      state:
        readiness.items.find((x) => x.code === "investment_approval")
          ?.status === "ready"
          ? "APPROVED"
          : "BLOCKED",
    },
    {
      name: "Promotion Readiness",
      state: readiness.ready ? "READY" : "BLOCKED",
    },
    {
      name: "Promotion Approval",
      state: approval?.status?.toUpperCase() ?? "NOT STARTED",
    },
    {
      name: "Product",
      state: promotion?.product_id ? "CREATED" : "NOT STARTED",
    },
    {
      name: "Product Truth",
      state: comparison?.truth
        ? "APPROVED"
        : drafts.length
          ? "DRAFT"
          : "NOT STARTED",
    },
    { name: "Supplier Readiness", state: "NOT STARTED" },
    { name: "Listing Readiness", state: "NOT STARTED" },
    { name: "Commerce Readiness", state: "NOT STARTED" },
  ];
  return (
    <>
      <section className="commerce-panel">
        <header>
          <div>
            <p className="eyebrow">Governed product lifecycle</p>
            <h2>Hypothesis → Product → Product Truth</h2>
          </div>
        </header>
        <div className="score-grid">
          {stages.map((stage) => (
            <div key={stage.name}>
              <span>{stage.name}</span>
              <strong>{stage.state}</strong>
            </div>
          ))}
        </div>
      </section>
      <section className="commerce-panel">
        <header>
          <div>
            <p className="eyebrow">Product promotion</p>
            <h2>Separate promotion decision</h2>
          </div>
          <span>{readiness.ready ? "READY" : "BLOCKED"}</span>
        </header>
        <div className="risk-list">
          {readiness.items.map((item) => (
            <article key={item.code}>
              <span className={`priority-mark priority-${item.severity}`}>
                {item.severity}
              </span>
              <div>
                <strong>{item.code.replaceAll("_", " ")}</strong>
                <p>{item.message}</p>
              </div>
            </article>
          ))}
        </div>
        {!promotion && readiness.ready && (
          <form action={requestAction}>
            <input type="hidden" name="hypothesis_id" value={hypothesisId} />
            <label>
              Brand
              <select name="brand_id" required>
                {brands.map((brand) => (
                  <option value={brand.id} key={brand.id}>
                    {brand.name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Promotion reason
              <textarea
                name="reason"
                required
                placeholder="Explain why this hypothesis should become a Build-owned Product."
              />
            </label>
            <button
              className="primary-button"
              disabled={requestPending || !brands.length}
            >
              Request Product Promotion
            </button>
          </form>
        )}
        {promotion && (
          <div className="decision-consequence">
            <span>Promotion approval</span>
            <strong>{approval?.status ?? promotion.status}</strong>
          </div>
        )}
        {promotion &&
          !promotion.product_id &&
          approval?.status === "approved" && (
            <form action={executeAction}>
              <input type="hidden" name="hypothesis_id" value={hypothesisId} />
              <input
                type="hidden"
                name="approval_id"
                value={promotion.approval_request_id}
              />
              <button className="primary-button" disabled={executePending}>
                Create governed Product
              </button>
            </form>
          )}
        <Message state={requestState} />
        <Message state={executeState} />
      </section>
      {promotion?.product_id && (
        <section className="commerce-panel">
          <header>
            <div>
              <p className="eyebrow">Product Truth workflow</p>
              <h2>
                {comparison?.truth
                  ? `Approved Product Truth v${comparison.truth.version}`
                  : drafts.length
                    ? "Product Truth draft awaiting review"
                    : "Create Product Truth draft"}
              </h2>
            </div>
          </header>
          {!comparison?.truth && !drafts.length && (
            <form action={draftAction}>
              <input
                type="hidden"
                name="product_id"
                value={promotion.product_id}
              />
              <input type="hidden" name="hypothesis_id" value={hypothesisId} />
              <label>
                Canonical summary
                <textarea
                  name="summary"
                  required
                  defaultValue="Initial canonical product definition."
                />
              </label>
              <label>
                Change reason
                <textarea
                  name="change_reason"
                  required
                  defaultValue="Initial truth draft after governed promotion."
                />
              </label>
              <button className="primary-button" disabled={draftPending}>
                Create Product Truth Draft
              </button>
            </form>
          )}
          <Message state={draftState} />
          {currentDraft && !currentDraft.approval_request_id && (
            <form action={reviewAction}>
              <input type="hidden" name="draft_id" value={currentDraft.id} />
              <input type="hidden" name="hypothesis_id" value={hypothesisId} />
              <label>
                Review reason
                <textarea
                  name="reason"
                  required
                  defaultValue="Verify claims, accuracy, and evidence before Product Truth publication."
                />
              </label>
              <button className="primary-button" disabled={reviewPending}>
                Request Product Truth Review
              </button>
            </form>
          )}
          {currentDraft?.approval_request_id && !currentDraft.truth_id && (
            <div className="decision-consequence">
              <span>Truth publication approval</span>
              <strong>{truthApproval?.status ?? currentDraft.status}</strong>
            </div>
          )}
          {currentDraft?.approval_request_id &&
            !currentDraft.truth_id &&
            truthApproval?.status === "approved" && (
              <form action={publishAction}>
                <input type="hidden" name="draft_id" value={currentDraft.id} />
                <input
                  type="hidden"
                  name="hypothesis_id"
                  value={hypothesisId}
                />
                <input
                  type="hidden"
                  name="approval_id"
                  value={currentDraft.approval_request_id}
                />
                <button className="primary-button" disabled={publishPending}>
                  Publish Versioned Product Truth
                </button>
              </form>
            )}
          <Message state={reviewState} />
          <Message state={publishState} />
          {comparison && (
            <div className="thesis-grid">
              {Object.entries(comparison.comparable_fields).map(
                ([field, values]) => (
                  <article key={field}>
                    <span>{field.replaceAll("_", " ")}</span>
                    <p>
                      <b>Hypothesis:</b>{" "}
                      {String(values.hypothesis ?? "UNKNOWN")}
                    </p>
                    <p>
                      <b>Current Product Truth:</b>{" "}
                      {String(values.truth ?? "UNKNOWN")}
                    </p>
                  </article>
                ),
              )}
            </div>
          )}
        </section>
      )}
    </>
  );
}
