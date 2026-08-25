import Link from "next/link";
import type { ReactNode } from "react";
import type { ApiResult, DashboardView, DecisionQueueItem, ExecutiveMetric, OperatingSignal } from "../lib/api/types";

type ViewResult = ApiResult<DashboardView>;

function formatMetric(metric: ExecutiveMetric): string {
  if (metric.unit.toUpperCase() === "USD") return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(metric.value);
  if (metric.unit === "%" || metric.unit.toLowerCase() === "percent") return `${metric.value}%`;
  return `${new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 }).format(metric.value)} ${metric.unit}`;
}

function signalHref(signal: OperatingSignal): string {
  const route: Record<string, string> = { intelligence: "/opportunities", decision: "/decisions", build: "/products", growth: "/growth", operations: "/customers", finance: "/analytics", governance: "/decisions" };
  return `${route[signal.domain] ?? "/dashboard"}?signal=${signal.id}`;
}

function DataState({ result, empty, children }: { result: ViewResult; empty: string; children: (data: DashboardView) => ReactNode }) {
  if (!result.ok) return <div className="dashboard-state state-error" role="status"><strong>Section unavailable</strong><span>{result.error.message}</span></div>;
  if (!result.data.metrics.length && !result.data.signals.length && !result.data.decisions.length) return <div className="dashboard-state"><strong>{empty}</strong><span>This view will update when governed source records are available.</span></div>;
  return children(result.data);
}

function MetricList({ metrics }: { metrics: ExecutiveMetric[] }) {
  if (!metrics.length) return <div className="dashboard-state compact"><strong>Awaiting metric observations</strong></div>;
  return <div className="real-metric-grid">{metrics.map((metric) => <article className="real-metric" key={metric.id}><span>{metric.metric_name}</span><strong>{formatMetric(metric)}</strong><small>{metric.metric_type} · {metric.source_domain}</small></article>)}</div>;
}

function SignalList({ signals, empty }: { signals: OperatingSignal[]; empty: string }) {
  if (!signals.length) return <div className="dashboard-state compact"><strong>{empty}</strong></div>;
  return <div className="executive-list">{signals.map((signal) => <Link className="executive-row" href={signalHref(signal)} key={signal.id}><span className={`severity-dot severity-${signal.severity}`} /><span><strong>{signal.title}</strong><small>{signal.impact}</small></span><span className="row-meta">{signal.status} →</span></Link>)}</div>;
}

function DecisionList({ decisions }: { decisions: DecisionQueueItem[] }) {
  const pending = decisions.filter((decision) => decision.status !== "closed");
  if (!pending.length) return <div className="dashboard-state compact"><strong>No pending decisions</strong><span>Human review queue is clear.</span></div>;
  return <div className="executive-list">{pending.map((decision) => <Link className="executive-row" href={`/decisions?item=${decision.id}`} key={decision.id}><span className={`priority-mark priority-${decision.priority}`}>{decision.priority}</span><span><strong>{decision.title}</strong><small>{decision.reason}</small></span><span className="row-meta">{decision.required_action} →</span></Link>)}</div>;
}

export function ExecutiveDashboard({ overview, financial, opportunities, risks, decisions }: { overview: ViewResult; financial: ViewResult; opportunities: ViewResult; risks: ViewResult; decisions: ViewResult }) {
  return <div className="executive-dashboard">
    <section className="executive-heading"><div><p className="eyebrow">Sense → Decide → Execute → Measure → Learn</p><h1>Executive dashboard</h1><p>Live, governed operating evidence from the Commerce OS backend.</p></div><div className="live-contract"><span>Read-only operational view</span><strong>Human authority preserved</strong></div></section>
    <section className="executive-section" aria-labelledby="business-health"><div className="executive-section-heading"><div><p className="section-number">01</p><h2 id="business-health">What is happening?</h2></div><span>Business health</span></div><DataState result={overview} empty="No operating observations yet">{(data) => <><MetricList metrics={data.metrics} /><SignalList signals={data.signals.filter((signal) => signal.status !== "resolved").slice(0, 4)} empty="No active operating signals" /></>}</DataState></section>
    <div className="executive-two-column">
      <section className="executive-section" aria-labelledby="money-health"><div className="executive-section-heading"><div><p className="section-number">02</p><h2 id="money-health">Where is money moving?</h2></div><Link href="/analytics">Analytics →</Link></div><DataState result={financial} empty="Awaiting revenue data">{(data) => <MetricList metrics={data.metrics} />}</DataState></section>
      <section className="executive-section" aria-labelledby="opportunity-health"><div className="executive-section-heading"><div><p className="section-number">03</p><h2 id="opportunity-health">What deserves attention?</h2></div><Link href="/opportunities">Opportunities →</Link></div><DataState result={opportunities} empty="No active opportunities">{(data) => <><MetricList metrics={data.metrics} /><SignalList signals={data.signals.slice(0, 4)} empty="No opportunity signals" /></>}</DataState></section>
    </div>
    <div className="executive-two-column">
      <section className="executive-section risk-section" aria-labelledby="risk-health"><div className="executive-section-heading"><div><p className="section-number">04</p><h2 id="risk-health">What requires intervention?</h2></div><span>Risk overview</span></div><DataState result={risks} empty="No active risk signals">{(data) => <><MetricList metrics={data.metrics} /><SignalList signals={data.signals.filter((signal) => signal.status !== "resolved").slice(0, 5)} empty="No active risk signals" /></>}</DataState></section>
      <section className="executive-section decision-queue-section" aria-labelledby="decision-health"><div className="executive-section-heading"><div><p className="section-number">05</p><h2 id="decision-health">What needs your decision?</h2></div><Link href="/decisions">Committee →</Link></div><DataState result={decisions} empty="No pending decisions">{(data) => <DecisionList decisions={data.decisions} />}</DataState></section>
    </div>
  </div>;
}
