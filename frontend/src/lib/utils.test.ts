import { describe, it, expect } from "vitest";
import { escapeHtml } from "./utils";

describe("escapeHtml — tooltip interpolation of user-entered names", () => {
  it("neutralizes tag and attribute injection", () => {
    expect(escapeHtml('<img src=x onerror="alert(1)">')).toBe(
      "&lt;img src=x onerror=&quot;alert(1)&quot;&gt;",
    );
  });

  it("escapes ampersands first so entities are not double-decoded", () => {
    expect(escapeHtml("&lt;")).toBe("&amp;lt;");
  });

  it("escapes single quotes", () => {
    expect(escapeHtml("a'b")).toBe("a&#39;b");
  });

  it("leaves plain Persian/numeric text untouched", () => {
    expect(escapeHtml("روش ۱ — DCF")).toBe("روش ۱ — DCF");
  });
});