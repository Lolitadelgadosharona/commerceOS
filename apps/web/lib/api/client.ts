import "server-only";
import type { ApiFailure, ApiResult } from "./types";

const DEFAULT_API_URL = "http://localhost:8000";

export function apiBaseUrl(): string {
  return (process.env.API_INTERNAL_URL ?? DEFAULT_API_URL).replace(/\/$/, "");
}

export function apiToken(): string | null {
  const token = process.env.COMMERCE_OS_API_TOKEN?.trim();
  return token || null;
}

function failure(kind: ApiFailure["kind"], message: string, status?: number): ApiResult<never> {
  return { ok: false, error: { kind, message, status } };
}

export async function apiGet<T>(path: string, query?: Record<string, string>): Promise<ApiResult<T>> {
  const token = apiToken();
  if (!token) {
    return failure("configuration", "A server-side Commerce OS session is required to load operational data.");
  }

  const url = new URL(`${apiBaseUrl()}${path}`);
  for (const [key, value] of Object.entries(query ?? {})) url.searchParams.set(key, value);

  let response: Response;
  try {
    response = await fetch(url, {
      cache: "no-store",
      headers: { Accept: "application/json", Authorization: `Bearer ${token}` },
      signal: AbortSignal.timeout(5_000),
    });
  } catch {
    return failure("network", "The Commerce OS API could not be reached.");
  }

  if (!response.ok) {
    const kind = response.status === 401 ? "authentication" : response.status === 403 ? "authorization" : "response";
    return failure(kind, `The Commerce OS API returned ${response.status} for ${path}.`, response.status);
  }

  try {
    return { ok: true, data: await response.json() as T };
  } catch {
    return failure("contract", `The Commerce OS API returned invalid JSON for ${path}.`);
  }
}
