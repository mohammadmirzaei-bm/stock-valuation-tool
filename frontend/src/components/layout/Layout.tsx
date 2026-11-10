import * as React from "react";
import { Outlet, useLocation } from "react-router-dom";
import { BarChart3, Menu } from "lucide-react";
import { SidebarNav } from "./Sidebar";
import { Stepper } from "./Stepper";
import { DigitToggle } from "@/components/common/DigitToggle";
import { MoneyUnitToggle } from "@/components/common/MoneyUnitToggle";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { useMediaQuery } from "@/hooks/useMediaQuery";
import { Skeleton } from "@/components/common/Skeleton";

const WORKFLOW_PREFIXES = ["/forecast", "/wacc", "/dcf", "/analyses", "/multiples", "/football-field"];

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

/** App shell: RTL header, right-hand sidebar (rail / icons / drawer) and outlet. */
export function Layout() {
  const location = useLocation();
  const isMd = useMediaQuery("(min-width: 768px)");
  const isLg = useMediaQuery("(min-width: 1024px)");
  const inWorkflow = WORKFLOW_PREFIXES.some((p) => location.pathname.startsWith(p));
  const [drawerOpen, setDrawerOpen] = React.useState(false);

  return (
    <div className="flex min-h-screen flex-col bg-bg text-foreground">
      <header className="app-header sticky top-0 z-40 flex min-h-[70px] items-center justify-between gap-3 border-b border-border px-4 py-3 sm:px-6">
        <div className="flex min-w-0 items-center gap-3">
          {!isMd && (
            <Dialog open={drawerOpen} onOpenChange={setDrawerOpen}>
              <DialogTrigger asChild>
                <Button type="button" variant="ghost" size="icon" aria-label="منو">
                  <Menu className="h-5 w-5" />
                </Button>
              </DialogTrigger>
              <DialogContent className="right-0 left-auto top-0 h-full max-w-[16rem] -translate-y-0 translate-x-0 rounded-none border-r">
                <DialogTitle className="sr-only">فهرست</DialogTitle>
                <DialogDescription className="sr-only">ناوبری گردش کار و ابزارهای ارزش‌گذاری</DialogDescription>
                <SidebarNav />
              </DialogContent>
            </Dialog>
          )}
          <div className="brand-mark hidden h-10 w-10 items-center justify-center rounded-xl sm:flex"><BarChart3 className="h-5 w-5" /></div>
          <div className="min-w-0"><h1 className="truncate text-sm font-bold sm:text-base">ابزار ارزش‌گذاری سهام</h1><p className="mt-0.5 hidden text-xs text-muted-foreground sm:block">تحلیل مالی، ساده و دقیق</p></div>
        </div>
        <div className="flex shrink-0 items-center gap-1">
          <MoneyUnitToggle />
          <DigitToggle />
        </div>
      </header>

      <div className="flex flex-1">
        {isMd && (
          <aside
            className="app-sidebar shrink-0 border-l border-border"
            style={{ width: isLg ? 256 : 64 }}
            aria-label="نوار کناری"
          >
            <SidebarNav compact={!isLg} />
          </aside>
        )}

        <main className="min-w-0 flex-1 p-4 sm:p-6 xl:p-8">
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
