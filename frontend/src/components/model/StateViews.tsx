import * as React from "react";
import { AlertTriangle, TriangleAlert, Server, RotateCcw } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/common/Skeleton";
import { checkHealth } from "@/lib/api";
import { isShapeError, type ApiError } from "@/lib/apiErrors";
import type { FastApiErrorDetail } from "@/lib/apiErrors";
import { cn } from "@/lib/utils";

/** Red banner for a 400 domain error — the Persian message shown verbatim. */
export function DomainErrorBanner({ message }: { message: string }) {
  return (
    <div
      role="alert"
      className="flex items-start gap-2 rounded-md border border-negative/50 bg-negative/10 px-3 py-2 text-sm text-negative"
    >
      <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
      <span className="whitespace-pre-line">{message}</span>
    </div>
  );
}

/** 422 shape error — surfaced as a form bug (fields are also marked inline). */
export function ShapeErrorNote({ detail }: { detail: FastApiErrorDetail[] }) {
  return (
    <div role="alert" className="rounded-md border border-warning/50 bg-warning/10 px-3 py-2 text-xs text-warning">
      <div className="flex items-center gap-1.5 font-medium">
        <AlertTriangle className="h-3.5 w-3.5" /> خطای شکل درخواست
      </div>
      <ul className="mt-1 list-inside list-disc">
        {detail.map((d, i) => (
          <li key={i} className="num text-left">
            {d.loc.join(".")} — {d.msg}
          </li>
        ))}
      </ul>
    </div>
  );
}

/** Network/server failure with Retry; on retry it re-probes /health first. */
export function NetworkBanner({ onRetry }: { onRetry?: () => void }) {
  const [status, setStatus] = React.useState<"idle" | "checking">("idle");
  return (
    <div
      role="alert"
      className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-border bg-muted px-3 py-2 text-sm"
    >
      <div className="flex items-center gap-2 text-foreground">
        <Server className="h-4 w-4 text-muted-foreground" aria-hidden />
        نمی‌توان به سرور متصل شد
      </div>
      <Button
        type="button"
        variant="outline"
        size="sm"
        onClick={async () => {
          setStatus("checking");
          const ok = await checkHealth();
          if (!ok) console.warn("[health] backend unreachable");
          onRetry?.();
          setStatus("idle");
        }}
      >
        <RotateCcw className={cn("h-4 w-4", status === "checking" && "animate-spin")} />
        تلاش دوباره
      </Button>
    </div>
  );
}

/** Renders the correct banner for any ApiError union member. */
export function ErrorState({ error, onRetry }: { error: ApiError; onRetry?: () => void }) {
  if (error.kind === "domain") return <DomainErrorBanner message={error.message} />;
  if (isShapeError(error)) return <ShapeErrorNote detail={error.detail} />;
  return <NetworkBanner onRetry={onRetry} />;
}

/** Empty state: the formula/explanation plus a "Try sample values" prompt. */
export function EmptyState({
  formula,
  whenSuitable,
  onLoadSample,
}: {
  formula: string;
  whenSuitable: string;
  onLoadSample: () => void;
}) {
  return (
    <Card className="p-6 text-center">
      <div className="formula mx-auto max-w-md text-sm text-muted-foreground">{formula}</div>
      <p className="mt-3 text-sm text-muted-foreground">{whenSuitable}</p>
      <Button type="button" variant="secondary" className="mt-4" onClick={onLoadSample}>
        استفاده از مقادیر نمونه
      </Button>
    </Card>
  );
}

/** Incomplete form prompt (no request sent). */
export function IncompleteState() {
  return (
    <Card className="p-6 text-center text-sm text-muted-foreground">
      برای دیدن نتیجه، فیلدهای مشخص‌شده را کامل کنید.
    </Card>
  );
}

/**
 * First-load skeleton shaped like the real result column: the hero answer
 * (label → big number → unit/hint), a row of component cards, then a chart block.
 */
export function ResultSkeleton() {
  return (
    <div className="space-y-4" role="status">
      <span className="sr-only">در حال بارگذاری نتیجه</span>
      {/* Hero: label above, big number, unit/hint below */}
      <div className="space-y-2">
        <Skeleton className="h-4 w-28" />
        <Skeleton className="h-10 w-56" />
        <Skeleton className="h-3 w-40" />
      </div>
      {/* Component-cards row (mirrors ComponentCards' grid) */}
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="space-y-2 rounded-card border border-border bg-surface p-2.5">
            <Skeleton className="h-3 w-16" />
            <Skeleton className="h-5 w-20" />
          </div>
        ))}
      </div>
      {/* Chart block */}
      <Skeleton className="h-56 w-full rounded-card" />
    </div>
  );
}

/** Hatched null cell / gap marker (never rendered as zero). */
export function NullCell({ title = "ترکیب نامعتبر" }: { title?: string }) {
  return (
    <span
      title={title}
      className="null-cell inline-flex h-8 w-full items-center justify-center rounded-sm border border-border text-[10px]"
    >
      —
    </span>
  );
}
