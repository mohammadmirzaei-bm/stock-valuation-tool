import * as React from "react";
import type { EChartsOption } from "echarts";
import { Chart } from "./Chart";
import { axisStyle, baseOption, chartColors } from "./theme";
import type { DcfResult } from "@/api/types";
import { useFormat } from "@/hooks/useFormat";

type WaterfallFields = Pick<
  DcfResult,
  "enterprise_value" | "cash" | "debt" | "minority_interest" | "preferred_equity" | "equity_value"
>;

export interface WaterfallBar {
  cat: string;
  /** Running value the bar starts at. */
  from: number;
  /** Running value the bar ends at. */
  to: number;
  /** Signed delta (or the total, for the two total bars) shown in the label/tooltip. */
  signed: number;
  tone: "total" | "positive" | "negative";
}

/**
 * EV → equity bridge expressed as [from, to] running spans. Kept pure so the
 * geometry can be tested with negative equity: a decrease that crosses zero has
 * `to < from`, and the chart draws each span with a custom series (rect from the
 * pixel of `from` to the pixel of `to`). A transparent stacked base cannot do
 * this — ECharts stacks positive and negative values separately, so a negative
 * running total collapses the floating bar.
 */
export function dcfWaterfallBars(res: WaterfallFields): WaterfallBar[] {
  const ev = res.enterprise_value;
  const afterCash = ev + res.cash;
  const afterDebt = afterCash - res.debt;
  const afterMi = afterDebt - res.minority_interest;
  const eq = res.equity_value;
  return [
    { cat: "ارزش بنگاه", from: 0, to: ev, signed: ev, tone: "total" },
    { cat: "+ نقد", from: ev, to: afterCash, signed: res.cash, tone: "positive" },
    { cat: "− بدهی", from: afterCash, to: afterDebt, signed: -res.debt, tone: "negative" },
    { cat: "− اقلیت", from: afterDebt, to: afterMi, signed: -res.minority_interest, tone: "negative" },
    { cat: "− ممتاز", from: afterMi, to: eq, signed: -res.preferred_equity, tone: "negative" },
    { cat: "ارزش سهام", from: 0, to: eq, signed: eq, tone: "total" },
  ];
}

/**
 * EV → equity waterfall: enterprise value, plus cash, minus debt, minus minority
 * interest, minus preferred equity, to equity value. Increases use the positive
 * color, decreases the negative color, totals the primary color (spec Step 3).
 * Each bar is a floating rect from its `from` to its `to` value, so a negative
 * equity value renders below the zero line instead of collapsing.
 */
export function DcfWaterfall({ res }: { res: DcfResult }) {
  const fmt = useFormat();
  const c = chartColors();

  const option = React.useMemo<EChartsOption>(() => {
    const bars = dcfWaterfallBars(res);
    const toneColor: Record<WaterfallBar["tone"], string> = {
      total: c.primary,
      positive: c.positive,
      negative: c.negative,
    };
    // custom-series datum: [categoryIndex, from, to]
    const data = bars.map((b, i) => [i, b.from, b.to]);

    return {
      ...baseOption(c),
      grid: { left: 8, right: 16, top: 30, bottom: 8, containLabel: true },
      xAxis: {
        type: "category",
        data: bars.map((b) => b.cat),
        ...axisStyle(c),
        axisLabel: { color: c.muted, fontSize: 10, interval: 0, rotate: 20 },
      },
      yAxis: { type: "value", ...axisStyle(c) },
      tooltip: {
        ...baseOption(c).tooltip,
        formatter: (p: any) => `${bars[p.dataIndex].cat}: ${fmt.number(bars[p.dataIndex].signed)}`,
      },
      series: [
        {
          type: "custom",
          renderItem: (params: any, api: any): any => {
            const i = params.dataIndex;
            const pFrom = api.coord([api.value(0), api.value(1)]);
            const pTo = api.coord([api.value(0), api.value(2)]);
            const width = api.size([1, 0])[0] * 0.5;
            const x = pFrom[0] - width / 2;
            const y = Math.min(pFrom[1], pTo[1]);
            const height = Math.max(Math.abs(pTo[1] - pFrom[1]), 1);
            const bar = bars[i];
            return {
              type: "group",
              children: [
                { type: "rect", shape: { x, y, width, height }, style: { fill: toneColor[bar.tone] } },
                {
                  type: "text",
                  style: {
                    text: fmt.number(bar.signed),
                    x: pFrom[0],
                    y: y - 5,
                    textAlign: "center",
                    textVerticalAlign: "bottom",
                    fill: c.text,
                    fontSize: 10,
                  },
                },
              ],
            };
          },
          data,
        },
      ],
    } as EChartsOption;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [res]);

  return (
    <Chart
      option={option}
      height={300}
      summary={`پل ارزش: از ارزش بنگاه ${fmt.number(res.enterprise_value)} تا ارزش سهام ${fmt.number(res.equity_value)} با افزودن نقد ${fmt.number(res.cash)} و کسر بدهی ${fmt.number(res.debt)}، اقلیت ${fmt.number(res.minority_interest)} و ممتاز ${fmt.number(res.preferred_equity)}.`}
    />
  );
}
