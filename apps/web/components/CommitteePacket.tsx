import Link from "next/link";
import type { CommitteePacket as Packet } from "../lib/api/opportunities";
import { InvestmentDecisionPanel } from "./InvestmentDecisionPanel";

function List({ items, empty }: { items: string[]; empty: string }) {
  return items.length ? (
    <ul>
      {items.map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  ) : (
    <p className="unknown-value">{empty}</p>
  );
}

export function CommitteePacket({
  packet,
  currentUserId,
}: {
  packet: Packet;
  currentUserId: string;
}) {
  return (
    <div className="commerce-workspace">
      <Link className="back-link" href="/decision-committee">
        ← Decision Committee
      </Link>
      <section className="page-heading">
        <div>
          <p className="eyebrow">Read-only investment committee packet</p>
          <h1>{packet.opportunity.title}</h1>
          <p className="page-description">
            A tenant-scoped composition of recorded evidence, product theses,
            economics, risks, governance state, and launch readiness.
          </p>
        </div>
        <div className="live-contract">
          <span>Source diversity</span>
          <strong>{packet.source_diversity}</strong>
        </div>
      </section>
      <section className="intelligence-metrics">
        <article>
          <span>Evidence</span>
          <strong>{packet.market_evidence.length}</strong>
          <small>opportunity records</small>
        </article>
        <article>
          <span>Signals</span>
          <strong>{packet.market_signals.length}</strong>
          <small>linked observations</small>
        </article>
        <article>
          <span>Product theses</span>
          <strong>{packet.product_theses.length}</strong>
          <small>advisory hypotheses</small>
        </article>
        <article>
          <span>Readiness</span>
          <strong>{packet.launch_readiness.overall_status}</strong>
          <small>not execution authority</small>
        </article>
      </section>
      <div className="commerce-grid">
        <section className="commerce-panel">
          <header>
            <div>
              <p className="eyebrow">Supporting case</p>
              <h2>Evidence for proceeding</h2>
            </div>
          </header>
          <List
            items={packet.supporting_case}
            empty="No supporting evidence recorded."
          />
        </section>
        <section className="commerce-panel">
          <header>
            <div>
              <p className="eyebrow">Opposing case</p>
              <h2>Risks and uncertainty</h2>
            </div>
          </header>
          <List
            items={packet.opposing_case}
            empty="No opposing evidence recorded; absence is not proof of safety."
          />
        </section>
      </div>
      <section className="commerce-panel">
        <header>
          <div>
            <p className="eyebrow">Product and economics traceability</p>
            <h2>Recorded theses</h2>
          </div>
        </header>
        {packet.product_theses.length ? (
          packet.product_theses.map((thesis) => (
            <article className="committee-panel" key={thesis.hypothesis.id}>
              <div>
                <h3>{thesis.hypothesis.name}</h3>
                <p>{thesis.hypothesis.solution_description}</p>
                <Link href={`/products/${thesis.hypothesis.id}`}>
                  Open product traceability →
                </Link>
              </div>
              <div>
                <strong>Economics inputs</strong>
                <List
                  items={thesis.economic_inputs.map(
                    (item) =>
                      `${item.metric}: ${item.value === null ? "UNKNOWN" : item.value} · ${item.classification} · ${item.source}`,
                  )}
                  empty="No field-level economics provenance."
                />
                <strong>Product Truth</strong>
                <p>
                  No approved Product Truth yet. Relationship status:{" "}
                  {thesis.product_truth_relationship_status}.
                </p>
              </div>
            </article>
          ))
        ) : (
          <p className="unknown-value">No product thesis linked.</p>
        )}
      </section>
      <div className="commerce-grid">
        <section className="commerce-panel">
          <header>
            <div>
              <p className="eyebrow">Missing evidence</p>
              <h2>Decision gaps</h2>
            </div>
          </header>
          <List
            items={packet.missing_evidence}
            empty="No missing fields reported by the composition."
          />
        </section>
        <section className="commerce-panel">
          <header>
            <div>
              <p className="eyebrow">Decision-quality warnings</p>
              <h2>Pre-decision checks</h2>
            </div>
          </header>
          {packet.decision_quality_warnings.length ? (
            <div className="risk-list">
              {packet.decision_quality_warnings.map((warning) => (
                <article key={warning.code}>
                  <span
                    className={`priority-mark priority-${warning.severity}`}
                  >
                    {warning.severity}
                  </span>
                  <div>
                    <strong>{warning.code.replaceAll("_", " ")}</strong>
                    <p>{warning.message}</p>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <p>No quality warnings recorded.</p>
          )}
        </section>
      </div>
      <InvestmentDecisionPanel
        opportunityId={packet.opportunity.id}
        approval={packet.approval}
        currentUserId={currentUserId}
        recommendation={packet.investment_memo.recommended_decision}
        readiness={packet.launch_readiness.overall_status}
      />
    </div>
  );
}
