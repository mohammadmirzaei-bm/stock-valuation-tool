import * as React from "react";
import { Outlet, useLocation } from "react-router-dom";
import { Menu, TrendingUp } from "lucide-react";
import { SidebarNav } from "./Sidebar";
import { Stepper } from "./Stepper";
import { GlobalSearch } from "./GlobalSearch";
import { DigitToggle } from "@/components/common/DigitToggle";
import { MoneyUnitToggle } from "@/components/common/MoneyUnitToggle";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { useMediaQuery } from "@/hooks/useMediaQuery";
import { Skeleton } from "@/components/common/Skeleton";
import { WORKFLOW_STEPS, ANALYSIS_TABS, EQUITY_META, PORTFOLIO_GROUP } from "@/config/models";

const WORKFLOW_PREFIXES = ["/forecast", "/wacc", "/dcf", "/analyses", "/multiples", "/football-field"];

/** Breadcrumb leaf for the current route (workspace · page). */
function usePageTitle(): string {
  const { pathname, search } = useLocation();
  if (pathname === "/") return "نمای کلی";
  const step = WORKFLOW_STEPS.find((s) => s.path === pathname);
  if (step) {
    if (step.id === "analyses") {
      const tab = new URLSearchParams(search).get("tab") ?? "scenarios";
      const t = ANALYSIS_TABS.find((a) => a.id === tab);
      return t ? `تحلیل‌ها · ${t.label}` : "تحلیل‌ها";
    }
    return step.label;
  }
  if (pathname.startsWith("/equity/")) {
    const id = pathname.slice("/equity/".length);
    return EQUITY_META[id]?.title ?? "مدل سهام";
  }
  const p = PORTFOLIO_GROUP.find((x) => x.path === pathname);
  if (p) return `پرتفوی · ${p.label}`;
  return "نمای کلی";
}

/** Shown while a lazily-loaded page chunk arrives; shell and stepper stay put. */
function PageFallback() {
  return (
    <div className="space-y-4" aria-busy="true" aria-label="در حال بارگذاری صفحه">
      <Skeleton className="h-8 w-52" />
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <Skeleton className="h-72 rounded-lg" />
        <Skeleton className="h-72 rounded-lg" />
      </div>
    </div>
  );
}

/** App shell: workspace header (breadcrumb + search + toggles), right-hand
 *  sidebar (rail / icons / drawer) and the page outlet. RTL mirror of the
 *  analytics-workspace layout. */
export function Layout() {
  const location = useLocation();
  const isMd = useMediaQuery("(min-width: 768px)");
  const isLg = useMediaQuery("(min-width: 1024px)");
  const inWorkflow = WORKFLOW_PREFIXES.some((p) => location.pathname.startsWith(p));
  const [drawerOpen, setDrawerOpen] = React.useState(false);
  const pageTitle = usePageTitle();

  return (
    <div className="flex min-h-screen bg-bg text-foreground">
      {/* Sidebar first in DOM = right side in RTL */}
      {isMd && (
        <aside
          className="app-sidebar sticky top-0 h-screen shrink-0 border-l border-border"
          style={{ width: isLg ? 264 : 68 }}
          aria-label="نوار کناری"
        >
          <SidebarNav compact={!isLg} />
        </aside>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="app-header sticky top-0 z-40 flex min-h-[64px] items-center gap-3 border-b border-border px-4 py-3 sm:px-6">
          {!isMd && (
            <Dialog open={drawerOpen} onOpenChange={setDrawerOpen}>
              <DialogTrigger asChild>
                <Button type="button" variant="ghost" size="icon" aria-label="منو">
                  <Menu className="h-5 w-5" />
                </Button>
              </DialogTrigger>
              <DialogContent className="right-0 left-auto top-0 h-full max-w-[17rem] -translate-y-0 translate-x-0 rounded-none border-l p-0">
                <DialogTitle className="sr-only">فهرست</DialogTitle>
                <DialogDescription className="sr-only">ناوبری گردش کار و ابزارهای ارزش‌گذاری</DialogDescription>
                <SidebarNav />
              </DialogContent>
            </Dialog>
          )}
          {!isMd && (
            <span className="brand-mark flex h-8 w-8 shrink-0 items-center justify-center rounded-lg">
              <TrendingUp className="h-4 w-4" />
            </span>
          )}

          <nav aria-label="موقعیت" className="hidden min-w-0 items-center gap-1.5 text-sm md:flex">
            <span className="shrink-0 text-muted-foreground">فضای کاری</span>
            <span className="shrink-0 text-muted-foreground/60" aria-hidden>·</span>
            <span className="truncate font-semibold text-foreground">{pageTitle}</span>
          </nav>

          <div className="flex min-w-0 flex-1 justify-center px-1 sm:px-4">
            <GlobalSearch />
          </div>

          <div className="flex shrink-0 items-center gap-1">
            <MoneyUnitToggle />
            <DigitToggle />
            <span
              className="mr-1 hidden h-8 w-8 items-center justify-center rounded-full bg-surface-3 text-xs font-bold text-foreground sm:flex"
              title="کاربر محلی — داده‌ها فقط روی همین دستگاه ذخیره می‌شوند"
              aria-label="کاربر محلی"
            >
              د
            </span>
          </div>
        </header>

        <main className="workspace-main min-w-0 flex-1">
          {/* Keyed by path so each page gets one short entrance; tab switches
              within /analyses (?tab=) do not replay it. */}
          <div key={location.pathname} className="page-enter">
            {inWorkflow && <Stepper />}
            <React.Suspense fallback={<PageFallback />}>
              <Outlet />
            </React.Suspense>
          </div>
        </main>
      </div>
    </div>
  );
}