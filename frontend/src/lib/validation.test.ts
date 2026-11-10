import { describe, it, expect } from "vitest";
import { validateModel, isValid, MIN_SPREAD_PP } from "./validation";
import { F } from "@/config/fields";

describe("validateModel (client mirror rules)", () => {
  const gordon = [F.d0, F.g, F.r];
  const spread = { spread: [{ higher: "r", lower: "g" }] };

  it("accepts a complete, in-range Gordon form", () => {
    expect(validateModel({ d0: 1.5, g: 5, r: 12 }, gordon, spread)).toEqual({});
  });

  it("reports a missing required field", () => {
    const errors = validateModel({ d0: 1.5, g: 5 }, gordon, spread);
    expect(errors.r).toBeTruthy();
    expect(isValid(errors)).toBe(false);
  });

  it("enforces the r − g spread of at least 0.5 percentage points", () => {
    expect(MIN_SPREAD_PP).toBe(0.5);
    const errors = validateModel({ d0: 1.5, g: 5, r: 5.2 }, gordon, spread);
    expect(errors.r).toBeTruthy();
  });

  it("rejects growth above the 0-200% band", () => {
    const errors = validateModel({ d0: 1.5, g: 250, r: 300 }, gordon, spread);
    expect(errors.g).toBeTruthy();
  });

  it("requires integers for count fields", () => {
    const errors = validateModel({ years: 3.5 }, [F.years]);
    expect(errors.years).toBeTruthy();
    expect(validateModel({ years: 3 }, [F.years])).toEqual({});
  });

  it("honors an exclusive maximum (tax / retention < 100%)", () => {
    expect(validateModel({ tax_rate: 100 }, [F.tax_rate]).tax_rate).toBeTruthy();
    expect(validateModel({ tax_rate: 25 }, [F.tax_rate])).toEqual({});
  });

  it("checks greater-than rules (market return > risk-free)", () => {
    const fields = [F.risk_free_rate, F.market_return];
    const opts = { greaterThan: [{ greater: "market_return", smaller: "risk_free_rate" }] };
    expect(validateModel({ risk_free_rate: 10, market_return: 4 }, fields, opts).market_return).toBeTruthy();
    expect(validateModel({ risk_free_rate: 4, market_return: 10 }, fields, opts)).toEqual({});
  });
});
