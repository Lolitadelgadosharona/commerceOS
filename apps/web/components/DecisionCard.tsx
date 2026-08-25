import type { QueueItemContract } from "../lib/contracts";
import { StatusBadge } from "./StatusBadge";

export function DecisionCard({ title, detail, status }: QueueItemContract) {
  return (
    <article className="decision-card">
      <div>
        <h3>{title}</h3>
        <p>{detail}</p>
      </div>
      <StatusBadge status={status} />
      <button type="button" aria-label={`Review ${title}`}>Review <span aria-hidden="true">→</span></button>
    </article>
  );
}
