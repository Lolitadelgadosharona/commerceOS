type StatusBadgeProps = {
  status: "Ready" | "Review" | "Monitoring" | "Draft" | "Blocked" | "Online" | "Unavailable";
};

export function StatusBadge({ status }: StatusBadgeProps) {
  return <span className={`status-badge status-${status.toLowerCase()}`}>{status}</span>;
}
