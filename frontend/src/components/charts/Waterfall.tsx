import * as React from "react";
import type { EChartsOption } from "echarts";
import { Chart } from "./Chart";
import { axisStyle, baseOption, chartColors } from "./theme";
import type { DcfResult } from "@/api/types";
import { useFormat } from "@/hooks/useFormat";

/**
 * EV → equity waterfall: enterprise value, plus cash, minus debt, minus minority
 * interest, minus preferred equity, to equity value. Increases use the positive
 * color, decreases the negative color, totals the primary color (spec Step 3).
 */
export function DcfWaterfall({ res }: { res: DcfResult }) {
  const fmt = useFormat();
  const c = chartColors();

  const option = React.useMemo<EChartsOption>(() => {
    const ev = res.enterprise_value;
    const cash = res.cash;
    const debt = res.debt;
    const mi = res.minority_interest;
    const pref = res.preferred_equity;
    const eq = res.equity_value;

    const runningAfterCash = ev + cash;
    const runningAfterDebt = runningAfterCash - debt;
    const runningAfterMi = runningAfterDebt - mi;

    const categories = ["ارزش بنگاه", "+ نقد", "− بدهی", "− اقلیت", "− ممتاز", "ارزش سهام"];
    // [base(transparent), value, color]
    const bars: { cat: string; base: number; val: number; color: string; signed: number }[] = [
      { cat: categories[0], base: 0, val: ev, color: c.primary, signed: ev },
      { cat: categories[1], base: ev, val: cash, color: c.positive, signed: cash },
      { cat: categories[2], base: runningAfterDebt, val: debt, color: c.negative, signed: -debt },
      { cat: categories[3], base: runningAfterMi, val: mi, color: c.negative, signed: -mi },
      { cat: categories[4], base: eq, val: pref, color: c.negative, signed: -pref },
      { cat: categories[5], base: 0, val: eq, color: c.primary, signed: eq },
    ];

    return {
      ...baseOption(c),
      grid: { left: 8, right: 16, top: 24, bottom: 8, containLabel: true },
      xAxis: { type: "category", data: bars.map((b) => b.cat), ...axisStyle(c), axisLabel: { color: c.muted, fontSize: 10, interval: 0, rotate: 20 } },
      yAxis: { type: "value", ...axisStyle(c) },
      tooltip: { ...baseOption(c).tooltip, formatter: (p: any) => `${p.name}: ${fmt.number(bars[p.dataIndex].signed)}` },
      series: [
        { name: "base", type: "bar", stack: "w", itemStyle: { color: "transparent" }, emphasis: { itemStyle: { color: "transparent" } }, data: bars.map((b) => b.base), tooltip: { show: false } },
        {
          name: "value",
          type: "bar",
          stack: "w",
          data: bars.map((b) => ({ value: b.val, itemStyle: { color: b.color } })),
          label: { show: true, position: "top", color: c.text, fontSize: 10, formatter: (p: any) => fmt.number(bars[p.dataIndex].signed) },
        },
      ],
    };
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
