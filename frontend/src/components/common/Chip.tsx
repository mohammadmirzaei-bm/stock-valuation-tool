import * as React from "react";
import { Check, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface ChipProps {
  children: React.ReactNode;
  tone?: "store" | "source" | "neutral";
  onRemove?: () => void;
  className?: string;
}

/**
 * Small pill. `store` renders the "From step N ✓" source chip; `source` marks
 * where a football-field range came from. Never relies on color alone — the
 * label text carries the meaning.
 */
export function Chip({ children, tone = "neutral", onRemove, className }: ChipProps) {
  const tones: Record<string, string> = {
    store: "border-positive/40 bg-positive/10 text-positive",
    source: "border-primary/40 bg-primary/10 text-primary",
    neutral: "border-border bg-muted text-muted-foreground",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs",
        tones[tone],
        className,
      )}
    >
      {tone === "store" && <Check className="h-3 w-3" aria-hidden />}
      <span>{children}</span>
      {onRemove && (
        <button
          type="button"
          onClick={onRemove}
          className="ml-0.5 rounded-full hover:bg-black/20"
          aria-label="حذف"
        >
          <X className="h-3 w-3" />
        </button>
      )}
    </span>
  );
}
