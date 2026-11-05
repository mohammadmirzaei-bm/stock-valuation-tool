import { useNavigate } from "react-router-dom";
import { Check, CircleDashed, ChevronLeft } from "lucide-react";
import { WORKFLOW_STEPS } from "@/config/models";
import { useWorkflow } from "@/store/workflow";
import { cn } from "@/lib/utils";

function analysisComplete(c: Record<string, boolean>) {
  return c.scenarios || c.sensitivity || c.reverse;
}

/**
 * Six-step guided-workflow flow diagram (spec "Home screen"). On wide screens
 * the steps render as connected nodes (arrows point left in RTL); on narrow
 * screens they wrap into a grid. Each node carries a status chip — never color
 * alone: the icon + "کامل"/"شروع نشده" text carry the meaning.
 */
export function HomeDiagram() {
  const navigate = useNavigate();
  const completed = useWorkflow((s) => s.completed);

  return (
    <ol className="grid gap-3 sm:grid-cols-2 2xl:grid-cols-3">
      {WORKFLOW_STEPS.map((s) => {
        const done = s.id === "analyses" ? analysisComplete(completed) : completed[s.id as never];
        return (
          <li key={s.id} className="flex min-w-0 items-stretch gap-1">
            <button
              type="button"
              onClick={() => navigate(s.path)}
              className={cn(
                "workflow-card flex min-h-32 w-full flex-col gap-3 rounded-2xl border bg-surface p-4 text-right transition-all hover:border-primary/60",
                done ? "border-positive/40" : "border-border",
              )}
            >
              <div className="flex items-center justify-between">
                <span className="step-number num flex h-9 w-9 items-center justify-center rounded-xl text-sm font-semibold">{s.step}</span>
                <span
                  className={cn(
                    "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px]",
                    done ? "border-positive/40 bg-positive/10 text-positive" : "border-border bg-muted text-muted-foreground",
                  )}
                >
                  {done ? <Check className="h-3 w-3" /> : <CircleDashed className="h-3 w-3" />}
                  {done ? "کامل" : "شروع نشده"}
                </span>
              </div>
              <div className="mt-auto flex items-center justify-between text-sm font-semibold text-foreground">
                <span>
                {s.label}
                {s.optional && <span className="mr-1 text-[10px] font-normal text-muted-foreground">اختیاری</span>}
                </span>
                <ChevronLeft className="h-4 w-4 text-muted-foreground" aria-hidden />
              </div>
            </button>
          </li>
        );
      })}
    </ol>
  );
}
