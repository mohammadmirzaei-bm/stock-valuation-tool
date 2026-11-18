import { useNavigate } from "react-router-dom";
import { Check } from "lucide-react";
import { WORKFLOW_STEPS } from "@/config/models";
import { useWorkflow } from "@/store/workflow";
import { stepComplete } from "@/components/layout/Stepper";
import { cn } from "@/lib/utils";

/**
 * Workflow steps as a task list. Completion is earned by actually running each
 * step (read from the store), never toggled by hand — the checkbox reflects
 * real state and the row navigates to the step. The header count updates live.
 */
export function TasksCard() {
  const navigate = useNavigate();
  const completed = useWorkflow((s) => s.completed);
  const doneCount = WORKFLOW_STEPS.filter((s) => stepComplete(completed, s.id)).length;

  return (
    <section className="metric-card flex flex-col p-4" aria-label="وظایف گردش کار">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold">
          وظایف گردش کار <span className="num mr-1 text-xs font-normal text-muted-foreground">{doneCount} از ۶</span>
        </h3>
        <button type="button" onClick={() => navigate("/forecast")} className="text-xs text-muted-foreground transition-colors hover:text-brand">
          همه
        </button>
      </div>
      <ul className="space-y-1">
        {WORKFLOW_STEPS.map((s) => {
          const done = stepComplete(completed, s.id);
          return (
            <li key={s.id}>
              <button
                type="button"
                onClick={() => navigate(s.path)}
                title={done ? "کامل شده — برای بازبینی کلیک کنید" : "برای تکمیل، این گام را انجام دهید"}
                className="flex w-full items-center gap-2.5 rounded-lg px-2 py-2 text-right transition-colors hover:bg-surface-2"
              >
                <span
                  className={cn(
                    "flex shrink-0 items-center justify-center rounded border",
                    done ? "border-positive bg-positive text-primary-foreground" : "border-primary/25 bg-surface",
                  )}
                  style={{ width: 18, height: 18 }}
                  aria-hidden
                >
                  {done && <Check className="h-3 w-3" />}
                </span>
                <span className={cn("min-w-0 flex-1 truncate text-sm", done ? "text-muted-foreground line-through decoration-border" : "text-foreground")}>
                  {s.label}
                </span>
                {s.optional && <span className="shrink-0 text-[10px] text-muted-foreground">اختیاری</span>}
                <span className="num shrink-0 rounded-full bg-surface-2 px-1.5 py-px text-[10px] text-muted-foreground">{s.step}</span>
              </button>
            </li>
          );
        })}
      </ul>
      <div className="mt-3 border-t border-border pt-3">
        <div className="mb-1.5 flex items-center justify-between text-[11px] text-muted-foreground">
          <span>پیشرفت</span>
          <span className="num">{Math.round((doneCount / 6) * 100)}%</span>
        </div>
        <div className="h-1.5 overflow-hidden rounded-full bg-surface-2" role="progressbar" aria-valuenow={doneCount} aria-valuemin={0} aria-valuemax={6} aria-label="پیشرفت گردش کار">
          <div className="h-full rounded-full bg-brand transition-all" style={{ width: `${(doneCount / 6) * 100}%` }} />
        </div>
      </div>
    </section>
  );
}