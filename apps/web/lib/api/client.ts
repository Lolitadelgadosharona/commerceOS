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

export async function apiRequest<T>(path: string, options: { method?: "GET" | "POST" | "PATCH"; query?: Record<string, string>; body?: unknown } = {}): Promise<ApiResult<T>> {
  const token = apiToken();
  if (!token) {
    return failure("configuration", "A server-side Commerce OS session is required to load operational data.");
  }

  const url = new URL(`${apiBaseUrl()}${path}`);
  for (const [key, value] of Object.entries(options.query ?? {})) url.searchParams.set(key, value);

  let response: Response;
  try {
    response = await fetch(url, {
      cache: "no-store",
      method: options.method ?? "GET",
      headers: { Accept: "application/json", Authorization: `Bearer ${token}`, ...(options.body ? { "Content-Type": "application/json" } : {}) },
      body: options.body ? JSON.stringify(options.body) : undefined,
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

export function apiGet<T>(path: string, query?: Record<string, string>): Promise<ApiResult<T>> {
  return apiRequest<T>(path, { query });
}

export function apiPost<T>(path: string, body: unknown, query?: Record<string, string>): Promise<ApiResult<T>> {
  return apiRequest<T>(path, { method: "POST", body, query });
}

export function apiPatch<T>(path: string, body: unknown, query?: Record<string, string>): Promise<ApiResult<T>> {
  return apiRequest<T>(path, { method: "PATCH", body, query });
}
