import { StatusBadge } from "./StatusBadge";

type TopNavigationProps = { apiAvailable: boolean };

export function TopNavigation({ apiAvailable }: TopNavigationProps) {
  return (
    <header className="top-navigation">
      <div className="workspace-context">
        <span>Organization</span>
        <strong>Commerce OS Lab</strong>
        <span className="context-chevron" aria-hidden="true">⌄</span>
      </div>
      <div className="top-actions">
        <div className="environment-status">
          <span className={apiAvailable ? "pulse-dot online" : "pulse-dot"} />
          <span>API</span>
          <StatusBadge status={apiAvailable ? "Online" : "Unavailable"} />
        </div>
        <button className="icon-button" type="button" aria-label="Search control center">⌕</button>
        <button className="icon-button notification-button" type="button" aria-label="View notifications">●<span>3</span></button>
      </div>
    </header>
  );
}
