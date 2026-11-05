import * as React from "react";
import type { EChartsOption } from "echarts";
import { Chart } from "./Chart";
import { axisStyle, baseOption, chartColors } from "./theme";

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
  valueLabel = (v: number | null) => (v === null ? "—" : String(v)),
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
  const option = React.useMemo<EChartsOption>(() => {
    const catAxis = { type: "category" as const, data: categories, ...axisStyle(c) };
    const valAxis = { type: "value" as const, ...axisStyle(c), splitLine: { lineStyle: { color: c.border } } };
    return {
      ...baseOption(c),
      legend: series.length > 1 ? { textStyle: { color: c.text }, top: 0 } : undefined,
      xAxis: horizontal ? valAxis : catAxis,
      yAxis: horizontal ? catAxis : valAxis,
      series: series.map((s, i) => ({
        name: s.name,
        type: "bar" as const,
        stack: stacked ? "total" : undefined,
        data: s.data,
        itemStyle: { color: s.color ?? (i === 0 ? c.primary : c.positive) },
        label: { show: true, color: c.text, formatter: (p: any) => valueLabel(p.value) },
      })),
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(categories), JSON.stringify(series), stacked, horizontal]);
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
  const palette = [c.primary, c.positive, c.warning, c.negative];
  const option = React.useMemo<EChartsOption>(
    () => ({
      ...baseOption(c),
      legend: series.length > 1 ? { textStyle: { color: c.text }, top: 0 } : undefined,
      grid: { left: 8, right: 16, top: 32, bottom: 8, containLabel: true },
      xAxis: { type: "category", boundaryGap: false, data: categories, ...axisStyle(c) },
      yAxis: { type: "value", name: yName, ...axisStyle(c) },
      series: series.map((s, i) => ({
        name: s.name,
        type: "line" as const,
        data: s.data,
        connectNulls: false,
        showSymbol: true,
        lineStyle: { color: s.color ?? palette[i % palette.length] },
        itemStyle: { color: s.color ?? palette[i % palette.length] },
      })),
    }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [JSON.stringify(categories), JSON.stringify(series), yName],
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
  const option = React.useMemo<EChartsOption>(
    () => ({
      ...baseOption(c),
      legend: { textStyle: { color: c.text }, top: 0 },
      grid: { left: 8, right: 16, top: 32, bottom: 8, containLabel: true },
      xAxis: { type: "category", data: categories, ...axisStyle(c) },
      yAxis: [
        { type: "value", name: barName, ...axisStyle(c) },
        { type: "value", name: lineName, ...axisStyle(c), splitLine: { show: false } },
      ],
      series: [
        { name: barName, type: "bar", data: bars, itemStyle: { color: c.primary } },
        { name: lineName, type: "line", yAxisIndex: 1, data: line, itemStyle: { color: c.warning }, lineStyle: { color: c.warning } },
      ],
    }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [JSON.stringify(categories), JSON.stringify(bars), JSON.stringify(line), barName, lineName],
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
  const option = React.useMemo<EChartsOption>(
    () => ({
      ...baseOption(c),
      legend: { textStyle: { color: c.text }, bottom: 0 },
      series: [
        {
          type: "pie",
          radius: ["45%", "70%"],
          avoidLabelOverlap: true,
          label: { color: c.text, formatter: "{b}\n{d}%" },
          data: data.map((d, i) => ({
            name: d.name,
            value: d.value,
            itemStyle: { color: d.color ?? (i === 0 ? c.primary : c.warning) },
          })),
        },
      ],
    }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [JSON.stringify(data)],
  );
  return <Chart option={option} height={height} summary={summary} />;
}
