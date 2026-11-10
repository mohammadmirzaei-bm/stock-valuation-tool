import * as React from "react";
import type { EChartsOption } from "echarts";
import { Chart } from "./Chart";
import { axisLabelStyle, axisStyle, baseOption, chartColors } from "./theme";
import { useFormat } from "@/hooks/useFormat";
import { formatNumber } from "@/lib/format";
import { escapeHtml } from "@/lib/utils";

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
  const { digits } = useFormat();

  const option = React.useMemo<EChartsOption>(
    () => ({
      ...baseOption(c),
      grid: { left: 8, right: 24, top: 8, bottom: 8, containLabel: true },
      xAxis: { type: "value", ...axisStyle(c), axisLabel: { ...axisLabelStyle(c), formatter: (v: number) => formatNumber(v, { digits }) } },
      yAxis: { type: "category", data: names, ...axisStyle(c), splitLine: { show: false } },
      tooltip: {
        ...baseOption(c).tooltip,
        formatter: (p: any) => `${escapeHtml(String(p.name))}: ${formatNumber(p.value, { digits, minFractionDigits: 2, maxFractionDigits: 2 })}٪`,
      },
      series: [
        {
          name: "وزن ٪",
          type: "bar",
          data: weightsPercent.map((w) => ({
            value: w,
            itemStyle: { color: w >= 0 ? c.primary : c.negative, borderRadius: w >= 0 ? [0, 4, 4, 0] : [4, 0, 0, 4] },
          })),
          label: { show: true, position: "right", color: c.text, fontSize: 10, formatter: (p: any) => `${formatNumber(p.value, { digits, minFractionDigits: 1, maxFractionDigits: 1 })}٪` },
        },
      ],
    }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [names, weightsPercent, digits],
  );

  return (
    <Chart
      option={option}
      height={height ?? Math.max(160, names.length * 36 + 40)}
      summary={summary ?? `وزن دارایی‌ها: ${names.map((n, i) => `${n} ${weightsPercent[i]?.toFixed(1)}٪`).join("، ")}.`}
    />
  );
}
