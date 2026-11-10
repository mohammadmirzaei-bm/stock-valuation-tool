import { describe, it, expect } from "vitest";
import { boxTooltipText } from "./BoxPlot";
import type { PeerStatisticsResult } from "@/api/types";

const stats = {
  min: 10,
  q1: 12.5,
  median: 15,
  q3: 17.5,
  max: 20,
  mean: 15.25,
} as PeerStatisticsResult;

describe("boxTooltipText — HTML tooltip with the active digit mode", () => {
  it("joins lines with <br/>, never \\n", () => {
    const html = boxTooltipText(stats, "latin");
    expect(html).toContain("<br/>");
    expect(html).not.toContain("\n");
  });

  it("keeps Latin digits in latin mode", () => {
    expect(boxTooltipText(stats, "latin")).toContain("میانه: 15");
  });

  it("converts every value to Persian digits in persian mode", () => {
    const html = boxTooltipText(stats, "persian");
    expect(html).toContain("کمینه: ۱۰");
    expect(html).toContain("میانه: ۱۵");
    expect(html).toContain("میانگین: ۱۵.۲۵");
  });
});
