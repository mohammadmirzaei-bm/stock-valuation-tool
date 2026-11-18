/**
 * Shared ECharts theming: reads the warm Cursor tokens from CSS variables so
 * charts stay consistent with the app and a theme swap is a variable change.
 * Also centralizes the axis / tooltip styling reused by every chart.
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
    text: cssVar("--text", "#26251E"),
    muted: cssVar("--text-muted", "#67665C"),
    border: cssVar("--border", "rgba(38, 37, 30, 0.1)"),
    surface: cssVar("--popover", "#FBFAF7"),
    primary: cssVar("--primary", "#26251E"),
    positive: cssVar("--positive", "#187A59"),
    negative: cssVar("--negative", "#C22448"),
    warning: cssVar("--warning", "#8F6410"),
  };
}

/** Base option merged into every chart: transparent bg, warm ink, RTL-friendly. */
export function baseOption(c = chartColors()): EChartsOption {
  return {
    backgroundColor: "transparent",
    textStyle: { color: c.text, fontFamily: "JetBrains Mono Variable, Vazirmatn, sans-serif" },
    grid: { left: 8, right: 16, top: 28, bottom: 8, containLabel: true },
    // Tooltip matches the card style: light warm surface, hairline border,
    // diffused ambient lift (Cursor elevation, not a hard drop shadow).
    tooltip: {
      backgroundColor: c.surface,
      borderColor: c.border,
      borderWidth: 1,
      borderRadius: 10,
      padding: [8, 12],
      textStyle: { color: c.text, fontSize: 12 },
      extraCssText: "box-shadow:rgba(38,37,30,0.10) 0px 12px 32px, rgba(38,37,30,0.06) 0px 4px 12px;",
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
 * on the cream surface by hue and luminance (ink, orange, soft blue, gold,
 * lavender, green, crimson). Semantic encodings (heatmap above/below base,
 * football-field market position) keep using the meaning-carrying tokens
 * directly — this palette is only for "series identity" colors.
 */
export function seriesPalette(c = chartColors()): string[] {
  return [
    c.primary,
    cssVar("--chart-2", "#F54E00"),
    cssVar("--chart-3", "#6A8FBF"),
    c.warning,
    cssVar("--chart-4", "#8A6FB8"),
    c.positive,
    cssVar("--chart-5", "#CF2D56"),
  ];
}
