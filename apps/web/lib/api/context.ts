import "server-only";
import { apiGet } from "./client";
import type { ApiResult, AuthenticatedActor } from "./types";

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export async function resolveExecutiveContext(): Promise<ApiResult<AuthenticatedActor>> {
  const actor = await apiGet<AuthenticatedActor>("/api/v1/auth/me");
  if (!actor.ok) return actor;
  if (!UUID_PATTERN.test(actor.data.organization_id) || !UUID_PATTERN.test(actor.data.user_id)) {
    return { ok: false, error: { kind: "contract", message: "The authenticated actor context is malformed." } };
  }

  const expectedOrganization = process.env.COMMERCE_OS_ORGANIZATION_ID?.trim();
  if (expectedOrganization && !UUID_PATTERN.test(expectedOrganization)) {
    return { ok: false, error: { kind: "configuration", message: "COMMERCE_OS_ORGANIZATION_ID must be a valid UUID." } };
  }
  if (expectedOrganization && expectedOrganization !== actor.data.organization_id) {
    return { ok: false, error: { kind: "authorization", message: "The configured organization does not match the authenticated session." } };
  }
  return actor;
}
