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

/**
 * ECharts draws on canvas, so it cannot resolve a CSS `var(--x)` string. This
 * guard turns any `var(--name)` color into its computed value (falling back to
 * `fallback` when the variable is undefined) and passes concrete colors through.
 */
export function resolveColor(color: string | undefined, fallback: string): string {
  if (!color) return fallback;
  const m = /^var\((--[\w-]+)\)$/.exec(color.trim());
  return m ? cssVar(m[1], fallback) : color;
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
    // Tooltip matches the card style: flat surface, 1px border, rounded, no shadow.
    tooltip: {
      backgroundColor: c.surface,
      borderColor: c.border,
      borderWidth: 1,
      borderRadius: 10,
      padding: [8, 12],
      textStyle: { color: c.text, fontSize: 12 },
      extraCssText: "box-shadow:none;",
    },
  };
}

/** Axis tick labels: muted, 12px. Spread into an axis, then add a `formatter`. */
export const axisLabelStyle = (c = chartColors()) => ({
  color: c.muted,
  fontSize: 12,
});

/** Axis line + muted dashed gridlines + 12px labels (single source of truth). */
export const axisStyle = (c = chartColors()) => ({
  axisLine: { lineStyle: { color: c.border } },
  axisTick: { show: false },
  axisLabel: axisLabelStyle(c),
  splitLine: { lineStyle: { color: c.border, type: "dashed" as const } },
});

/** Consistent legend: small round swatches, muted 12px text, top or bottom. */
export const legendStyle = (c = chartColors(), position: "top" | "bottom" = "top") => ({
  ...(position === "top" ? { top: 0 } : { bottom: 0 }),
  icon: "roundRect" as const,
  itemWidth: 10,
  itemHeight: 10,
  itemGap: 12,
  textStyle: { color: c.muted, fontSize: 12 },
});

/** Rounded bar ends: cap the two outer corners for the bar's orientation. */
export function barRadius(horizontal = false): number[] {
  return horizontal ? [0, 4, 4, 0] : [4, 4, 0, 0];
}

/**
 * Categorical palette for multi-series charts: seven hues that stay separable
 * on the dark surface (blue, teal, violet, amber, rose, green, sky). Semantic
 * encodings (heatmap above/below base, football-field market position) keep
 * using the meaning-carrying tokens directly — this palette is only for
 * "series identity" colors.
 */
export function seriesPalette(c = chartColors()): string[] {
  return [
    c.primary,
    cssVar("--chart-2", "#56B8A8"),
    cssVar("--chart-3", "#A78BDA"),
    c.warning,
    cssVar("--chart-4", "#E88FB4"),
    c.positive,
    cssVar("--chart-5", "#7DC4E8"),
  ];
}
