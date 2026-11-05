import * as React from "react";
import type { EChartsOption } from "echarts";
import { Chart, type ChartInstance } from "./Chart";
import { axisStyle, baseOption, chartColors } from "./theme";
import type { FootballFieldResult, FootballFieldRowResult } from "@/api/types";
import { marketPositionView, type Tone } from "@/lib/semantics";

const TONE_COLOR: Record<Tone, string> = {
  positive: "positive",
  primary: "primary",
  warning: "warning",
  negative: "negative",
  neutral: "primary",
};

/**
 * Football field: one horizontal low→high bar per method (floating bar via a
 * transparent base + a range bar), a diamond at each mid, a dashed market-price
 * line and a translucent overlap band. Bars are tinted by market_position
 * (below/inside/above) and the tint always pairs with the text label in the
 * tooltip — never color alone (spec Step 6).
 */
export function FootballFieldChart({
  res,
  onInit,
  format,
}: {
  res: FootballFieldResult;
  onInit?: (chart: ChartInstance) => void;
  format: (v: number) => string;
}) {
  const c = chartColors();
  const rows = res.rows;

  const option = React.useMemo<EChartsOption>(() => {
    const categories = rows.map((r) => r.method);

    const colorOf = (r: FootballFieldRowResult) => {
      const view = marketPositionView(r.market_position);
      const key = view ? TONE_COLOR[view.tone] : "primary";
      return c[key as keyof typeof c] ?? c.primary;
    };

    const rangeData = rows.map((r) => ({ value: r.high - r.low, itemStyle: { color: colorOf(r), opacity: 0.75 } }));
    const mids = rows.map((r, i) => [r.mid, i]);

    const series: EChartsOption["series"] = [
      {
        name: "پایه",
        type: "bar",
        stack: "ff",
        data: rows.map((r) => r.low),
        itemStyle: { color: "transparent" },
        emphasis: { itemStyle: { color: "transparent" } },
        tooltip: { show: false },
        barWidth: "55%",
      },
      {
        name: "بازه ارزش",
        type: "bar",
        stack: "ff",
        data: rangeData,
        barWidth: "55%",
        markLine:
          res.market_price !== null
            ? {
                symbol: "none",
                lineStyle: { color: c.text, type: "dashed", width: 1.5 },
                label: { formatter: `بازار ${format(res.market_price)}`, color: c.text, position: "insideEndTop" },
                data: [{ xAxis: res.market_price }],
              }
            : undefined,
        markArea: res.has_overlap
          ? {
              silent: true,
              itemStyle: { color: c.primary, opacity: 0.1 },
              data: [[{ xAxis: res.overlap_low }, { xAxis: res.overlap_high }]],
            }
          : undefined,
      },
      {
        name: "مقدار میانی",
        type: "scatter",
        symbol: "diamond",
        symbolSize: 13,
        data: mids,
        itemStyle: { color: c.text, borderColor: c.surface, borderWidth: 1 },
        z: 5,
      },
    ];

    return {
      ...baseOption(c),
      grid: { left: 8, right: 24, top: 16, bottom: 8, containLabel: true },
      xAxis: { type: "value", scale: true, ...axisStyle(c) },
      yAxis: { type: "category", data: categories, ...axisStyle(c), axisLabel: { color: c.text, fontSize: 12 } },
      tooltip: {
        ...baseOption(c).tooltip,
        formatter: (p: any) => {
          const r = rows[p.dataIndex];
          if (!r) return "";
          const view = marketPositionView(r.market_position);
          return `<b>${r.method}</b><br/>بازه: ${format(r.low)} – ${format(r.high)}<br/>میانی: ${format(
            r.mid,
          )}${view ? `<br/>موقعیت: ${view.label}` : ""}`;
        },
      },
      series,
    } as EChartsOption;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [res]);

  return (
    <Chart
      option={option}
      height={Math.max(200, rows.length * 48 + 80)}
      onInit={onInit}
      summary={`زمین فوتبال با ${rows.length} روش. ${rows
        .map((r) => `${r.method}: ${format(r.low)} تا ${format(r.high)}، میانی ${format(r.mid)}`)
        .join("؛ ")}.`}
    />
  );
}
