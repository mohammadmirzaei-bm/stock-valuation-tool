import { describe, it, expect } from "vitest";
import { formatNumber, formatPercent, formatSigned, formatSignedPercent, formatCurrency, toPersianDigits } from "./format";

describe("format", () => {
  it("groups thousands with Latin digits by default", () => {
    expect(formatNumber(1000)).toBe("1,000");
    expect(formatNumber(22.5)).toBe("22.5");
    expect(formatNumber(140.19, { maxFractionDigits: 2 })).toBe("140.19");
  });

  it("switches to Persian digits when requested", () => {
    expect(formatNumber(1000, { digits: "persian" })).toBe("۱,۰۰۰");
    expect(toPersianDigits("12%")).toBe("۱۲%");
  });

  it("renders null / non-finite as an em dash, never zero", () => {
    expect(formatNumber(null)).toBe("—");
    expect(formatNumber(undefined)).toBe("—");
    expect(formatNumber(NaN)).toBe("—");
    expect(formatPercent(null)).toBe("—");
  });

  it("formats percent that is already in percent units (no ×100)", () => {
    expect(formatPercent(12.5)).toBe("12.5%");
    expect(formatPercent(9)).toBe("9%");
  });

  it("adds a leading + only for positive signed values", () => {
    expect(formatSigned(5)).toBe("+5");
    expect(formatSigned(-3)).toBe("-3");
    expect(formatSignedPercent(8.2)).toBe("+8.2%");
    expect(formatSignedPercent(-1.5)).toBe("-1.5%");
  });

  it("appends the ریال unit for currency", () => {
    expect(formatCurrency(250)).toBe("250 ریال");
  });
});
