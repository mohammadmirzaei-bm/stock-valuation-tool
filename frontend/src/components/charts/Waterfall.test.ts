import { describe, it, expect } from "vitest";
import { dcfWaterfallBars } from "./Waterfall";

// EV + cash − debt − minority − preferred = 800 + 100 − 1200 − 50 − 50 = −400.
const NEGATIVE_EQUITY = {
  enterprise_value: 800,
  cash: 100,
  debt: 1200,
  minority_interest: 50,
  preferred_equity: 50,
  equity_value: -400,
};

describe("dcfWaterfallBars — negative equity bridge geometry", () => {
  const bars = dcfWaterfallBars(NEGATIVE_EQUITY);

  it("ends the equity total bar below zero when equity is negative", () => {
    const equity = bars[bars.length - 1];
    expect(equity.cat).toBe("ارزش سهام");
    expect(equity.from).toBe(0);
    expect(equity.to).toBe(-400);
    expect(equity.signed).toBe(-400);
    expect(equity.tone).toBe("total");
  });

  it("renders a decrease that crosses zero as to < from (debt bar)", () => {
    const debt = bars[2];
    expect(debt.from).toBe(900); // EV + cash
    expect(debt.to).toBe(-300); // 900 − 1200
    expect(debt.to).toBeLessThan(debt.from);
    expect(debt.signed).toBe(-1200);
    expect(debt.tone).toBe("negative");
  });

  it("keeps the running spans connected end-to-end", () => {
    // Each non-total bar starts where the previous running value ended.
    expect(bars[1].from).toBe(bars[0].to); // +نقد starts at EV
    expect(bars[2].from).toBe(bars[1].to); // −بدهی starts after cash
    expect(bars[3].from).toBe(bars[2].to); // −اقلیت starts after debt
    expect(bars[4].from).toBe(bars[3].to); // −ممتاز starts after minority
    expect(bars[4].to).toBe(NEGATIVE_EQUITY.equity_value); // bridge lands on equity
  });

  it("still produces an above-zero equity bar for a positive fixture", () => {
    const positive = dcfWaterfallBars({
      enterprise_value: 1000,
      cash: 200,
      debt: 300,
      minority_interest: 0,
      preferred_equity: 0,
      equity_value: 900,
    });
    expect(positive[positive.length - 1].to).toBe(900);
    // Every running span stays at or above zero (contrast with the negative case).
    expect(positive.every((b) => b.from >= 0 && b.to >= 0)).toBe(true);
  });
});
