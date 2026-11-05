/**
 * Shared ECharts theming: reads the dark tokens from CSS variables so charts
 * stay consistent with the app and a theme swap is a variable change. Also
 * centralizes the axis / tooltip styling reused by every chart.
 */

import type { EChartsOption } from "echarts";

export function cssVar(name: string, fallback = ""): string {
  if (typeof window === "undefined") return fallback;
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return v || fallback;
}

export interface ChartColors {
  text: string;
  muted: string;
  border: string;
  surface: string;
  primary: string;
  positive: string;
  negative: string;
  warning: string;
}

export function chartColors(): ChartColors {
  return {
    text: cssVar("--text", "#E6EAF2"),
    muted: cssVar("--text-muted", "#9AA6BD"),
    border: cssVar("--border", "#263047"),
    surface: cssVar("--surface", "#171E2E"),
    primary: cssVar("--primary", "#4C8DC9"),
    positive: cssVar("--positive", "#4CAF7A"),
    negative: cssVar("--negative", "#E5645F"),
    warning: cssVar("--warning", "#E0A33A"),
  };
}

/** Base option merged into every chart: transparent bg, dark text, RTL-friendly. */
export function baseOption(c = chartColors()): EChartsOption {
  return {
    backgroundColor: "transparent",
    textStyle: { color: c.text, fontFamily: "JetBrains Mono Variable, Vazirmatn, sans-serif" },
    grid: { left: 8, right: 16, top: 28, bottom: 8, containLabel: true },
    tooltip: {
      backgroundColor: c.surface,
      borderColor: c.border,
      textStyle: { color: c.text, fontSize: 12 },
    },
  };
}

export const axisStyle = (c = chartColors()) => ({
  axisLine: { lineStyle: { color: c.border } },
  axisLabel: { color: c.muted, fontSize: 11 },
  splitLine: { lineStyle: { color: c.border, type: "dashed" as const } },
});
