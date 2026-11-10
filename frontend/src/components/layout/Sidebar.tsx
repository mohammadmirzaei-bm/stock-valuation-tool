import * as React from "react";
import { NavLink, Link, useLocation } from "react-router-dom";
import { Home as HomeIcon, GitBranch, Layers, PieChart } from "lucide-react";
import { WORKFLOW_STEPS, EQUITY_GROUP, PORTFOLIO_GROUP, ANALYSIS_TABS } from "@/config/models";
import { cn } from "@/lib/utils";

interface SectionProps {
  icon: React.ReactNode;
  title: string;
  compact: boolean;
  children: React.ReactNode;
}

function Section({ icon, title, compact, children }: SectionProps) {
  return (
    <div className="mb-6">
      <div className={cn("mb-2 flex items-center gap-2 px-3 text-xs font-semibold text-muted-foreground")}>
        <span className="shrink-0">{icon}</span>
        {!compact && <span className="truncate">{title}</span>}
      </div>
      <nav className="space-y-0.5">{children}</nav>
    </div>
  );
}

const linkClass = ({ isActive }: { isActive: boolean }) =>
  cn(
    "flex min-h-9 items-center gap-2.5 rounded-lg px-3 py-2 text-sm transition-colors",
    isActive ? "sidebar-active bg-primary/15 font-semibold text-primary" : "text-muted-foreground hover:bg-accent hover:text-foreground",
  );

/**
 * Right-hand sidebar (RTL) holding both the guided workflow and the standalone
 * tools. `compact` collapses to icons (tablet); on mobile it renders inside the
 * drawer.
 */
export function SidebarNav({ compact = false }: { compact?: boolean }) {
  const location = useLocation();
  // Step 4 hosts three analyses as tabs; the active tab comes from ?tab=.
  const currentTab = new URLSearchParams(location.search).get("tab") ?? "scenarios";
  return (
    <div className="flex h-full flex-col overflow-y-auto p-3">
      <Link to="/" className={cn(linkClass({ isActive: false }), "mb-2")} aria-label="خانه">
        <HomeIcon className="h-4 w-4 shrink-0" />
        {!compact && <span>خانه</span>}
      </Link>

      <Section icon={<GitBranch className="h-4 w-4" />} title="گردش کار" compact={compact}>
        {WORKFLOW_STEPS.map((s) => (
          <React.Fragment key={s.id}>
            <NavLink to={s.path} className={linkClass} title={s.label}>
              <span className="num flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-accent text-[11px]">
                {s.step}
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
        ))}
      </Section>

      <Section icon={<Layers className="h-4 w-4" />} title="مدل‌های سهام عادی" compact={compact}>
        {EQUITY_GROUP.map((e) => (
          <NavLink key={e.id} to={e.path} className={linkClass} title={e.label}>
            <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-muted-foreground" />
            {!compact && <span className="truncate">{e.label}</span>}
          </NavLink>
        ))}
      </Section>

      <Section icon={<PieChart className="h-4 w-4" />} title="پرتفوی" compact={compact}>
        {PORTFOLIO_GROUP.map((p) => (
          <NavLink key={p.id} to={p.path} className={linkClass} title={p.label}>
            <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-muted-foreground" />
            {!compact && <span className="truncate">{p.label}</span>}
          </NavLink>
        ))}
      </Section>
    </div>
  );
}
