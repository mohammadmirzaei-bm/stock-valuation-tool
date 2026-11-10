import * as React from "react";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

/** The formula, always rendered as an LTR island (spec "Results column, 1"). */
export function FormulaStrip({ formula }: { formula: string }) {
  return (
    <div className="formula rounded-md border border-border bg-bg px-3 py-2 text-sm text-muted-foreground">
      {formula}
    </div>
  );
}

/**
 * The results column stack. While a newer request is in flight the previous
 * result stays visible but dimmed (never a skeleton over a known answer), and
 * the region is marked busy for assistive tech. One definition for every page.
 */
export function ResultStack({ updating = false, children }: { updating?: boolean; children: React.ReactNode }) {
  return (
    <div className={cn("space-y-4", updating && "is-updating")} aria-busy={updating || undefined}>
      {children}
    </div>
  );
}

type Tone = "default" | "positive" | "negative" | "warning";

const toneClass: Record<Tone, string> = {
  default: "text-foreground",
  positive: "text-positive",
  negative: "text-negative",
  warning: "text-warning",
};

/** The single large answer (price / value per share / WACC). */
export function Hero({
  label,
  value,
  hint,
  tone = "default",
}: {
  label: string;
  value: React.ReactNode;
  hint?: React.ReactNode;
  tone?: Tone;
}) {
  return (
    <div className="space-y-1">
      <div className="text-sm text-muted-foreground">{label}</div>
      <div className={cn("num text-[40px] font-bold leading-tight", toneClass[tone])} data-testid="hero-value">{value}</div>
      {hint && <div className="text-xs text-muted-foreground">{hint}</div>}
    </div>
  );
}

export interface CardItem {
  label: string;
  value: React.ReactNode;
  hint?: React.ReactNode;
  tone?: Tone;
}

/** A row of small component cards ("show the parts, not only the answer"). */
export function ComponentCards({ items }: { items: CardItem[] }) {
  if (items.length === 0) return null;
  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
      {items.map((item, i) => (
        <Card key={i} className="p-2.5">
          <div className="text-xs text-muted-foreground">{item.label}</div>
          <div className={cn("num mt-1 text-base font-medium", toneClass[item.tone ?? "default"])}>
            {item.value}
          </div>
          {item.hint && <div className="mt-0.5 text-[11px] text-muted-foreground">{item.hint}</div>}
        </Card>
      ))}
    </div>
  );
}
