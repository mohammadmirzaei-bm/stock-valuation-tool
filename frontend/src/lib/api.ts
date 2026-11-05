/**
 * Typed API client for the FastAPI valuation backend.
 *
 * Reads the base URL from `VITE_API_BASE_URL` (dev default: the local uvicorn
 * on :8000, whose CORS already allows the Vite origins). Every calculation is a
 * POST with a JSON body; requests carry exactly the documented fields because
 * the backend models use `extra="forbid"`. A caller-supplied `AbortSignal`
 * cancels in-flight requests when a newer one starts.
 */

import type { ApiError, DomainError, FastApiErrorDetail } from "./apiErrors";

export const API_BASE: string =
  (import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000").replace(/\/+$/, "");

export const VALUATION_BASE = `${API_BASE}/api/valuation`;
export const PORTFOLIO_BASE = `${API_BASE}/api/portfolio`;

function isAbort(e: unknown): boolean {
  return e instanceof DOMException && e.name === "AbortError";
}

async function parseDomainError(res: Response): Promise<DomainError> {
  let message = "خطای نامشخص دامنه";
  let error_code = "CALCULATION_ERROR";
  let details: Record<string, unknown> | null = null;
  try {
    const body = await res.json();
    message = body.message ?? message;
    error_code = body.error_code ?? error_code;
    details = body.details ?? null;
  } catch {
    /* keep defaults if the body is unreadable */
  }
  return { kind: "domain", status: 400, error_code, message, details };
}

async function parseShapeError(res: Response): Promise<ApiError> {
  let detail: FastApiErrorDetail[] = [];
  try {
    const body = await res.json();
    detail = Array.isArray(body.detail) ? body.detail : [];
  } catch {
    /* ignore */
  }
  return { kind: "shape", status: 422, detail };
}

/** POST a JSON body and return the parsed response, or throw an {@link ApiError}. */
export async function apiPost<TResponse>(
  url: string,
  body: unknown,
  signal?: AbortSignal,
): Promise<TResponse> {
  let res: Response;
  try {
    res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal,
    });
  } catch (e) {
    if (isAbort(e)) throw e; // let TanStack Query swallow cancellations
    throw <ApiError>{ kind: "network", message: "Cannot reach the server" };
  }

  if (res.ok) {
    return (await res.json()) as TResponse;
  }
  if (res.status === 400) {
    throw await parseDomainError(res);
  }
  if (res.status === 422) {
    throw await parseShapeError(res);
  }
  // Any other non-2xx is treated as a server/network failure.
  throw <ApiError>{ kind: "network", message: `Server error ${res.status}` };
}

/** Liveness probe used by the network-failure Retry banner. */
export async function checkHealth(signal?: AbortSignal): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/health`, { signal });
    return res.ok;
  } catch {
    return false;
  }
}
