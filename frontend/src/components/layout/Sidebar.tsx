import * as React from "react";
import { NavLink, Link, useLocation, useNavigate } from "react-router-dom";
import { LayoutDashboard, TrendingUp, Check, Sparkles, ArrowLeft } from "lucide-react";
import { WORKFLOW_STEPS, EQUITY_GROUP, PORTFOLIO_GROUP, ANALYSIS_TABS } from "@/config/models";
import { useWorkflow } from "@/store/workflow";
import { stepComplete } from "./Stepper";
import { cn } from "@/lib/utils";

interface SectionProps {
  title: string;
  compact: boolean;
  badge?: string;
  children: React.ReactNode;
}

/** Nav group with a small muted label and an optional count badge. */
function Section({ title, compact, badge, children }: SectionProps) {
  return (
    <div className="mb-5">
      {!compact && (
        <div className="mb-1.5 flex items-center justify-between px-3">
          <span className="text-[11px] font-semibold text-muted-foreground">{title}</span>
          {badge && (
            <span className="num rounded-full bg-surface-3 px-1.5 py-px text-[10px] text-muted-foreground">{badge}</span>
          )}
        </div>
      )}
      <nav className="space-y-0.5">{children}</nav>
    </div>
  );
}

const linkClass = ({ isActive }: { isActive: boolean }) =>
  cn(
    "flex min-h-9 items-center gap-2.5 rounded-lg px-3 py-2 text-sm transition-colors",
    isActive ? "sidebar-active" : "text-muted-foreground hover:bg-surface-3/60 hover:text-foreground",
  );

/**
 * Right-hand sidebar (RTL) in the workspace style: brand tile, grouped nav
 * (overview / guided workflow / standalone tools) and a contextual card at the
 * bottom. `compact` collapses to icons (tablet); on mobile it renders in a drawer.
 */
export function SidebarNav({ compact = false }: { compact?: boolean }) {
  const location = useLocation();
  const navigate = useNavigate();
  const completed = useWorkflow((s) => s.completed);
  const projections = useWorkflow((s) => s.projections);
  const loadSample = useWorkflow((s) => s.loadSample);
  // Step 4 hosts three analyses as tabs; the active tab comes from ?tab=.
  const currentTab = new URLSearchParams(location.search).get("tab") ?? "scenarios";

  const doneCount = WORKFLOW_STEPS.filter((s) => stepComplete(completed, s.id)).length;
  const nextStep = WORKFLOW_STEPS.find((s) => !stepComplete(completed, s.id));
  const hasWork = projections !== null;

  return (
    <div className="flex h-full flex-col">
      {/* Brand */}
      <Link to="/" className={cn("flex items-center gap-2.5 px-3 pb-4 pt-4", compact && "justify-center px-0")} aria-label="ارزش‌گذاری سهام — نمای کلی">
        <span className="brand-mark flex h-9 w-9 shrink-0 items-center justify-center rounded-lg">
          <TrendingUp className="h-[18px] w-[18px]" />
        </span>
        {!compact && (
          <span className="min-w-0">
            <span className="block truncate text-sm font-bold leading-tight">ارزش‌گذاری سهام</span>
            <span className="block text-[11px] text-muted-foreground">محیط یادگیری تحلیل مالی</span>
          </span>
        )}
      </Link>

      <div className="min-h-0 flex-1 overflow-y-auto px-3 pb-3">
        <Section title="فضای کاری" compact={compact}>
          <NavLink to="/" end className={linkClass} title="نمای کلی">
            <LayoutDashboard className="h-4 w-4 shrink-0" />
            {!compact && <span>نمای کلی</span>}
          </NavLink>
        </Section>

        <Section title="گردش کار ارزش‌گذاری" compact={compact} badge={`${doneCount}/6`}>
          {WORKFLOW_STEPS.map((s) => {
            const done = stepComplete(completed, s.id);
            return (
              <React.Fragment key={s.id}>
                <NavLink to={s.path} className={linkClass} title={s.label}>
                  <span
                    className={cn(
                      "num flex h-5 w-5 shrink-0 items-center justify-center rounded-full border text-[11px]",
                      done ? "border-positive/40 bg-positive/10 text-positive" : "border-border bg-surface text-muted-foreground",
                    )}
                  >
                    {done ? <Check className="h-3 w-3" /> : s.step}
                  </span>
                  {!compact && (
                    <span className="truncate">
                      {s.label}
                      {s.optional && <span className="mr-1 text-[10px] text-muted-foreground">(اختیاری)</span>}
                    </span>
                  )}
                </NavLink>
                {s.id === "analyses" && !compact && (
                  <div className="mr-5 space-y-0.5 border-r border-border pr-2">
                    {ANALYSIS_TABS.map((t) => (
                      <Link
                        key={t.id}
                        to={t.path}
                        title={t.label}
                        className={cn(
                          linkClass({ isActive: location.pathname === "/analyses" && currentTab === t.id }),
                          "min-h-8 py-1 text-xs",
                        )}
                      >
                        <span className="h-1 w-1 shrink-0 rounded-full bg-muted-foreground" />
                        <span className="truncate">{t.label}</span>
                      </Link>
                    ))}
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </Section>

        <Section title="مدل‌های سهام عادی" compact={compact} badge={String(EQUITY_GROUP.length)}>
          {EQUITY_GROUP.map((e) => (
            <NavLink key={e.id} to={e.path} className={linkClass} title={e.label}>
              <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-muted-foreground/60" />
              {!compact && <span className="truncate">{e.label}</span>}
            </NavLink>
          ))}
        </Section>

        <Section title="پرتفوی" compact={compact}>
          {PORTFOLIO_GROUP.map((p) => (
            <NavLink key={p.id} to={p.path} className={linkClass} title={p.label}>
              <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-muted-foreground/60" />
              {!compact && <span className="truncate">{p.label}</span>}
            </NavLink>
          ))}
        </Section>
      </div>

      {/* Contextual bottom card: sample CTA when empty, progress when underway. */}
      {!compact && (
        <div className="p-3 pt-0">
          <div className="rounded-[var(--radius)] bg-primary p-4 text-primary-foreground">
            {hasWork ? (
              <>
                <div className="text-sm font-semibold">گردش کار شما</div>
                <p className="mt-1 text-xs leading-5 opacity-70">
                  <span className="num">{doneCount}</span> از <span className="num">6</span> گام کامل شده است.
                </p>
                <div className="mt-2.5 h-1.5 overflow-hidden rounded-full bg-primary-foreground/20" role="progressbar" aria-valuenow={doneCount} aria-valuemin={0} aria-valuemax={6} aria-label="پیشرفت گردش کار">
                  <div className="h-full rounded-full bg-brand transition-all" style={{ width: `${(doneCount / 6) * 100}%` }} />
                </div>
                {nextStep && (
                  <button
                    type="button"
                    onClick={() => navigate(nextStep.path)}
                    className="mt-3 flex w-full items-center justify-center gap-1.5 rounded-lg bg-primary-foreground px-3 py-2 text-xs font-semibold text-primary transition-colors hover:bg-surface-2"
                  >
                    ادامه: {nextStep.label}
                    <ArrowLeft className="h-3.5 w-3.5" />
                  </button>
                )}
              </>
            ) : (
              <>
                <div className="text-sm font-semibold">شروع سریع با نمونه</div>
                <p className="mt-1 text-xs leading-5 opacity-70">
                  گردش کار را با اعداد مرجع آموزشی پر کنید و نتیجهٔ ارزش‌گذاری را ببینید.
                </p>
                <button
                  type="button"
                  onClick={() => { loadSample(); navigate("/dcf"); }}
                  className="mt-3 flex w-full items-center justify-center gap-1.5 rounded-lg bg-primary-foreground px-3 py-2 text-xs font-semibold text-primary transition-colors hover:bg-surface-2"
                >
                  <Sparkles className="h-3.5 w-3.5" />
                  بارگذاری دادهٔ نمونه
                </button>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}