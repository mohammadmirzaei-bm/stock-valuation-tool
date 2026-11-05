import * as React from "react";
import { AlertTriangle, TriangleAlert, Server, RotateCcw } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
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

/** First-load skeleton for the results column. */
export function ResultSkeleton() {
  return (
    <Card className="space-y-3 p-6">
      <div className="h-4 w-1/3 animate-pulse rounded bg-accent/60" />
      <div className="h-10 w-1/2 animate-pulse rounded bg-accent/60" />
      <div className="h-40 w-full animate-pulse rounded bg-accent/60" />
    </Card>
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
