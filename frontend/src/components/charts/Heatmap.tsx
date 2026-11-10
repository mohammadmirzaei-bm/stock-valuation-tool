import * as React from "react";
import { chartColors, cssVar } from "./theme";
import { cn } from "@/lib/utils";

interface HeatmapProps {
  rowLabels: string[];
  colLabels: string[];
  matrix: (number | null)[][];
  baseRow: number;
  baseCol: number;
  baseValue: number;
  format: (v: number) => string;
}

/**
 * Sensitivity heatmap. Rows are WACC, columns terminal growth. Cells colored
 * green above / red below the base value; the base cell is outlined and tagged;
 * null cells are hatched and never shown as zero (spec Rule 4 + Step 4b).
 */
export function Heatmap({ rowLabels, colLabels, matrix, baseRow, baseCol, baseValue, format }: HeatmapProps) {
  const c = chartColors();

  const numeric: number[] = [];
  for (const row of matrix) for (const v of row) if (v !== null && Number.isFinite(v)) numeric.push(v);
  const lo = Math.min(...numeric, baseValue);
  const hi = Math.max(...numeric, baseValue);
  const span = hi - lo || 1;

  const cellBg = (v: number, isBase: boolean): React.CSSProperties => {
    const intensity = Math.min(Math.abs(v - baseValue) / span, 1) * 0.55 + 0.06;
    const above = v >= baseValue;
    const color = isBase ? cssVar("--primary", c.primary) : above ? cssVar("--positive", c.positive) : cssVar("--negative", c.negative);
    return { backgroundColor: hexToRgba(color, isBase ? 0.25 : intensity) };
  };

  return (
    <div dir="ltr" className="overflow-x-auto">
      <table className="border-separate border-spacing-0.5 text-table-num">
        <thead>
          <tr>
            <th className="p-1 text-[10px] font-normal text-muted-foreground">WACC \ g</th>
            {colLabels.map((cl, j) => (
              <th key={j} className={cn("min-w-14 p-1 text-[10px] font-medium", j === baseCol ? "text-primary" : "text-muted-foreground")}>
                {cl}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {matrix.map((row, i) => (
            <tr key={i}>
              <th className={cn("whitespace-nowrap p-1 text-right text-[10px] font-medium", i === baseRow ? "text-primary" : "text-muted-foreground")}>
                {rowLabels[i]}
              </th>
              {row.map((v, j) => {
                const isBase = i === baseRow && j === baseCol;
                if (v === null || !Number.isFinite(v)) {
                  return (
                    <td key={j}>
                      <div className="null-cell flex h-9 min-w-14 items-center justify-center rounded-sm border border-border text-[10px]" title="ترکیب نامعتبر">
                        —
                      </div>
                    </td>
                  );
                }
                return (
                  <td key={j}>
                    <div
                      className={cn(
                        "num relative flex h-9 min-w-14 items-center justify-center rounded-sm border text-[11px]",
                        isBase ? "border-primary ring-1 ring-primary" : "border-border",
                      )}
                      style={cellBg(v, isBase)}
                    >
                      {format(v)}
                      {isBase && <span className="absolute -top-2 left-0 text-[8px] text-primary">پایه</span>}
                    </div>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function hexToRgba(hex: string, alpha: number): string {
  const h = hex.trim();
  if (h.startsWith("#")) {
    const n = h.length === 4 ? `#${h[1]}${h[1]}${h[2]}${h[2]}${h[3]}${h[3]}` : h;
    const r = parseInt(n.slice(1, 3), 16);
    const g = parseInt(n.slice(3, 5), 16);
    const b = parseInt(n.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }
  return h;
}
