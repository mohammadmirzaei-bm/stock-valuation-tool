import { CircleCheck, TriangleAlert, TrendingDown, type LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

export type InsightTone = "warning" | "negative" | "positive";

const TONE: Record<InsightTone, { Icon: LucideIcon; box: string; accent: string }> = {
  warning: { Icon: TriangleAlert, box: "border-warning/40 bg-warning/10", accent: "text-warning" },
  negative: { Icon: TrendingDown, box: "border-negative/40 bg-negative/10", accent: "text-negative" },
  positive: { Icon: CircleCheck, box: "border-positive/40 bg-positive/10", accent: "text-positive" },
};

/**
 * A single insight: icon + one-line title + one-line explanation, tinted by tone.
 * Replaces ad-hoc warning paragraphs so every "heads-up" (terminal-value share,
 * negative equity, ROE below the required return, ...) reads the same way.
 */
export function InsightCallout({
  tone,
  title,
  explanation,
}: {
  tone: InsightTone;
  title: string;
  explanation?: string;
}) {
  const { Icon, box, accent } = TONE[tone];
  return (
    <div className={cn("flex items-start gap-2 rounded-md border px-3 py-2", box)}>
      <Icon className={cn("mt-0.5 h-4 w-4 shrink-0", accent)} aria-hidden />
      <div className="min-w-0 space-y-0.5">
        <div className={cn("text-sm font-medium", accent)}>{title}</div>
        {explanation && <div className="text-xs text-muted-foreground">{explanation}</div>}
      </div>
    </div>
  );
}
