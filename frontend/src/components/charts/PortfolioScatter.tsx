import * as React from "react";
import type { EChartsOption } from "echarts";
import { Chart, type ChartInstance } from "./Chart";
import { axisLabelStyle, axisStyle, baseOption, chartColors, legendStyle } from "./theme";
import type { PortfolioAnalysisResult } from "@/api/types";
import { useFormat } from "@/hooks/useFormat";
import { formatNumber } from "@/lib/format";
import { escapeHtml } from "@/lib/utils";

/**
 * Risk/return scatter for the optimizer (spec Portfolio): asset dots, the
 * efficient-frontier curve, min-variance / tangency / equal-weight markers and
 * the capital allocation line drawn through its two helper points. Axes are
 * volatility (x) and return (y), both in percent — taken straight from the
 * response `_percent` fields, never recomputed.
 */
export function PortfolioScatter({
  res,
  onInit,
}: {
  res: PortfolioAnalysisResult;
  onInit?: (chart: ChartInstance) => void;
}) {
  const c = chartColors();
  const { digits } = useFormat();

  const option = React.useMemo<EChartsOption>(() => {
    const vol = (p: { volatility_percent: number }) => p.volatility_percent;
    const ret = (p: { expected_return_percent: number }) => p.expected_return_percent;

    const assets = res.assets.map((a) => ({
      name: a.name,
      value: [a.volatility_percent, a.expected_return_percent],
    }));

    const frontier = [...res.frontier]
      .sort((a, b) => vol(a) - vol(b))
      .map((p) => [vol(p), ret(p)]);

    const cal = res.capital_allocation_line.points.map((p) => [p.volatility_percent, p.expected_return_percent]);

    const marker = (p: { volatility_percent: number; expected_return_percent: number }, color: string, label: string) => ({
      name: label,
      type: "scatter" as const,
      symbol: "pin",
      symbolSize: 34,
      data: [[vol(p), ret(p)]],
      itemStyle: { color },
      label: { show: true, formatter: label, color: c.text, fontSize: 9, position: "inside" },
    });

    return {
      ...baseOption(c),
      legend: { ...legendStyle(c), type: "scroll" },
      grid: { left: 8, right: 24, top: 40, bottom: 8, containLabel: true },
      xAxis: { type: "value", name: "نوسان ٪", nameLocation: "middle", nameGap: 26, scale: true, ...axisStyle(c), axisLabel: { ...axisLabelStyle(c), formatter: (v: number) => formatNumber(v, { digits }) } },
      yAxis: { type: "value", name: "بازده ٪", scale: true, ...axisStyle(c), axisLabel: { ...axisLabelStyle(c), formatter: (v: number) => formatNumber(v, { digits }) } },
      tooltip: {
        ...baseOption(c).tooltip,
        formatter: (p: any) =>
          p.seriesType === "scatter" && p.data?.name
            ? `${escapeHtml(String(p.data.name))}: نوسان ${formatNumber(p.value[0], { digits, minFractionDigits: 2, maxFractionDigits: 2 })}٪، بازده ${formatNumber(p.value[1], { digits, minFractionDigits: 2, maxFractionDigits: 2 })}٪`
            : `${escapeHtml(String(p.seriesName))}`,
      },
      series: [
        {
          name: "دارایی‌ها",
          type: "scatter",
          symbolSize: 12,
          data: assets,
          itemStyle: { color: c.primary },
          label: { show: true, formatter: (p: any) => p.data.name, position: "top", color: c.muted, fontSize: 10 },
        },
        {
          name: "مرز کارا",
          type: "line",
          data: frontier,
          showSymbol: false,
          lineStyle: { color: c.positive, width: 2 },
          itemStyle: { color: c.positive },
        },
        {
          name: "خط تخصیص سرمایه",
          type: "line",
          data: cal,
          showSymbol: false,
          lineStyle: { color: c.warning, type: "dashed", width: 1.5 },
          itemStyle: { color: c.warning },
        },
        marker(res.min_variance, c.muted, "حداقل واریانس"),
        marker(res.tangency, c.positive, "مماس"),
        marker(res.equal_weight, c.negative, "وزن برابر"),
      ],
    } as EChartsOption;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [res, digits]);

  const summary = `نمودار پراکندگی ریسک-بازده با ${res.assets.length} دارایی، مرز کارا و خط تخصیص سرمایه.`;
  return <Chart option={option} height={380} onInit={onInit} summary={summary} />;
}
