import * as React from "react";
import { Link } from "react-router-dom";
import { Check, ChevronDown, ChevronLeft, CircleDashed } from "lucide-react";
import { ANALYSIS_TABS, WORKFLOW_STEPS } from "@/config/models";
import { useWorkflow, type StepId } from "@/store/workflow";
import { cn } from "@/lib/utils";

function analysisComplete(c: Record<string, boolean>) {
  return c.scenarios || c.sensitivity || c.reverse;
}

/** Status chip: icon + text, never color alone (accessibility). */
function StatusChip({ done }: { done: boolean }) {
  return (
    <span
      className={cn(
        "inline-flex shrink-0 items-center gap-1 rounded-full border px-2 py-0.5 text-[11px]",
        done ? "border-positive/40 bg-positive/10 text-positive" : "border-border bg-muted text-muted-foreground",
      )}
    >
      {done ? <Check className="h-3 w-3" /> : <CircleDashed className="h-3 w-3" />}
      {done ? "کامل" : "شروع نشده"}
    </span>
  );
}

/**
 * Six-step guided-workflow flow (spec "Home screen"). On wide screens the steps
 * are connected nodes in one row — arrows point left in RTL, from each step to
 * the next — and step 4 fans out into its three sub-analyses as small branches.
 * On narrow screens the same nodes stack into a vertical list with down arrows.
 */
export function HomeDiagram() {
  const completed = useWorkflow((s) => s.completed);

  return (
    <ol className="flex flex-col gap-1 lg:flex-row lg:items-start lg:gap-0">
      {WORKFLOW_STEPS.map((s, i) => {
        const done = s.id === "analyses" ? analysisComplete(completed) : completed[s.id as StepId];
        return (
          <React.Fragment key={s.id}>
            <li className="flex min-w-0 flex-1 flex-col">
              <Link
                to={s.path}
                className={cn(
                  "card-surface flex min-h-[84px] w-full flex-col justify-between gap-2 p-3 text-right transition-colors hover:border-primary",
                  done && "border-positive/50",
                )}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="step-number num flex h-7 w-7 items-center justify-center rounded-lg text-xs font-semibold">
                    {s.step}
                  </span>
                  <StatusChip done={done} />
                </div>
                <span className="text-sm font-semibold text-foreground">
                  {s.label}
                  {s.optional && <span className="mr-1 text-[10px] font-normal text-muted-foreground">اختیاری</span>}
                </span>
              </Link>

              {s.id === "analyses" && (
                <div className="mt-2 space-y-1 border-r-2 border-border pr-2">
                  {ANALYSIS_TABS.map((t) => {
                    const tDone = completed[t.id as StepId];
                    return (
                      <Link
                        key={t.id}
                        to={t.path}
                        className="flex w-full items-center justify-between gap-2 rounded-md border border-border bg-bg px-2 py-1 text-[11px] transition-colors hover:border-primary"
                      >
                        <span className="truncate text-muted-foreground">{t.label}</span>
                        {tDone ? (
                          <Check className="h-3 w-3 shrink-0 text-positive" />
                        ) : (
                          <CircleDashed className="h-3 w-3 shrink-0 text-muted-foreground" />
                        )}
                      </Link>
                    );
                  })}
                </div>
              )}
            </li>

            {i < WORKFLOW_STEPS.length - 1 && (
              <li aria-hidden="true" className="flex items-center justify-center py-0.5 lg:mt-8 lg:px-1 lg:py-0">
                <ChevronDown className="h-5 w-5 text-muted-foreground lg:hidden" />
                <ChevronLeft className="hidden h-5 w-5 text-muted-foreground lg:block" />
              </li>
            )}
          </React.Fragment>
        );
      })}
    </ol>
  );
}
