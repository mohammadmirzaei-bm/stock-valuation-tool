import { describe, it, expect } from "vitest";
import { toWire, fromWire, isPercentDisplay } from "./units";

// Acceptance rule: every rate is a decimal on the wire (12% -> 0.12) EXCEPT the
// two raw-percent fields (bond_rate_percent / growth_rate_percent) that pass
// through untouched. This lives entirely in the field `unit`.
describe("toWire / fromWire", () => {
  it("divides rate fields by 100", () => {
    expect(toWire("rate", 12)).toBe(0.12);
    expect(toWire("rate", 5)).toBe(0.05);
    expect(toWire("rate", 0.5)).toBe(0.005);
  });

  it("passes raw-percent fields through untouched", () => {
    expect(toWire("percent-raw", 8)).toBe(8); // /risk-premium bond_rate_percent
    expect(toWire("percent-raw", 10)).toBe(10); // /peg growth_rate_percent
  });

  it("passes money / number / count through", () => {
    expect(toWire("money", 250)).toBe(250);
    expect(toWire("number", 1.2)).toBe(1.2);
    expect(toWire("count", 5)).toBe(5);
  });

  it("round-trips rate and raw fields", () => {
    expect(fromWire("rate", toWire("rate", 12))).toBeCloseTo(12);
    expect(fromWire("percent-raw", toWire("percent-raw", 8))).toBe(8);
  });

  it("flags percent-display units", () => {
    expect(isPercentDisplay("rate")).toBe(true);
    expect(isPercentDisplay("percent-raw")).toBe(true);
    expect(isPercentDisplay("money")).toBe(false);
  });
});
