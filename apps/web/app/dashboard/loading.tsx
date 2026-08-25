export default function DashboardLoading() {
  return <div className="dashboard-loading" role="status" aria-label="Loading executive dashboard"><div className="loading-heading" /><div className="loading-grid">{Array.from({ length: 4 }, (_, index) => <div className="loading-card" key={index} />)}</div><span>Loading governed operating evidence…</span></div>;
}
