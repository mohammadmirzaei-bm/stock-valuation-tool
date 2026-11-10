import { describe, it, expect } from "vitest";
import { capmSmlPoints, SML_LABEL, gordonDividendBody, ENTRIES } from "./EquityPages";
import { EQUITY_GROUP, EQUITY_META } from "@/config/models";

describe("Equity navigation — every sidebar link resolves to a real model", () => {
  it.each(EQUITY_GROUP.map((e) => [e.id, e.path] as const))(
    "%s (%s) has matching registry metadata and a result entry",
    (id, path) => {
      // The route is /equity/:id, so the path's last segment is the lookup key.
      const routeId = path.split("/").pop();
      expect(routeId).toBe(id);
      expect(EQUITY_META[id], `EQUITY_META missing "${id}"`).toBeDefined();
      expect(ENTRIES[id], `ENTRIES missing "${id}"`).toBeDefined();
    },
  );
});

describe("CAPM — Security Market Line", () => {
  it("uses the renamed heading, not the old wording", () => {
    expect(SML_LABEL).toBe("خط بازار اوراق بهادار (SML)");
    expect(SML_LABEL).not.toBe("خط امنیتی بازار (SML)");
  });

  it("builds three points on a numeric beta axis (0, 1, stock beta)", () => {
    const pts = capmSmlPoints(
      { beta: 1.5, risk_free_rate_percent: 4, market_return_percent: 10, required_return_percent: 13 },
      0,
    );
    expect(pts.map((p) => p.beta)).toEqual([0, 1, 1.5]);
    expect(pts.map((p) => p.ret)).toEqual([4, 10, 13]);
    expect(pts.map((p) => p.label)).toEqual(["r_f", "r_m", "سهم"]);
  });

  it("falls back to the form market return when market_return_percent is null", () => {
    const pts = capmSmlPoints(
      { beta: 0.8, risk_free_rate_percent: 4, market_return_percent: null, required_return_percent: 8.8 },
      10,
    );
    expect(pts[1].ret).toBe(10);
    expect(pts[2].beta).toBe(0.8);
  });
});

describe("Gordon — 10-year dividend projection body", () => {
  it("projects 10 periods with g converted percent → decimal via the unit layer", () => {
    expect(gordonDividendBody(1.5, 5)).toEqual({ d0: 1.5, g: 0.05, periods: 10 });
  });

  it("stays null until both d0 and g are present", () => {
    expect(gordonDividendBody(undefined, 5)).toBeNull();
    expect(gordonDividendBody(1.5, undefined)).toBeNull();
  });
});
