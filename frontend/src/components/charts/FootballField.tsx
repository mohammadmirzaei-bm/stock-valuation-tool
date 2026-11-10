import * as React from "react";
import type { EChartsOption } from "echarts";
import { Chart, type ChartInstance } from "./Chart";
import { axisStyle, baseOption, chartColors } from "./theme";
import type { FootballFieldResult, FootballFieldRowResult } from "@/api/types";
import { marketPositionView, type Tone } from "@/lib/semantics";
import { escapeHtml } from "@/lib/utils";

const TONE_COLOR: Record<Tone, string> = {
  positive: "positive",
  primary: "primary",
  warning: "warning",
  negative: "negative",
  neutral: "primary",
};

/**
 * Football field: one horizontal low→high bar per method, a diamond at each mid,
 * a dashed market-price line and a translucent overlap band. The range bar is a
 * custom-series rect drawn from the pixel of `low` to the pixel of `high`, so a
 * negative low spans correctly across zero — a transparent stacked base cannot,
 * because ECharts stacks positive and negative values separately. Bars are tinted
 * by market_position (below/inside/above) and the tint always pairs with the text
 * label in the tooltip — never color alone (spec Step 6).
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
    const colors = rows.map(colorOf);

    // custom-series datum: [low, high]; the category index is the dataIndex.
    const rangeData = rows.map((r) => [r.low, r.high]);
    const mids = rows.map((r, i) => [r.mid, i]);

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
          return `<b>${escapeHtml(r.method)}</b><br/>بازه: ${format(r.low)} – ${format(r.high)}<br/>میانی: ${format(
            r.mid,
          )}${view ? `<br/>موقعیت: ${view.label}` : ""}`;
        },
      },
      series: [
        {
          name: "بازه ارزش",
          type: "custom",
          renderItem: (params: any, api: any): any => {
            const i = params.dataIndex;
            const pLow = api.coord([api.value(0), i]);
            const pHigh = api.coord([api.value(1), i]);
            const height = api.size([0, 1])[1] * 0.55;
            const x = Math.min(pLow[0], pHigh[0]);
            const width = Math.max(Math.abs(pHigh[0] - pLow[0]), 1);
            const y = pLow[1] - height / 2;
            return { type: "rect", shape: { x, y, width, height, r: 4 }, style: { fill: colors[i], opacity: 0.75 } };
          },
          data: rangeData,
          z: 2,
        },
        {
          name: "مقدار میانی",
          type: "scatter",
          symbol: "diamond",
          symbolSize: 13,
          data: mids,
          itemStyle: { color: c.text, borderColor: c.surface, borderWidth: 1 },
          z: 5,
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
      ],
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
