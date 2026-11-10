import { useLocation, useNavigate } from "react-router-dom";
import { Check, CircleDashed, RotateCcw } from "lucide-react";
import { WORKFLOW_STEPS } from "@/config/models";
import { useWorkflow, type StepId } from "@/store/workflow";
import { Button } from "@/components/ui/button";
import { ConfirmDialog, RESET_DIALOG_COPY, useConfirmDialog } from "@/components/common/ConfirmDialog";
import { cn } from "@/lib/utils";

/** Step-4 "analyses" is complete when any of its three tabs has produced data. */
export function stepComplete(completed: Record<StepId, boolean>, id: string): boolean {
  if (id === "analyses") return completed.scenarios || completed.sensitivity || completed.reverse;
  // "football" is complete only from its own flag — never inferred from "multiples".
  return completed[id as StepId];
}

/** Top stepper showing workflow progress; steps 2 and 4 are optional shortcuts. */
export function Stepper() {
  const navigate = useNavigate();
  const location = useLocation();
  const completed = useWorkflow((s) => s.completed);
  const reset = useWorkflow((s) => s.reset);
  const confirm = useConfirmDialog();

  return (
    <div className="mb-4 flex flex-wrap items-center justify-between gap-2 rounded-[var(--radius)] border border-border bg-surface p-2">
      <ol className="flex flex-1 flex-wrap items-center gap-1">
        {WORKFLOW_STEPS.map((s, i) => {
          const done = stepComplete(completed, s.id);
          // aria-current marks where the student IS; completion is conveyed by
          // the check icon + sr-only text, never by aria-current.
          const current = location.pathname === s.path;
          return (
            <li key={s.id} className="flex items-center">
              <button
                type="button"
                onClick={() => navigate(s.path)}
                className={cn(
                  "flex items-center gap-1.5 rounded-md px-2 py-1 text-xs transition-colors hover:bg-accent",
                  current && "bg-accent font-semibold text-foreground",
                  done ? "text-positive" : current ? "text-foreground" : "text-muted-foreground",
                )}
                aria-current={current ? "step" : undefined}
              >
                <span className="num flex h-5 w-5 items-center justify-center rounded-full border border-current text-[11px]">
                  {s.step}
                </span>
                <span className="hidden sm:inline">{s.label}</span>
                <span className="sr-only">{done ? " — کامل شده" : " — شروع نشده"}</span>
                {done ? <Check className="h-3.5 w-3.5" /> : <CircleDashed className="h-3.5 w-3.5" />}
              </button>
              {i < WORKFLOW_STEPS.length - 1 && <span className="mx-1 text-border">←</span>}
            </li>
          );
        })}
      </ol>
      <Button type="button" variant="ghost" size="sm" onClick={confirm.request} title="بازنشانی گردش کار">
        <RotateCcw className="h-4 w-4" />
        <span className="hidden sm:inline">شروع دوباره گردش کار</span>
      </Button>
      <ConfirmDialog
        open={confirm.open}
        onOpenChange={confirm.onOpenChange}
        {...RESET_DIALOG_COPY}
        onConfirm={reset}
      />
    </div>
  );
}