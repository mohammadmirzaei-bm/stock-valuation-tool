import * as React from "react";
import type { EChartsOption } from "echarts";
import { Chart } from "./Chart";
import { axisLabelStyle, axisStyle, barRadius, baseOption, chartColors, legendStyle, resolveColor, seriesPalette } from "./theme";
import { useFormat } from "@/hooks/useFormat";
import { escapeHtml } from "@/lib/utils";

interface Series {
  name: string;
  data: (number | null)[];
  color?: string;
}

/** Horizontal/vertical bar chart, optional stacking; nulls render as gaps. */
export function BarSeriesChart({
  categories,
  series,
  stacked = false,
  horizontal = false,
  height = 260,
  valueLabel,
  summary,
}: {
  categories: string[];
  series: Series[];
  stacked?: boolean;
  horizontal?: boolean;
  height?: number;
  valueLabel?: (v: number | null) => string;
  summary?: string;
}) {
  const c = chartColors();
  const fmt = useFormat();
  const vl = valueLabel ?? ((v: number | null) => fmt.number(v));
  const option = React.useMemo<EChartsOption>(() => {
    const palette = seriesPalette(c);
    const catAxis = { type: "category" as const, data: categories, ...axisStyle(c) };
    const valAxis = { type: "value" as const, ...axisStyle(c), axisLabel: { ...axisLabelStyle(c), formatter: (v: number) => fmt.number(v) } };
    return {
      ...baseOption(c),
      legend: series.length > 1 ? legendStyle(c) : undefined,
      xAxis: horizontal ? valAxis : catAxis,
      yAxis: horizontal ? catAxis : valAxis,
      series: series.map((s, i) => ({
        name: s.name,
        type: "bar" as const,
        stack: stacked ? "total" : undefined,
        data: s.data,
        itemStyle: { color: resolveColor(s.color, palette[i % palette.length]), borderRadius: stacked ? 0 : barRadius(horizontal) },
        label: { show: true, color: c.text, formatter: (p: any) => vl(p.value) },
      })),
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(categories), JSON.stringify(series), stacked, horizontal, fmt.digits]);
  return <Chart option={option} height={height} summary={summary} />;
}

/** Multi-series line chart; null values break the line into gaps (never zero). */
export function LineChart({
  categories,
  series,
  height = 260,
  yName,
  summary,
}: {
  categories: string[];
  series: Series[];
  height?: number;
  yName?: string;
  summary?: string;
}) {
  const c = chartColors();
  const fmt = useFormat();
  const palette = seriesPalette(c);
  const option = React.useMemo<EChartsOption>(
    () => ({
      ...baseOption(c),
      legend: series.length > 1 ? legendStyle(c) : undefined,
      grid: { left: 8, right: 16, top: 32, bottom: 8, containLabel: true },
      xAxis: { type: "category", boundaryGap: false, data: categories, ...axisStyle(c) },
      yAxis: { type: "value", name: yName, ...axisStyle(c), axisLabel: { ...axisLabelStyle(c), formatter: (v: number) => fmt.number(v) } },
      series: series.map((s, i) => ({
        name: s.name,
        type: "line" as const,
        data: s.data,
        connectNulls: false,
        showSymbol: true,
        lineStyle: { color: resolveColor(s.color, palette[i % palette.length]) },
        itemStyle: { color: resolveColor(s.color, palette[i % palette.length]) },
      })),
    }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [JSON.stringify(categories), JSON.stringify(series), yName, fmt.digits],
  );
  return <Chart option={option} height={height} summary={summary} />;
}

/** Combo chart: bars for one series + a line on a second y-axis (Forecast). */
export function ComboBarsLine({
  categories,
  bars,
  line,
  barName,
  lineName,
  height = 300,
  summary,
}: {
  categories: string[];
  bars: number[];
  line: number[];
  barName: string;
  lineName: string;
  height?: number;
  summary?: string;
}) {
  const c = chartColors();
  const fmt = useFormat();
  const option = React.useMemo<EChartsOption>(
    () => ({
      ...baseOption(c),
      legend: legendStyle(c),
      grid: { left: 8, right: 16, top: 32, bottom: 8, containLabel: true },
      tooltip: { ...baseOption(c).tooltip, trigger: "axis", valueFormatter: (v: any) => fmt.number(v as number) },
      xAxis: { type: "category", data: categories, ...axisStyle(c) },
      yAxis: [
        { type: "value", name: barName, ...axisStyle(c), axisLabel: { ...axisLabelStyle(c), formatter: (v: number) => fmt.number(v) } },
        { type: "value", name: lineName, ...axisStyle(c), splitLine: { show: false }, axisLabel: { ...axisLabelStyle(c), formatter: (v: number) => fmt.number(v) } },
      ],
      series: [
        { name: barName, type: "bar", data: bars, itemStyle: { color: c.primary, borderRadius: barRadius() } },
        { name: lineName, type: "line", yAxisIndex: 1, data: line, itemStyle: { color: c.warning }, lineStyle: { color: c.warning } },
      ],
    }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [JSON.stringify(categories), JSON.stringify(bars), JSON.stringify(line), barName, lineName, fmt.digits],
  );
  return <Chart option={option} height={height} summary={summary} />;
}

/** Donut for part-of-whole (WACC weights). */
export function Donut({
  data,
  height = 240,
  summary,
}: {
  data: { name: string; value: number; color?: string }[];
  height?: number;
  summary?: string;
}) {
  const c = chartColors();
  const fmt = useFormat();
  const option = React.useMemo<EChartsOption>(() => {
    const palette = seriesPalette(c);
    return {
      ...baseOption(c),
      legend: legendStyle(c, "bottom"),
      tooltip: { ...baseOption(c).tooltip, formatter: (p: any) => `${p.marker}${escapeHtml(String(p.name))}: ${fmt.number(p.value)} (${fmt.number(p.percent)}%)` },
      series: [
        {
          type: "pie",
          radius: ["45%", "70%"],
          avoidLabelOverlap: true,
          label: { color: c.text, formatter: (p: any) => `${p.name}\n${fmt.number(p.percent)}%` },
          data: data.map((d, i) => ({
            name: d.name,
            value: d.value,
            itemStyle: { color: resolveColor(d.color, palette[i % palette.length]) },
          })),
        },
      ],
    };
  },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [JSON.stringify(data), fmt.digits],
  );
  return <Chart option={option} height={height} summary={summary} />;
}
