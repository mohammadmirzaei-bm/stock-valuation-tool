import { describe, it, expect } from "vitest";
import {
  EQUITY_SAMPLES,
  WACC_SAMPLE,
  BALANCE_SHEET_SAMPLE,
  REFERENCE_PROJECTIONS,
  MULTIPLES_SAMPLE,
  FOOTBALL_SAMPLE,
} from "./samples";
import { F } from "@/config/fields";
import { toWire } from "./units";

// The samples are the exact inputs behind the documented hero results
// (Gordon 1.5 / 5% / 12% → 22.50; WACC 600/400/12/6/25 → 9.00%). The frontend
// never recomputes them; it only guarantees the inputs and the wire conversion.
describe("reference samples", () => {
  it("Gordon matches the acceptance anchor inputs", () => {
    expect(EQUITY_SAMPLES.gordon).toEqual({ d0: 1.5, g: 5, r: 12 });
    // r (12%) is a rate → 0.12 on the wire; g (5%) → 0.05; d0 stays raw money.
    expect(toWire(F.r.unit, EQUITY_SAMPLES.gordon.r)).toBe(0.12);
    expect(toWire(F.g.unit, EQUITY_SAMPLES.gordon.g)).toBe(0.05);
    expect(toWire(F.d0.unit, EQUITY_SAMPLES.gordon.d0)).toBe(1.5);
  });

  it("the two raw-percent exceptions are NOT divided", () => {
    expect(F.bond_rate_percent.unit).toBe("percent-raw");
    expect(F.growth_rate_percent.unit).toBe("percent-raw");
    expect(toWire(F.bond_rate_percent.unit, 8)).toBe(8);
    expect(toWire(F.growth_rate_percent.unit, 10)).toBe(10);
  });

  it("WACC sample matches the 9.00% reference inputs", () => {
    expect(WACC_SAMPLE).toEqual({ equity: 600, debt: 400, cost_of_equity: 12, cost_of_debt: 6, tax_rate: 25 });
  });

  it("the 5-year FCFF reference drives the DCF/scenarios samples", () => {
    expect(REFERENCE_PROJECTIONS.length).toBe(5);
    expect(REFERENCE_PROJECTIONS[0].ebit).toBe(1000);
    expect(REFERENCE_PROJECTIONS[4].ebit).toBe(1400);
    expect(BALANCE_SHEET_SAMPLE.shares_outstanding).toBe(100);
  });

  it("multiples + football samples are internally consistent", () => {
    expect(MULTIPLES_SAMPLE.peers.length).toBe(4);
    expect(MULTIPLES_SAMPLE.kind).toBe("ev_ebitda");
    for (const r of FOOTBALL_SAMPLE.ranges) expect(r.low).toBeLessThanOrEqual(r.mid);
    for (const r of FOOTBALL_SAMPLE.ranges) expect(r.mid).toBeLessThanOrEqual(r.high);
  });
});
