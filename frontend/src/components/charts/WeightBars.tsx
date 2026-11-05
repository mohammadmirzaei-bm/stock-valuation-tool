import * as React from "react";
import type { EChartsOption } from "echarts";
import { Chart } from "./Chart";
import { axisStyle, baseOption, chartColors } from "./theme";

/**
 * Weight bars for a portfolio: one horizontal bar per asset; positive weights
 * extend right of zero, negative (short) weights extend left (spec Portfolio).
 * `weightsPercent` is the backend `weights_percent` / `risky_weights_percent`.
 */
export function WeightBars({
  names,
  weightsPercent,
  height,
  summary,
}: {
  names: string[];
  weightsPercent: number[];
  height?: number;
  summary?: string;
}) {
  const c = chartColors();

  const option = React.useMemo<EChartsOption>(
    () => ({
      ...baseOption(c),
      grid: { left: 8, right: 24, top: 8, bottom: 8, containLabel: true },
      xAxis: { type: "value", ...axisStyle(c) },
      yAxis: { type: "category", data: names, ...axisStyle(c), splitLine: { show: false } },
      tooltip: {
        ...baseOption(c).tooltip,
        formatter: (p: any) => `${p.name}: ${p.value.toFixed(2)}٪`,
      },
      series: [
        {
          name: "وزن ٪",
          type: "bar",
          data: weightsPercent.map((w) => ({
            value: w,
            itemStyle: { color: w >= 0 ? c.primary : c.negative },
          })),
          label: { show: true, position: "right", color: c.text, fontSize: 10, formatter: (p: any) => `${p.value.toFixed(1)}٪` },
        },
      ],
    }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [names, weightsPercent],
  );

  return (
    <Chart
      option={option}
      height={height ?? Math.max(160, names.length * 36 + 40)}
      summary={summary ?? `وزن دارایی‌ها: ${names.map((n, i) => `${n} ${weightsPercent[i]?.toFixed(1)}٪`).join("، ")}.`}
    />
  );
}
