import * as React from "react";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { Sparkline } from "./Sparkline";
import { cn } from "@/lib/utils";

type Tone = "default" | "positive" | "negative" | "warning";

const toneText: Record<Tone, string> = {
  default: "text-foreground",
  positive: "text-positive",
  negative: "text-negative",
  warning: "text-warning",
};

/**
 * One overview metric tile (the workspace's KPI card): label + optional pill,
 * a large tabular number, a signed delta with an icon (never color alone), and
 * an optional sparkline. Empty values render an em dash with a hint.
 */
export function MetricCard({
  label,
  badge,
  value,
  hint,
  delta,
  spark,
  sparkTone,
  tone = "default",
}: {
  label: string;
  badge?: string;
  value: React.ReactNode;
  hint?: React.ReactNode;
  delta?: { text: string; dir: "up" | "down" | "flat"; tone?: Tone } | null;
  spark?: (number | null | undefined)[];
  sparkTone?: string;
  tone?: Tone;
}) {
  const DeltaIcon = delta?.dir === "up" ? TrendingUp : delta?.dir === "down" ? TrendingDown : Minus;
  return (
    <div className="metric-card flex flex-col p-4">
      <div className="flex items-center justify-between gap-2">
        <span className="truncate text-xs text-muted-foreground">{label}</span>
        {badge && (
          <span className="shrink-0 rounded-full bg-surface-2 px-2 py-0.5 text-[10px] font-medium text-muted-foreground">{badge}</span>
        )}
      </div>
      <div className={cn("num mt-2 text-[26px] font-bold leading-tight", toneText[tone])}>{value}</div>
      <div className="mt-1 flex min-h-5 items-center gap-1.5 text-xs">
        {delta ? (
          <span className={cn("inline-flex items-center gap-1", toneText[delta.tone ?? "default"])}>
            <DeltaIcon className="h-3.5 w-3.5" aria-hidden />
            <span className="num">{delta.text}</span>
          </span>
        ) : (
          hint && <span className="text-muted-foreground">{hint}</span>
        )}
        {delta && hint && <span className="truncate text-muted-foreground">{hint}</span>}
      </div>
      <div className="mt-3">
        {spark ? <Sparkline data={spark} tone={sparkTone} label={`روند ${label}`} /> : <div className="h-9" aria-hidden />}
      </div>
    </div>
  );
}