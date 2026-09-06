import Link from "next/link";
import type { ApiResult } from "../lib/api/types";
import type {
  ApprovalRequest,
  DecisionQueueRecord,
  Opportunity,
} from "../lib/api/opportunities";
import { isDiscoveryOpportunity } from "../lib/api/opportunities";

const label = (value: string) => value.replaceAll("_", " ");

export function DecisionCommitteeWorkspace({
  approvals,
  decisions,
  opportunities,
  focusItem,
}: {
  approvals: ApiResult<ApprovalRequest[]>;
  decisions: ApiResult<DecisionQueueRecord[]>;
  opportunities: ApiResult<Opportunity[]>;
  focusItem?: string;
}) {
  if (!approvals.ok || !decisions.ok)
    return (
      <div className="commerce-workspace">
        <section className="page-heading">
          <div>
            <p className="eyebrow">Governance</p>
            <h1>Decision Committee</h1>
          </div>
        </section>
        <div className="dashboard-state state-error">
          <strong>Decision workspace unavailable</strong>
          <span>
            {!approvals.ok
              ? approvals.error.message
              : !decisions.ok
                ? decisions.error.message
                : "Unknown failure"}
          </span>
        </div>
      </div>
    );
  const pending = approvals.data.filter((item) => item.status === "pending");
  return (
    <div className="commerce-workspace">
      <section className="page-heading">
        <div>
          <p className="eyebrow">Evidence → recommendation → human authority</p>
          <h1>Decision Committee</h1>
          <p className="page-description">
            A governed queue for approvals. Recommendations remain advisory and
            every recorded decision stays in the approval source of truth.
          </p>
        </div>
        <div className="live-contract">
          <span>Authority owner</span>
          <strong>Governance</strong>
        </div>
      </section>
      <section className="intelligence-metrics" aria-label="Decision overview">
        <article>
          <span>Pending approvals</span>
          <strong>{pending.length}</strong>
          <small>human action required</small>
        </article>
        <article>
          <span>Queue items</span>
          <strong>{decisions.data.length}</strong>
          <small>cross-domain decisions</small>
        </article>
        <article>
          <span>Approved</span>
          <strong>
            {approvals.data.filter((item) => item.status === "approved").length}
          </strong>
          <small>recorded outcomes</small>
        </article>
        <article>
          <span>Rejected</span>
          <strong>
            {approvals.data.filter((item) => item.status === "rejected").length}
          </strong>
          <small>recorded outcomes</small>
        </article>
      </section>
      {!decisions.data.length && !approvals.data.length ? (
        <div className="dashboard-state">
          <strong>No governed decisions yet</strong>
          <span>
            Approval Requests and Decision Queue items will appear here when a
            domain requests human authority.
          </span>
        </div>
      ) : (
        <section className="decision-ledger">
          {decisions.data.map((queue) => {
            const approval = queue.approval_request_id
              ? approvals.data.find(
                  (item) => item.id === queue.approval_request_id,
                )
              : undefined;
            const opportunity =
              approval && opportunities.ok
                ? opportunities.data.find(
                    (item) => item.id === approval.object_id,
                  )
                : undefined;
            const href = approval?.object_type === "shopify_publication"
              ? "/channels/shopify"
              : opportunity
              ? isDiscoveryOpportunity(opportunity)
                ? `/opportunities/${opportunity.id}?kind=candidate`
                : `/decision-committee/${opportunity.id}`
              : null;
            return (
              <article
                className={focusItem === queue.id ? "decision-focus" : ""}
                key={queue.id}
              >
                <header>
                  <div>
                    <span>{queue.domain}</span>
                    <b className={`priority-mark priority-${queue.priority}`}>
                      {queue.priority}
                    </b>
                  </div>
                  <strong>{queue.status}</strong>
                </header>
                <h2>{queue.title}</h2>
                <p>{queue.reason}</p>
                <dl>
                  <div>
                    <dt>Required action</dt>
                    <dd>{label(queue.required_action)}</dd>
                  </div>
                  <div>
                    <dt>Approval state</dt>
                    <dd>{approval?.status ?? "No linked approval"}</dd>
                  </div>
                  <div>
                    <dt>Requester</dt>
                    <dd>{approval?.requester_id ?? "Not recorded"}</dd>
                  </div>
                  <div>
                    <dt>Decision reason</dt>
                    <dd>
                      {approval?.decision_reason ??
                        "Pending human evidence review"}
                    </dd>
                  </div>
                </dl>
                {href ? (
                  <Link href={href}>
                    {approval?.object_type === "shopify_publication"
                      ? "Open Shopify governance workspace →"
                      : approval?.status === "pending"
                      ? "Review evidence and decide →"
                      : "Open decision evidence →"}
                  </Link>
                ) : (
                  <small className="unknown-value">
                    No executable detail link exists for this queue item.
                  </small>
                )}
              </article>
            );
          })}
          {approvals.data
            .filter(
              (item) =>
                !decisions.data.some(
                  (queue) => queue.approval_request_id === item.id,
                ),
            )
            .map((approval) => (
              <article key={approval.id}>
                <header>
                  <div>
                    <span>{label(approval.object_type)}</span>
                  </div>
                  <strong>{approval.status}</strong>
                </header>
                <h2>{label(approval.requested_action)}</h2>
                <p>{approval.reason}</p>
                <dl>
                  <div>
                    <dt>Object</dt>
                    <dd>{approval.object_id}</dd>
                  </div>
                  <div>
                    <dt>Requester</dt>
                    <dd>{approval.requester_id}</dd>
                  </div>
                </dl>
                <small className="unknown-value">
                  No Decision Queue relationship is recorded.
                </small>
              </article>
            ))}
        </section>
      )}
      {!opportunities.ok && (
        <div className="partial-data-note">
          Opportunity context is unavailable. Governance records remain visible;
          detail links are withheld.
        </div>
      )}
      <section className="boundary-panel">
        <p className="eyebrow">Separation of authority</p>
        <h2>The committee never executes commerce actions</h2>
        <p>
          Approval records authorize a bounded next step. They do not publish,
          spend, pay, refund, or launch by themselves; self-approval and
          service-account approval remain prohibited by backend governance.
        </p>
      </section>
    </div>
  );
}
