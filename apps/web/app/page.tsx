import Link from "next/link";
import { DecisionCard } from "../components/DecisionCard";
import { MetricCard } from "../components/MetricCard";
import { ModuleCard } from "../components/ModuleCard";
import { moduleContracts } from "../lib/contracts";
import { navigationItems } from "../lib/navigation";

const moduleAccents = ["#d7ff59", "#8be9fd", "#bca7ff", "#ffb86c", "#7de2b8", "#f0c36e", "#ff8fa3", "#88a9ff"];

export default function ControlCenterPage() {
  const dashboard = moduleContracts.dashboard;
  return (
    <div className="control-center">
      <section className="hero-section">
        <div>
          <p className="eyebrow">Executive workspace</p>
          <h1>Commerce OS<br /><span>Control Center</span></h1>
          <p className="hero-copy">See what matters, understand why, and make the decisions that move the business forward—without surrendering human authority.</p>
          <div className="hero-actions">
            <Link className="primary-button" href="/decisions">Review decision queue <span aria-hidden="true">→</span></Link>
            <Link className="secondary-button" href="/dashboard">Open executive dashboard</Link>
          </div>
        </div>
        <aside className="brief-card">
          <div className="brief-card-header"><span>Daily operating brief</span><span className="live-label"><i /> LIVE</span></div>
          <strong>3 decisions need your attention</strong>
          <p>Opportunity evidence is strengthening. Growth execution remains human-controlled.</p>
          <div className="brief-progress"><span style={{ width: "72%" }} /></div>
          <div className="brief-footer"><span>Evidence coverage</span><strong>72%</strong></div>
        </aside>
      </section>

      <section className="metric-grid home-metrics" aria-label="Executive metrics">
        {dashboard.metrics.map((metric) => <MetricCard key={metric.label} {...metric} />)}
      </section>

      <section className="section-block">
        <div className="section-heading"><div><p className="eyebrow">Operating system</p><h2>Business modules</h2></div><p>One evidence chain. Clear domain ownership. Human decisions at every critical boundary.</p></div>
        <div className="module-grid">
          {navigationItems.map((item, index) => (
            <ModuleCard key={item.href} href={item.href} label={item.label} description={item.description} meta={moduleContracts[item.href.slice(1)]?.eyebrow ?? "Commerce OS"} accent={moduleAccents[index]} />
          ))}
        </div>
      </section>

      <section className="section-block decision-section">
        <div className="section-heading"><div><p className="eyebrow">Human authority</p><h2>Need your decision</h2></div><Link href="/decisions">Open committee queue →</Link></div>
        <div className="decision-list home-decision-list">{dashboard.queue.map((item) => <DecisionCard key={item.title} {...item} />)}</div>
      </section>
    </div>
  );
}
