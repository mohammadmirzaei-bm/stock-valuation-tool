import { describe, it, expect, vi, afterEach } from "vitest";
import { apiPost } from "./api";
import { fieldFromLoc, isDomainError, isShapeError, isNetworkError } from "./apiErrors";

function jsonResponse(body: unknown, status: number): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

afterEach(() => vi.restoreAllMocks());

describe("apiPost error mapping", () => {
  it("returns parsed JSON on 2xx", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => jsonResponse({ value_per_share: 22.5 }, 200)));
    await expect(apiPost("/x", {})).resolves.toEqual({ value_per_share: 22.5 });
  });

  it("maps 400 to a domain error with the Persian message kept verbatim", async () => {
    const body = { error_code: "VALIDATION_ERROR", message: "نرخ رشد باید کمتر از نرخ تنزیل باشد", details: { spread: 0.5 } };
    vi.stubGlobal("fetch", vi.fn(async () => jsonResponse(body, 400)));
    await expect(apiPost("/x", {})).rejects.toSatisfy((e: unknown) => {
      expect(isDomainError(e)).toBe(true);
      expect((e as { message: string }).message).toBe(body.message);
      return true;
    });
  });

  it("maps 422 to a shape error carrying the detail array", async () => {
    const detail = [{ loc: ["body", "peers", 0, "name"], msg: "field required", type: "missing" }];
    vi.stubGlobal("fetch", vi.fn(async () => jsonResponse({ detail }, 422)));
    await expect(apiPost("/x", {})).rejects.toSatisfy((e: unknown) => {
      expect(isShapeError(e)).toBe(true);
      expect((e as { detail: unknown[] }).detail).toEqual(detail);
      return true;
    });
  });

  it("maps a fetch rejection to a network error", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => {
      throw new Error("boom");
    }));
    await expect(apiPost("/x", {})).rejects.toSatisfy((e: unknown) => isNetworkError(e));
  });

  it("re-throws AbortError so cancellation is not shown as failure", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => {
      throw new DOMException("aborted", "AbortError");
    }));
    await expect(apiPost("/x", {})).rejects.toBeInstanceOf(DOMException);
  });
});

describe("fieldFromLoc", () => {
  it("returns the last string segment", () => {
    expect(fieldFromLoc(["body", "peers", 0, "name"])).toBe("name");
    expect(fieldFromLoc(["query", "r"])).toBe("r");
    expect(fieldFromLoc([0, 1])).toBeUndefined();
  });
});
