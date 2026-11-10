import * as React from "react";
import * as echarts from "echarts";
import type { EChartsOption } from "echarts";
import { cn } from "@/lib/utils";

export type ChartInstance = echarts.ECharts;

interface ChartProps {
  option: EChartsOption;
  height?: number | string;
  className?: string;
  /** Text alternative for screen readers (accessibility: every chart gets one). */
  summary?: string;
  /** Called with the instance once created, so parents can call getDataURL. */
  onInit?: (chart: ChartInstance) => void;
}

/**
 * Thin ECharts wrapper: creates the instance, applies option updates, resizes
 * with its container and disposes on unmount. Uses the canvas renderer so PNG
 * export (getDataURL) works for the football-field and portfolio charts.
 */
export function Chart({ option, height = 320, className, summary, onInit }: ChartProps) {
  const elRef = React.useRef<HTMLDivElement | null>(null);
  const chartRef = React.useRef<ChartInstance | null>(null);

  React.useEffect(() => {
    if (!elRef.current) return;
    const chart = echarts.init(elRef.current, undefined, { renderer: "canvas" });
    chartRef.current = chart;
    onInit?.(chart);
    const ro = new ResizeObserver(() => chart.resize());
    ro.observe(elRef.current);
    return () => {
      ro.disconnect();
      chart.dispose();
      chartRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  React.useEffect(() => {
    chartRef.current?.setOption(option, { notMerge: true });
  }, [option]);

  return (
    <div className={cn("w-full", className)}>
      <div ref={elRef} style={{ height, width: "100%" }} role="img" aria-label={summary} />
    </div>
  );
}
