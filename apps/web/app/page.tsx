type Health = { status: string; service: string; version: string };

async function readHealth(): Promise<Health | null> {
  const baseUrl = process.env.API_INTERNAL_URL ?? "http://localhost:8000";
  try {
    const response = await fetch(`${baseUrl}/api/v1/health`, { cache: "no-store" });
    return response.ok ? ((await response.json()) as Health) : null;
  } catch {
    return null;
  }
}

export default async function Home() {
  const health = await readHealth();
  return (
    <main>
      <p className="eyebrow">Engineering foundation</p>
      <h1>Commerce OS</h1>
      <p>No business workflows are enabled in Sprint 001.</p>
      <dl>
        <div>
          <dt>API</dt>
          <dd>{health?.status ?? "unavailable"}</dd>
        </div>
      </dl>
    </main>
  );
}
