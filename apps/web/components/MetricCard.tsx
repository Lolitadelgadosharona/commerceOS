import type { MetricContract } from "../lib/contracts";

export function MetricCard({ label, value, change, tone = "neutral" }: MetricContract) {
  return (
    <article className={`metric-card metric-${tone}`}>
      <p>{label}</p>
      <strong>{value}</strong>
      <span>{change}</span>
    </article>
  );
}
