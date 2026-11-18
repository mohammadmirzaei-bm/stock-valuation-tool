import { useNavigate } from "react-router-dom";
import { useWorkflow } from "@/store/workflow";
import { useFormat } from "@/hooks/useFormat";
import { cn } from "@/lib/utils";

/**
 * Live status of the shared company data (the workspace's "team status"
 * analog): each input row shows a ready/empty dot plus its current value, so
 * the student sees at a glance what is filled and what is still missing.
 */
export function DataStatusCard() {
  const navigate = useNavigate();
  const fmt = useFormat();
  const wf = useWorkflow();
  const bs = wf.balanceSheet;

  const rows: { label: string; value: string; ready: boolean; to: string }[] = [
    {
      label: "پیش‌بینی جریان نقدی",
      value: wf.projections ? `${fmt.number(wf.projections.length)} سال` : "وارد نشده",
      ready: !!wf.projections,
      to: "/forecast",
    },
    {
      label: "نرخ تنزیل (WACC)",
      value: wf.waccPercent !== null ? fmt.percent(wf.waccPercent) : "وارد نشده",
      ready: wf.waccPercent !== null && wf.waccPercent > 0,
      to: "/wacc",
    },
    {
      label: "تعداد سهام",
      value: bs.sharesOutstanding > 0 ? `${fmt.number(bs.sharesOutstanding)} سهم` : "وارد نشده",
      ready: bs.sharesOutstanding > 0,
      to: "/dcf",
    },
    {
      label: "قیمت بازار",
      value: wf.marketPrice !== null ? fmt.currency(wf.marketPrice) : "اختیاری — وارد نشده",
      ready: wf.marketPrice !== null,
      to: "/dcf",
    },
    {
      label: "بازه‌های زمین فوتبال",
      value: wf.ranges.length > 0 ? `${fmt.number(wf.ranges.length)} بازه` : "هنوز جمع نشده",
      ready: wf.ranges.length > 0,
      to: "/football-field",
    },
  ];

  return (
    <section className="metric-card flex flex-col p-4" aria-label="وضعیت داده‌ها">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold">وضعیت داده‌ها</h3>
        <button type="button" onClick={() => navigate("/dcf")} className="text-xs text-muted-foreground transition-colors hover:text-brand">
          مدیریت
        </button>
      </div>
      <ul className="space-y-0.5">
        {rows.map((r) => (
          <li key={r.label}>
            <button
              type="button"
              onClick={() => navigate(r.to)}
              className="flex w-full items-center gap-2.5 rounded-lg px-2 py-2 text-right transition-colors hover:bg-surface-2"
            >
              <span className={cn("h-2 w-2 shrink-0 rounded-full", r.ready ? "bg-positive" : "bg-muted-foreground/40")} aria-hidden />
              <span className="min-w-0 flex-1 truncate text-sm text-foreground">{r.label}</span>
              <span className={cn("num shrink-0 text-xs", r.ready ? "text-muted-foreground" : "text-muted-foreground/60")}>{r.value}</span>
            </button>
          </li>
        ))}
      </ul>
      <p className="mt-3 border-t border-border pt-3 text-[11px] leading-5 text-muted-foreground">
        داده‌ها به‌صورت محلی روی همین دستگاه ذخیره می‌شوند و با هر محاسبه به‌روز می‌مانند.
      </p>
    </section>
  );
}