import * as React from "react";
import type { EChartsOption } from "echarts";
import { Chart } from "./Chart";
import { axisLabelStyle, axisStyle, baseOption, chartColors } from "./theme";
import { useFormat } from "@/hooks/useFormat";
import { formatNumber } from "@/lib/format";

export interface SmlPoint {
  /** Beta on the numeric x axis. */
  beta: number;
  /** Return (already in percent units) on the y axis. */
  ret: number;
  label: string;
}

/**
 * Security Market Line drawn on a numeric beta axis (not evenly-spaced
 * categories), so the gap between β=0, β=1 and the stock's β is proportional.
 * The three points are collinear (r = r_f + β(r_m − r_f)); they are sorted by
 * beta before the line is drawn so a β below 1 never doubles the line back.
 */
export function SecurityMarketLine({ points, summary }: { points: SmlPoint[]; summary?: string }) {
  const c = chartColors();
  const { digits } = useFormat();

  const option = React.useMemo<EChartsOption>(() => {
    const sorted = [...points].sort((a, b) => a.beta - b.beta);
    const line = sorted.map((p) => [p.beta, p.ret]);
    const scatter = sorted.map((p) => ({ value: [p.beta, p.ret], name: p.label }));
    return {
      ...baseOption(c),
      grid: { left: 8, right: 24, top: 24, bottom: 8, containLabel: true },
      xAxis: {
        type: "value",
        name: "β",
        scale: true,
        ...axisStyle(c),
        axisLabel: { ...axisLabelStyle(c), formatter: (v: number) => formatNumber(v, { digits }) },
      },
      yAxis: {
        type: "value",
        name: "بازده ٪",
        ...axisStyle(c),
        axisLabel: { ...axisLabelStyle(c), formatter: (v: number) => formatNumber(v, { digits }) },
      },
      tooltip: {
        ...baseOption(c).tooltip,
        formatter: (p: any) =>
          `${sorted[p.dataIndex]?.label ?? ""}<br/>β ${formatNumber(p.value[0], { digits })}: ${formatNumber(
            p.value[1],
            { digits },
          )}٪`,
      },
      series: [
        {
          name: "SML",
          type: "line",
          data: line,
          showSymbol: false,
          lineStyle: { color: c.primary, width: 2 },
          itemStyle: { color: c.primary },
          z: 1,
        },
        {
          name: "نقاط",
          type: "scatter",
          data: scatter,
          symbolSize: 12,
          itemStyle: { color: c.warning },
          label: { show: true, position: "top", color: c.text, fontSize: 10, formatter: (p: any) => p.data.name },
          z: 2,
        },
      ],
    } as EChartsOption;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [points, digits]);

  return (
    <Chart
      option={option}
      height={280}
      summary={
        summary ??
        `خط بازار اوراق بهادار: ${points.map((p) => `${p.label} در بتای ${p.beta}`).join("، ")}.`
      }
    />
  );
}
