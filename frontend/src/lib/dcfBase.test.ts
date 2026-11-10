import { describe, it, expect } from "vitest";
import { buildDcfBase } from "./dcfBase";
import { REFERENCE_PROJECTIONS } from "./samples";

const wf = (over: Partial<Parameters<typeof buildDcfBase>[0]> = {}) => ({
  projections: REFERENCE_PROJECTIONS,
  waccPercent: 9,
  balanceSheet: {
    cash: 500,
    debt: 1500,
    minorityInterest: 50,
    preferredEquity: 25,
    sharesOutstanding: 100,
    taxRate: 25,
  },
  ...over,
});

describe("buildDcfBase — the shared DCF request fragment", () => {
  it("converts percent inputs to wire decimals via the unit layer", () => {
    const base = buildDcfBase(wf());
    expect(base.wacc).toBeCloseTo(0.09, 10);
    expect(base.tax_rate).toBeCloseTo(0.25, 10);
  });

  it("passes the balance sheet and shares through untouched", () => {
    const base = buildDcfBase(wf());
    expect(base).toMatchObject({
      shares_outstanding: 100,
      cash: 500,
      debt: 1500,
      minority_interest: 50,
      preferred_equity: 25,
    });
  });

  it("copies the forecast rows so a request body never aliases the store", () => {
    const store = wf();
    const base = buildDcfBase(store);
    expect(base.projections).toEqual(REFERENCE_PROJECTIONS);
    expect(base.projections[0]).not.toBe(store.projections![0]);
  });

  it("falls back to an empty row list when the store has no forecast yet", () => {
    expect(buildDcfBase(wf({ projections: null })).projections).toEqual([]);
  });
});
