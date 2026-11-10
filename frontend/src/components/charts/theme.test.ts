import { describe, it, expect } from "vitest";
import { axisLabelStyle, barRadius, baseOption, legendStyle, resolveColor, seriesPalette } from "./theme";

describe("resolveColor — ECharts cannot resolve CSS var() on canvas", () => {
  it("passes a concrete color straight through", () => {
    expect(resolveColor("#4C8DC9", "#000")).toBe("#4C8DC9");
    expect(resolveColor("rgb(1, 2, 3)", "#000")).toBe("rgb(1, 2, 3)");
  });

  it("falls back when no color is given", () => {
    expect(resolveColor(undefined, "#fff")).toBe("#fff");
  });

  it("resolves var(--x) to the fallback when the variable is undefined", () => {
    // jsdom defines no --missing token, so the guard must not leak "var(...)".
    expect(resolveColor("var(--missing)", "#fff")).toBe("#fff");
  });

  it("resolves var(--x) to its computed value when the variable is defined", () => {
    document.documentElement.style.setProperty("--test-accent", "rgb(10, 20, 30)");
    expect(resolveColor("var(--test-accent)", "#fff")).toBe("rgb(10, 20, 30)");
    document.documentElement.style.removeProperty("--test-accent");
  });
});

describe("chart theme — unified axis, legend, tooltip and bar styling", () => {
  it("uses muted 12px axis labels", () => {
    expect(axisLabelStyle()).toMatchObject({ fontSize: 12 });
  });

  it("builds a card-style tooltip: 1px border, rounded, flat (no shadow)", () => {
    const t = baseOption().tooltip as any;
    expect(t.borderWidth).toBe(1);
    expect(t.borderRadius).toBe(10);
    expect(t.extraCssText).toContain("box-shadow:none");
  });

  it("caps bar ends, flipping the rounded corners for horizontal bars", () => {
    expect(barRadius()).toEqual([4, 4, 0, 0]);
    expect(barRadius(true)).toEqual([0, 4, 4, 0]);
  });

  it("places the legend top by default and bottom on request", () => {
    expect(legendStyle()).toMatchObject({ top: 0 });
    expect(legendStyle(undefined, "bottom")).toMatchObject({ bottom: 0 });
  });

  it("exposes a categorical palette of at least six concrete, distinct hues", () => {
    const p = seriesPalette();
    expect(p.length).toBeGreaterThanOrEqual(6);
    expect(new Set(p).size).toBe(p.length);
    // Canvas cannot consume var() — every entry must already be resolved.
    for (const color of p) expect(color).not.toMatch(/^var\(/);
  });
});
