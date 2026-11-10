import { describe, it, expect } from "vitest";
import { PREREQ_META, missingPrereqs, type PrereqValues } from "./prerequisites";

const vals = (over: Partial<PrereqValues> = {}): PrereqValues => ({
  forecast: [{ year: 1 }],
  wacc: 9,
  shares: 1000,
  taxRate: 25,
  marketPrice: 500,
  ...over,
});

describe("PREREQ_META — each prerequisite links to the step that provides it", () => {
  it("maps forecast rows to step 1 and WACC to step 2", () => {
    expect(PREREQ_META.forecast).toMatchObject({ step: 1, path: "/forecast" });
    expect(PREREQ_META.wacc).toMatchObject({ step: 2, path: "/wacc" });
  });

  it("maps shares, tax rate and market price to step 3 (the DCF page)", () => {
    expect(PREREQ_META.shares).toMatchObject({ step: 3, path: "/dcf" });
    expect(PREREQ_META.taxRate).toMatchObject({ step: 3, path: "/dcf" });
    expect(PREREQ_META.marketPrice).toMatchObject({ step: 3, path: "/dcf" });
  });

  it("gives every prerequisite a distinct focus id", () => {
    const ids = Object.values(PREREQ_META).map((m) => m.focusId);
    expect(new Set(ids).size).toBe(ids.length);
  });
});

describe("missingPrereqs", () => {
  it("returns nothing when every needed prerequisite is present", () => {
    expect(missingPrereqs(["forecast", "wacc", "shares", "taxRate"], vals())).toEqual([]);
  });

  it("flags empty or null forecast rows", () => {
    expect(missingPrereqs(["forecast"], vals({ forecast: [] }))).toEqual(["forecast"]);
    expect(missingPrereqs(["forecast"], vals({ forecast: null }))).toEqual(["forecast"]);
  });

  it("flags a null or non-positive WACC and non-positive shares", () => {
    expect(missingPrereqs(["wacc"], vals({ wacc: null }))).toEqual(["wacc"]);
    expect(missingPrereqs(["shares", "wacc"], vals({ shares: 0, wacc: 0 }))).toEqual(["wacc", "shares"]);
  });

  it("flags an out-of-range tax rate and a missing market price", () => {
    expect(missingPrereqs(["taxRate"], vals({ taxRate: 100 }))).toEqual(["taxRate"]);
    expect(missingPrereqs(["taxRate"], vals({ taxRate: -1 }))).toEqual(["taxRate"]);
    expect(missingPrereqs(["marketPrice"], vals({ marketPrice: null }))).toEqual(["marketPrice"]);
  });

  it("only reports prerequisites the page actually needs", () => {
    expect(missingPrereqs(["forecast"], vals({ shares: 0, wacc: null }))).toEqual([]);
  });

  it("returns results in canonical step order regardless of the needs order", () => {
    expect(
      missingPrereqs(["shares", "forecast", "wacc"], vals({ forecast: [], wacc: null, shares: 0 })),
    ).toEqual(["forecast", "wacc", "shares"]);
  });
});
