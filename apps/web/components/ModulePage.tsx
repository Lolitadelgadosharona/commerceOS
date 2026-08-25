import type { ModuleContract } from "../lib/contracts";
import { DecisionCard } from "./DecisionCard";
import { MetricCard } from "./MetricCard";

export function ModulePage({ contract }: { contract: ModuleContract }) {
  return (
    <div className="module-page">
      <section className="page-heading">
        <div><p className="eyebrow">{contract.eyebrow}</p><h1>{contract.title}</h1><p className="page-description">{contract.description}</p></div>
        <div className="api-contract"><span>Future API contract</span><code>{contract.endpoint}</code></div>
      </section>
      <section className="metric-grid" aria-label={`${contract.title} metrics`}>
        {contract.metrics.map((metric) => <MetricCard key={metric.label} {...metric} />)}
      </section>
      <section className="content-grid">
        <div className="panel queue-panel">
          <div className="panel-heading"><div><p className="eyebrow">Active work</p><h2>{contract.queueTitle}</h2></div><button type="button">View all</button></div>
          <div className="decision-list">{contract.queue.map((item) => <DecisionCard key={item.title} {...item} />)}</div>
        </div>
        <aside className="panel insight-panel">
          <div className="insight-mark" aria-hidden="true">OS</div>
          <p className="eyebrow">Operating principle</p><h2>{contract.insightTitle}</h2><p>{contract.insight}</p>
          <div className="confidence-row"><span>Governance boundary</span><strong>Enforced</strong></div>
        </aside>
      </section>
    </div>
  );
}
