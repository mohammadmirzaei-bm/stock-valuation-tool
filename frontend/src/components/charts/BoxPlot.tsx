import * as React from "react";
import type { EChartsOption } from "echarts";
import { Chart } from "./Chart";
import { axisLabelStyle, axisStyle, baseOption, chartColors } from "./theme";
import type { PeerStatisticsResult } from "@/api/types";
import { useFormat } from "@/hooks/useFormat";
import { formatNumber, type DigitMode } from "@/lib/format";

/**
 * Box-plot tooltip as HTML: one stat per line, joined with <br/> (never \n, which
 * does not break lines in an HTML tooltip) and every number run through the
 * active digit mode so Persian digits show when selected.
 */
export function boxTooltipText(stats: PeerStatisticsResult, digits: DigitMode): string {
  const n = (v: number) => formatNumber(v, { digits });
  return [
    `کمینه: ${n(stats.min)}`,
    `Q1: ${n(stats.q1)}`,
    `میانه: ${n(stats.median)}`,
    `Q3: ${n(stats.q3)}`,
    `بیشینه: ${n(stats.max)}`,
    `میانگین: ${n(stats.mean)}`,
  ].join("<br/>");
}

/**
 * Peer-multiple distribution as a single horizontal box plot (min → Q1 → median
 * → Q3 → max) with a mean marker, plus the excluded peers greyed alongside
 * (spec Step 5: box plot over q1/median/q3/mean/min/max). Values come straight
 * from the backend statistics; nothing is recomputed here.
 */
export function BoxPlot({ stats, summary }: { stats: PeerStatisticsResult; summary?: string }) {
  const c = chartColors();
  const { digits } = useFormat();

  const option = React.useMemo<EChartsOption>(() => {
    // boxplot data order: [min, Q1, median, Q3, max]
    const box = [stats.min, stats.q1, stats.median, stats.q3, stats.max];
    return {
      ...baseOption(c),
      grid: { left: 8, right: 24, top: 16, bottom: 8, containLabel: true },
      xAxis: { type: "value", ...axisStyle(c), scale: true, axisLabel: { ...axisLabelStyle(c), formatter: (v: number) => formatNumber(v, { digits }) } },
      yAxis: { type: "category", data: ["همتاها"], ...axisStyle(c), splitLine: { show: false } },
      tooltip: {
        ...baseOption(c).tooltip,
        formatter: () => boxTooltipText(stats, digits),
      },
      series: [
        {
          name: "توزیع ضریب",
          type: "boxplot",
          data: [box],
          itemStyle: { color: c.surface, borderColor: c.primary },
        } as never,
        {
          name: "میانگین",
          type: "scatter",
          symbol: "diamond",
          symbolSize: 12,
          data: [[stats.mean, 0]],
          itemStyle: { color: c.warning },
        },
      ],
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stats, digits]);

  return (
    <Chart
      option={option}
      height={180}
      summary={
        summary ??
        `جعبه‌نمودار ضریب همتایان: کمینه ${stats.min}، چارک اول ${stats.q1}، میانه ${stats.median}، چارک سوم ${stats.q3}، بیشینه ${stats.max}، میانگین ${stats.mean}.`
      }
    />
  );
}
