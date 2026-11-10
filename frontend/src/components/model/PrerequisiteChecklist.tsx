import { useLocation, useNavigate } from "react-router-dom";
import { ArrowLeft, Crosshair, TriangleAlert } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { IncompleteState } from "./StateViews";
import { PREREQ_META, type PrereqKind } from "@/lib/prerequisites";

/**
 * Result-column prompt for the guided-workflow pages, replacing the generic
 * {@link IncompleteState}. It lists exactly what is missing:
 *  - `missing`: shared prerequisites, each with a button that jumps to the step
 *    providing it — or, when that step is the page you are already on, scrolls
 *    to and focuses the inline field instead of a misleading no-op navigation.
 *  - `local`: page-local blockers (peer count, range order, ...) as plain rows,
 *    since they are fixed right here and have no step to jump to.
 * Falls back to the generic prompt only when there is nothing to list.
 */
export function PrerequisiteChecklist({
  missing,
  local = [],
}: {
  missing: readonly PrereqKind[];
  local?: readonly string[];
}) {
  const navigate = useNavigate();
  const { pathname } = useLocation();

  if (missing.length === 0 && local.length === 0) return <IncompleteState />;

  const goToPrereq = (kind: PrereqKind) => {
    const meta = PREREQ_META[kind];
    if (meta.path === pathname) {
      const el = document.getElementById(meta.focusId);
      if (el) {
        el.scrollIntoView?.({ behavior: "smooth", block: "center" });
        el.focus?.();
        return;
      }
    }
    navigate(meta.path);
  };

  return (
    <Card className="p-4">
      <div className="mb-3 flex items-center gap-2 text-sm font-medium text-foreground">
        <TriangleAlert className="h-4 w-4 shrink-0 text-warning" aria-hidden />
        برای دیدن نتیجه، این پیش‌نیازها را کامل کنید
      </div>

      {missing.length > 0 && (
        <ul className="space-y-2">
          {missing.map((kind) => {
            const meta = PREREQ_META[kind];
            const here = meta.path === pathname;
            return (
              <li
                key={kind}
                className="flex items-center justify-between gap-2 rounded-md border border-border bg-muted px-3 py-2"
              >
                <span className="text-sm text-foreground">{meta.label}</span>
                <Button type="button" variant="outline" size="sm" onClick={() => goToPrereq(kind)}>
                  {here ? <Crosshair className="h-4 w-4" /> : <ArrowLeft className="h-4 w-4" />}
                  {here ? "رفتن به فیلد" : `گام ${meta.step}`}
                </Button>
              </li>
            );
          })}
        </ul>
      )}

      {local.length > 0 && (
        <ul className="mt-3 space-y-1.5">
          {local.map((msg) => (
            <li key={msg} className="flex items-start gap-2 text-xs text-muted-foreground">
              <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-current" aria-hidden />
              <span>{msg}</span>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
