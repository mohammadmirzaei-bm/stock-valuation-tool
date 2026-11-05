import * as React from "react";
import { Sparkles, Send } from "lucide-react";
import { SplitLayout } from "@/components/layout/SplitLayout";
import { NumberField } from "@/components/model/NumberField";
import { Segmented } from "@/components/common/Segmented";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ComboBarsLine } from "@/components/charts/Basic";
import { EmptyState, ErrorState, IncompleteState, ResultSkeleton } from "@/components/model/StateViews";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { postForecast } from "@/api/endpoints";
import type { ForecastRequest, ForecastResult } from "@/api/types";
import { FORECAST_SAMPLE, type DriverInput, type ForecastSample } from "@/lib/samples";
import { usePersistentState } from "@/hooks/usePersistentState";
import { useAutoQuery } from "@/hooks/useAutoQuery";
import { useWorkflow } from "@/store/workflow";
import { useFormat } from "@/hooks/useFormat";

type DriverKey = ForecastSample["drivers"] extends Record<infer K, DriverInput> ? K : never;
const DRIVER_KEYS: DriverKey[] = [
  "revenue_growth",
  "ebitda_margin",
  "da_pct_revenue",
  "capex_pct_revenue",
  "nwc_pct_incremental_revenue",
];
const DRIVER_META: Record<DriverKey, { label: string; info: string; neg?: boolean }> = {
  revenue_growth: { label: "رشد درآمد", info: "رشد درآمد هر سال (٪). از ۱۰۰−٪ تا ۲۰۰٪.", neg: true },
  ebitda_margin: { label: "حاشیه EBITDA", info: "حاشیه سود عملیاتی (٪). ۰ تا ۱۰۰." },
  da_pct_revenue: { label: "استهلاک / درآمد", info: "نسبت استهلاک به درآمد (٪). ۰ تا ۱۰۰." },
  capex_pct_revenue: { label: "Capex / درآمد", info: "نسبت مخارج سرمایه‌ای به درآمد (٪). خروج نقد مثبت." },
  nwc_pct_incremental_revenue: { label: "NWC / درآمد افزایشی", info: "سرمایه در گردش نسبت به درآمد افزایشی (٪)." },
};

function makeSample(): ForecastSample {
  return JSON.parse(JSON.stringify(FORECAST_SAMPLE));
}

function syncYears(d: DriverInput, years: number): DriverInput {
  if (d.mode === "all") return { ...d, perYear: Array.from({ length: years }, () => d.value) };
  const perYear = Array.from({ length: years }, (_, i) => d.perYear[i] ?? d.perYear[d.perYear.length - 1] ?? 0);
  return { ...d, perYear };
}

export function ForecastPage() {
  const fmt = useFormat();
  const sendToDcf = useWorkflow((s) => s.sendToDcf);
  const [form, setForm] = usePersistentState<ForecastSample>("forecast", makeSample());
  const [sent, setSent] = React.useState(false);

  const setYears = (years: number) =>
    setForm((f) => ({ ...f, years, drivers: Object.fromEntries(Object.entries(f.drivers).map(([k, d]) => [k, syncYears(d as DriverInput, years)])) }) as ForecastSample);

  const setDriver = (key: DriverKey, d: DriverInput) => setForm((f) => ({ ...f, drivers: { ...f.drivers, [key]: d } }));

  const driverOk = (d: DriverInput) =>
    d.mode === "all" ? Number.isFinite(d.value) : d.perYear.length === form.years && d.perYear.every((x) => Number.isFinite(x));

  const ready =
    Number.isFinite(form.base_revenue) &&
    form.base_revenue > 0 &&
    form.years >= 1 &&
    form.years <= 50 &&
    DRIVER_KEYS.every((k) => driverOk(form.drivers[k])) &&
    (!form.normalize_terminal_year || (Number.isFinite(form.terminal_growth) && form.terminal_growth >= 0));

  const body: ForecastRequest | null = ready
    ? {
        base_revenue: form.base_revenue,
        years: form.years,
        revenue_growth: wireDriver(form.drivers.revenue_growth),
        ebitda_margin: wireDriver(form.drivers.ebitda_margin),
        da_pct_revenue: wireDriver(form.drivers.da_pct_revenue),
        capex_pct_revenue: wireDriver(form.drivers.capex_pct_revenue),
        nwc_pct_incremental_revenue: wireDriver(form.drivers.nwc_pct_incremental_revenue),
        normalize_terminal_year: form.normalize_terminal_year,
        ...(form.normalize_terminal_year ? { terminal_growth: form.terminal_growth / 100 } : {}),
      }
    : null;

  const query = useAutoQuery<ForecastResult>("forecast", body, postForecast, ready);
  const res = query.data;

  return (
    <SplitLayout
      title="گام ۱: پیش‌بینی جریان نقدی"
      formula="Revenueₜ = Revenueₜ₋₁ × (1 + g) ;  FCFF = EBIT(1−t) + D&A − Capex − ΔNWC"
      whenSuitable="محرک‌های درآمد و حاشیه را وارد کنید تا سطرها سال‌به‌سال ساخته و برای DCF آماده شوند."
      howToRead="درآمد سال‌به‌سال از رشد قبلی می‌آید. Capex خروج نقد مثبت و ΔNWC هنگام رشد مثبتِ سرمایه در گردش، مثبت است."
      input={
        <>
          <Button type="button" variant="secondary" size="sm" onClick={() => { setForm(makeSample()); setSent(false); }} className="w-full">
            <Sparkles className="h-4 w-4" />
            مقادیر نمونه
          </Button>
          <NumberField label="درآمد پایه" suffix="ریال" value={form.base_revenue} onChange={(v) => setForm((f) => ({ ...f, base_revenue: v ?? 0 }))} info="آخرین درآمد تاریخی (مثبت)." min={0} />
          <div className="grid gap-1.5">
            <Label>
              تعداد سال‌ها: <span className="num">{fmt.number(form.years)}</span>
            </Label>
            <Slider min={1} max={50} step={1} value={[form.years]} onValueChange={([y]) => setYears(y)} aria-label="تعداد سال‌ها" />
          </div>

          {DRIVER_KEYS.map((key) => {
            const d = form.drivers[key];
            const meta = DRIVER_META[key];
            return (
              <div key={key} className="space-y-2 rounded-md border border-border bg-bg/50 p-2">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-sm text-foreground">{meta.label}</span>
                  <Segmented
                    ariaLabel={meta.label}
                    value={d.mode}
                    onChange={(mode) => setDriver(key, syncYears({ ...d, mode }, form.years))}
                    options={[
                      { value: "all", label: "همه سال‌ها یکسان" },
                      { value: "year", label: "سال‌به‌سال" },
                    ]}
                  />
                </div>
                {d.mode === "all" ? (
                  <NumberField label="" suffix="٪" value={d.value} onChange={(v) => setDriver(key, syncYears({ ...d, value: v ?? 0 }, form.years))} info={meta.info} min={meta.neg ? -100 : 0} max={meta.neg ? 200 : 100} />
                ) : (
                  <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                    {d.perYear.map((val, i) => (
                      <NumberField key={i} label={`سال ${i + 1}`} suffix="٪" value={val} onChange={(v) => { const py = [...d.perYear]; py[i] = v ?? 0; setDriver(key, { ...d, perYear: py }); }} min={meta.neg ? -100 : 0} max={meta.neg ? 200 : 100} compact />
                    ))}
                  </div>
                )}
              </div>
            );
          })}

          <div className="flex items-center justify-between gap-2 rounded-md border border-border bg-bg/50 p-2">
            <Label htmlFor="norm" className="text-foreground">نرمال‌سازی سال پایانی</Label>
            <Switch id="norm" checked={form.normalize_terminal_year} onCheckedChange={(c) => setForm((f) => ({ ...f, normalize_terminal_year: c }))} />
          </div>
          {form.normalize_terminal_year && (
            <NumberField label="نرخ رشد پایانی" suffix="٪" value={form.terminal_growth} onChange={(v) => setForm((f) => ({ ...f, terminal_growth: v ?? 0 }))} info="ارزش انتهایی از آخرین سال صریح ساخته می‌شود؛ آن سال باید پایدار باشد (Capex برابر استهلاک)." min={0} max={200} />
          )}
        </>
      }
      results={
        !ready ? (
          <IncompleteState />
        ) : query.isPending && !res ? (
          <ResultSkeleton />
        ) : query.error ? (
          <div className="space-y-3">
            <ErrorState error={query.error} />
          </div>
        ) : res ? (
          <div className={query.isFetching ? "is-updating space-y-4" : "space-y-4"}>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>سال</TableHead>
                    <TableHead>درآمد</TableHead>
                    <TableHead>رشد ٪</TableHead>
                    <TableHead>EBITDA</TableHead>
                    <TableHead>حاشیه ٪</TableHead>
                    <TableHead>EBIT</TableHead>
                    <TableHead>استهلاک</TableHead>
                    <TableHead>Capex</TableHead>
                    <TableHead>ΔNWC</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {res.rows.map((r) => (
                    <TableRow key={r.year}>
                      <TableCell className="num">{r.year}</TableCell>
                      <TableCell className="num">{fmt.number(r.revenue)}</TableCell>
                      <TableCell className="num">{fmt.percent(r.growth_percent)}</TableCell>
                      <TableCell className="num">{fmt.number(r.ebitda)}</TableCell>
                      <TableCell className="num">{fmt.percent(r.ebitda_margin_percent)}</TableCell>
                      <TableCell className="num">{fmt.number(r.ebit)}</TableCell>
                      <TableCell className="num">{fmt.number(r.depreciation)}</TableCell>
                      <TableCell className="num">{fmt.number(r.capex)}</TableCell>
                      <TableCell className="num">{fmt.number(r.delta_nwc)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
            <ComboBarsLine
              categories={res.rows.map((r) => String(r.year))}
              bars={res.revenues}
              line={res.rows.map((r) => r.ebitda_margin_percent)}
              barName="درآمد"
              lineName="حاشیه EBITDA ٪"
              summary="نمودار درآمد سالانه با خط حاشیه سود عملیاتی."
            />
            <Card className="p-3">
              <Button type="button" onClick={() => { sendToDcf(res.projections); setSent(true); }}>
                <Send className="h-4 w-4" />
                ارسال به DCF
              </Button>
              {sent && <span className="mr-3 text-xs text-positive">سطرها به گام ۳ ارسال شد ✓</span>}
            </Card>
          </div>
        ) : (
          <EmptyState formula="Revenueₜ = Revenueₜ₋₁ × (1 + g)" whenSuitable="محرک‌ها را پر کنید." onLoadSample={() => setForm(makeSample())} />
        )
      }
    />
  );
}

function wireDriver(d: DriverInput): number | number[] {
  return d.mode === "all" ? d.value / 100 : d.perYear.map((x) => x / 100);
}
