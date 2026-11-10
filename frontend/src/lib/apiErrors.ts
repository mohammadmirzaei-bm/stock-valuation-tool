/**
 * The two error shapes from the API contract, plus a network failure state.
 *
 *  - 400 domain error: `{ error_code, message, details }`. `message` is Persian
 *    and must be shown verbatim in a red banner (never replaced by a generic
 *    message). `error_code` is `VALIDATION_ERROR` or `CALCULATION_ERROR`.
 *  - 422 shape error: FastAPI's standard `detail` array with `loc` and `msg`.
 *    Treated as a form bug: mark the field named in `loc`.
 *  - Network/server failure: cannot reach the backend; UI offers Retry + health.
 */

export interface FastApiErrorDetail {
  loc: (string | number)[];
  msg: string;
  type: string;
}

export interface DomainError {
  kind: "domain";
  status: 400;
  error_code: "VALIDATION_ERROR" | "CALCULATION_ERROR" | string;
  message: string;
  details: Record<string, unknown> | null;
}

export interface ShapeError {
  kind: "shape";
  status: 422;
  detail: FastApiErrorDetail[];
}

export interface NetworkError {
  kind: "network";
  message: string;
}

export type ApiError = DomainError | ShapeError | NetworkError;

export function isDomainError(e: unknown): e is DomainError {
  return typeof e === "object" && e !== null && (e as ApiError).kind === "domain";
}

export function isShapeError(e: unknown): e is ShapeError {
  return typeof e === "object" && e !== null && (e as ApiError).kind === "shape";
}

export function isNetworkError(e: unknown): e is NetworkError {
  return typeof e === "object" && e !== null && (e as ApiError).kind === "network";
}

/** Extract the last string segment of a 422 `loc` — the offending field name. */
export function fieldFromLoc(loc: (string | number)[]): string | undefined {
  for (let i = loc.length - 1; i >= 0; i -= 1) {
    const segment = loc[i];
    if (typeof segment === "string") return segment;
  }
  return undefined;
}
