import * as React from "react";
import { Copy, Send, Plus, Trash2 } from "lucide-react";
import { NumberField } from "@/components/model/NumberField";
import { Hero, ComponentCards } from "@/components/model/ResultParts";
import { Chip } from "@/components/common/Chip";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ProjectionsEditor } from "@/components/model/ProjectionsEditor";
import { Heatmap } from "@/components/charts/Heatmap";
import { BarSeriesChart } from "@/components/charts/Basic";
import { ErrorState, IncompleteState, ResultSkeleton } from "@/components/model/StateViews";
import { postDcfScenarios, postDcfSensitivity, postReverseDcf } from "@/api/endpoints";
import type {
  DcfScenarioRequest, DcfScenarioResult, DcfSensitivityRequest, DcfSensitivityResult,
  ReverseDcfRequest, ReverseDcfResult, CashFlowProjectionInput,
} from "@/api/types";
import { useAutoQuery } from "@/hooks/useAutoQuery";
import { usePersistentState } from "@/hooks/usePersistentState";
import { useWorkflow, type FootballRange } from "@/store/workflow";
import { useFormat } from "@/hooks/useFormat";
import { MIN_SPREAD_PP } from "@/lib/validation";
import { chartColors } from "@/components/charts/theme";

function projectionsValid(rows: CashFlowProjectionInput[]) {
  return rows.length >= 1 && rows.length <= 50;
}

/** Sum of scenario probabilities in percent. */
function probTotal(pcts: number[]): number {
  return pcts.reduce((a, b) => a + (b || 0), 0);
}

function ScenarioTab() {
  const fmt = useFormat();
  const wf = useWorkflow();
  const rows = wf.projections ?? [];
  const bs = wf.balanceSheet;

  const [scenarios, setScenarios] = usePersistentState<
    { name: string; probability: number; wacc: number; terminal_growth: number; rows: CashFlowProjectionInput[] | null }[]
  >("analyses-scenarios", [
    { name: "bear", probability: 25, wacc: 11, terminal_growth: 2, rows: null },
    { name: "base", probability: 50, wacc: 9, terminal_growth: 3, rows: null },
    { name: "bull", probability: 25, wacc: 8.5, terminal_growth: 3.5, rows: null },
  ]);

  const total = probTotal(scenarios.map((s) => s.probability));
  const unique = new Set(scenarios.map((s) => s.name.trim())).size === scenarios.length;
  const allRows = scenarios.map((s) => s.rows ?? rows);
  const ready =
    scenarios.length >= 2 && scenarios.length <= 5 &&
    Math.abs(total - 100) <= 0.0001 && unique &&
    allRows.every(projectionsValid) &&
    scenarios.every((s) => s.wacc > 0 && s.wacc - s.terminal_growth >= MIN_SPREAD_PP) &&
    bs.sharesOutstanding > 0;

  const body: DcfScenarioRequest | null = ready
    ? {
        scenarios: scenarios.map((s) => ({
          name: s.name.trim(),
          probability: s.probability / 100,
          wacc: s.wacc / 100,
          terminal_growth: s.terminal_growth / 100,
          projections: (s.rows ?? rows).map((r) => ({ ...r })),
        })),
        shares_outstanding: bs.sharesOutstanding,
        tax_rate: bs.taxRate / 100,
        cash: bs.cash,
        debt: bs.debt,
        minority_interest: bs.minorityInterest,
        preferred_equity: bs.preferredEquity,
        market_price: wf.marketPrice ?? undefined,
      }
    : null;

  const query = useAutoQuery<DcfScenarioResult>("dcf-scenarios", body, postDcfScenarios, ready);
  const res = query.data;

  const sendRange = () => {
    if (!res) return;
    const range: FootballRange = { method: "Scenarios", low: res.min_value_per_share, mid: res.expected_value_per_share, high: res.max_value_per_share, source: "از سناریوها" };
    wf.upsertRange(range);
    wf.completeStep("scenarios");
  };

  const c = chartColors();
  return (
    <>
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">سناریوها (۲ تا ۵)</span>
          <span className={`num text-sm ${Math.abs(total - 100) <= 0.0001 ? "text-positive" : "text-negative"}`}>
            مجموع: {fmt.percent(total)} {Math.abs(total - 100) <= 0.0001 ? "✓" : "✗"}
          </span>
        </div>
        {scenarios.map((s, i) => (
          <Card key={i} className="space-y-3 p-3">
            <div className="flex items-center justify-between">
              <ScenarioName value={s.name} onChange={(v) => setScenarios((arr) => arr.map((x, idx) => (idx === i ? { ...x, name: v } : x)))} />
              <div className="flex items-center gap-2">
                <Chip tone={s.rows ? "neutral" : "store"}>{s.rows ? "سطر دستی" : "از پیش‌بینی"}</Chip>
                <Button type="button" variant="ghost" size="icon" aria-label="کپی از پیش‌بینی" title="کپی از پیش‌بینی" onClick={() => setScenarios((arr) => arr.map((x, idx) => (idx === i ? { ...x, rows: [...rows] } : x)))} disabled={!rows.length}>
                  <Copy className="h-3.5 w-3.5" />
                </Button>
                <Button type="button" variant="ghost" size="icon" aria-label="حذف سناریو" disabled={scenarios.length <= 2} onClick={() => setScenarios((arr) => arr.filter((_, idx) => idx !== i))}>
                  <Trash2 className="h-3.5 w-3.5" />
                </Button>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              <NumberField label="احتمال" suffix="٪" value={s.probability} onChange={(v) => setScenarios((arr) => arr.map((x, idx) => (idx === i ? { ...x, probability: v ?? 0 } : x)))} min={0} max={100} />
              <NumberField label="WACC" suffix="٪" value={s.wacc} onChange={(v) => setScenarios((arr) => arr.map((x, idx) => (idx === i ? { ...x, wacc: v ?? 0 } : x)))} min={0} />
              <NumberField label="رشد پایانی" suffix="٪" value={s.terminal_growth} onChange={(v) => setScenarios((arr) => arr.map((x, idx) => (idx === i ? { ...x, terminal_growth: v ?? 0 } : x)))} min={0} max={200} />
            </div>
            {s.rows && <ProjectionsEditor rows={s.rows} onChange={(r) => setScenarios((arr) => arr.map((x, idx) => (idx === i ? { ...x, rows: r } : x)))} />}
          </Card>
        ))}
        <Button type="button" variant="outline" size="sm" disabled={scenarios.length >= 5} onClick={() => setScenarios((arr) => [...arr, { name: `سناریو${arr.length + 1}`, probability: 0, wacc: 9, terminal_growth: 3, rows: null }])}>
          <Plus className="h-4 w-4" /> افزودن سناریو
        </Button>
      </div>

      <div className="space-y-4">
        {!ready ? (
          <IncompleteState />
        ) : query.isPending && !res ? (
          <ResultSkeleton />
        ) : query.error ? (
          <ErrorState error={query.error} />
        ) : res ? (
          <div className={query.isFetching ? "is-updating space-y-4" : "space-y-4"}>
            <Hero label="ارزش مورد انتظار هر سهم" value={fmt.number(res.expected_value_per_share)} />
            <ComponentCards
              items={[
                { label: "انحراف معیار", value: fmt.number(res.std_dev_value_per_share) },
                { label: "بدترین", value: res.worst_scenario },
                { label: "بهترین", value: res.best_scenario },
                ...(res.expected_upside_percent !== undefined ? [{ label: "بازده مورد انتظار", value: fmt.signedPercent(res.expected_upside_percent) }] : []),
                ...(res.probability_of_upside_percent !== undefined ? [{ label: "احتمال بازده مثبت", value: fmt.percent(res.probability_of_upside_percent) }] : []),
              ]}
            />
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    {["سناریو", "ارزش هر سهم", "احتمال", "ارزش وزنی", "بازده ٪"].map((h) => <TableHead key={h}>{h}</TableHead>)}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {res.scenarios.map((s) => (
                    <TableRow key={s.name}>
                      <TableCell>{s.name}</TableCell>
                      <TableCell className="num">{fmt.number(s.value_per_share)}</TableCell>
                      <TableCell className="num">{fmt.percent(s.probability_percent)}</TableCell>
                      <TableCell className="num">{fmt.number(s.weighted_value_per_share)}</TableCell>
                      <TableCell className="num">{fmt.signedPercent(s.upside_percent)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
            <BarSeriesChart
              categories={res.scenarios.map((s) => `${s.name} (${fmt.percent(s.probability_percent)})`)}
              series={[{ name: "ارزش هر سهم", data: res.scenarios.map((s) => s.value_per_share), color: c.primary }]}
              valueLabel={(v) => fmt.number(v as number)}
              summary="ستون ارزش هر سهم برای هر سناریو با درصد احتمال."
            />
            <Button type="button" size="sm" onClick={sendRange}>
              <Send className="h-4 w-4" /> ارسال بازه به زمین فوتبال
            </Button>
          </div>
        ) : null}
      </div>
    </>
  );
}

function ScenarioName({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return (
    <input
      value={value}
      onChange={(e) => onChange(e.target.value)}
      aria-label="نام سناریو"
      className="h-9 w-full rounded-md border border-input bg-bg px-3 text-sm"
    />
  );
}

function SensitivityTab() {
  const fmt = useFormat();
  const wf = useWorkflow();
  const rows = wf.projections ?? [];
  const bs = wf.balanceSheet;
  const [tg, setTg] = usePersistentState<number>("analyses-sens-growth", 3);
  const [waccStep, setWaccStep] = usePersistentState<number>("analyses-sens-waccstep", 1);
  const [growthStep, setGrowthStep] = usePersistentState<number>("analyses-sens-growthstep", 0.5);
  const [points, setPoints] = usePersistentState<number>("analyses-sens-points", 5);
  const [view, setView] = React.useState<"vps" | "ev">("vps");

  const wacc = wf.waccPercent ?? undefined;
  const odd = (n: number) => n % 2 === 1 && n >= 3 && n <= 11;
  const ready =
    rows.length >= 1 && wacc !== undefined && wacc > 0 && wacc - tg >= MIN_SPREAD_PP &&
    waccStep > 0 && growthStep > 0 && odd(points) && bs.sharesOutstanding > 0;

  const body: DcfSensitivityRequest | null = ready
    ? {
        projections: rows.map((r) => ({ ...r })),
        wacc: (wacc as number) / 100,
        terminal_growth: tg / 100,
        shares_outstanding: bs.sharesOutstanding,
        tax_rate: bs.taxRate / 100,
        cash: bs.cash, debt: bs.debt, minority_interest: bs.minorityInterest, preferred_equity: bs.preferredEquity,
        wacc_step: waccStep / 100, growth_step: growthStep / 100, wacc_points: points, growth_points: points,
      }
    : null;

  const query = useAutoQuery<DcfSensitivityResult>("dcf-sensitivity", body, postDcfSensitivity, ready);
  const res = query.data;

  const sendRange = () => {
    if (!res) return;
    const flat = res.value_per_share.flat().filter((v): v is number => v !== null && Number.isFinite(v));
    if (!flat.length) return;
    wf.upsertRange({ method: "Sensitivity", low: Math.min(...flat), mid: res.base_value_per_share, high: Math.max(...flat), source: "از حساسیت" });
    wf.completeStep("sensitivity");
  };

  const matrix = res ? (view === "vps" ? res.value_per_share : res.enterprise_value) : [];
  return (
    <>
      <div className="space-y-3">
        {!wf.projections && <div className="text-sm text-warning">ابتدا پیش‌بینی گام ۱ را بفرستید.</div>}
        <Chip tone={wf.waccDetached ? "neutral" : "store"}>WACC {wf.waccDetached ? "(دستی)" : "از گام ۲ ✓"}: {wacc !== undefined ? fmt.percent(wacc) : "—"}</Chip>
        <div className="grid grid-cols-2 gap-3">
          <NumberField label="رشد پایانی پایه" suffix="٪" value={tg} onChange={(v) => setTg(v ?? 0)} min={0} max={200} />
          <NumberField label="گام WACC" suffix="٪" value={waccStep} onChange={(v) => setWaccStep(v ?? 0)} min={0} />
          <NumberField label="گام رشد" suffix="٪" value={growthStep} onChange={(v) => setGrowthStep(v ?? 0)} min={0} />
          <NumberField label="نقاط هر محور" value={points} onChange={(v) => setPoints(v ?? 5)} min={3} max={11} step={2} info="تعداد نقاط فرد: ۳ تا ۱۱." />
        </div>
      </div>

      <div className="space-y-4">
        {!ready ? (
          <IncompleteState />
        ) : query.isPending && !res ? (
          <ResultSkeleton />
        ) : query.error ? (
          <ErrorState error={query.error} />
        ) : res ? (
          <div className={query.isFetching ? "is-updating space-y-4" : "space-y-4"}>
            <div className="flex items-center justify-between">
              <Tabs value={view} onValueChange={(v) => setView(v as "vps" | "ev")}>
                <TabsList>
                  <TabsTrigger value="vps">ارزش هر سهم</TabsTrigger>
                  <TabsTrigger value="ev">ارزش بنگاه</TabsTrigger>
                </TabsList>
              </Tabs>
              <span className="num text-xs text-muted-foreground">{res.valid_cells} از {res.total_cells} سلول معتبر</span>
            </div>
            <Heatmap
              rowLabels={res.wacc_values_percent.map((x) => fmt.percent(x))}
              colLabels={res.growth_values_percent.map((x) => fmt.percent(x))}
              matrix={matrix}
              baseRow={res.base_row}
              baseCol={res.base_col}
              baseValue={view === "vps" ? res.base_value_per_share : res.base_enterprise_value}
              format={(v) => fmt.number(v)}
            />
            <Button type="button" size="sm" onClick={sendRange}>
              <Send className="h-4 w-4" /> ارسال بازه به زمین فوتبال
            </Button>
          </div>
        ) : null}
      </div>
    </>
  );
}

function ReverseTab() {
  const fmt = useFormat();
  const wf = useWorkflow();
  const rows = wf.projections ?? [];
  const bs = wf.balanceSheet;
  const wacc = wf.waccPercent ?? undefined;
  const [ownGrowth, setOwnGrowth] = usePersistentState<number | undefined>("analyses-reverse-own", undefined);

  const ready = rows.length >= 1 && wacc !== undefined && wacc > 0 && bs.sharesOutstanding > 0 && (wf.marketPrice ?? 0) > 0;

  const body: ReverseDcfRequest | null = ready
    ? {
        projections: rows.map((r) => ({ ...r })),
        wacc: (wacc as number) / 100,
        shares_outstanding: bs.sharesOutstanding,
        tax_rate: bs.taxRate / 100,
        market_price: wf.marketPrice as number,
        cash: bs.cash, debt: bs.debt, minority_interest: bs.minorityInterest, preferred_equity: bs.preferredEquity,
        ...(ownGrowth !== undefined ? { terminal_growth: ownGrowth / 100 } : {}),
      }
    : null;

  const query = useAutoQuery<ReverseDcfResult>("reverse-dcf", body, postReverseDcf, ready);
  const res = query.data;

  return (
    <>
      <div className="space-y-3">
        {!wf.projections && <div className="text-sm text-warning">ابتدا پیش‌بینی گام ۱ را بفرستید.</div>}
        <div className="text-xs text-muted-foreground">قیمت بازار: <span className="num">{wf.marketPrice !== null ? fmt.number(wf.marketPrice) : "—"}</span> (از گام ۳/مشترک)</div>
        <NumberField label="رشد پایانی نظر خودتان (اختیاری)" suffix="٪" value={ownGrowth} onChange={(v) => setOwnGrowth(v)} min={0} max={200} info="فقط برای محاسبهٔ اختلاف با رشد تلویحی." />
      </div>

      <div className="space-y-4">
        {!ready ? (
          <IncompleteState />
        ) : query.isPending && !res ? (
          <ResultSkeleton />
        ) : query.error ? (
          <ErrorState error={query.error} />
        ) : res ? (
          <div className={query.isFetching ? "is-updating space-y-4" : "space-y-4"}>
            {res.status === "solved" ? (
              <>
                <p className="text-lg font-medium text-foreground">{res.message}</p>
                <GrowthRangeBar min={res.search_min_growth} max={res.search_max_growth} implied={res.implied_growth ?? null} own={ownGrowth !== undefined ? ownGrowth / 100 : null} gap={res.growth_gap ?? null} />
                <ComponentCards
                  items={[
                    { label: "ارزش بنگاه", value: fmt.number(res.enterprise_value) },
                    { label: "ارزش سهام", value: fmt.number(res.equity_value) },
                    { label: "سهم ارزش انتهایی", value: fmt.percent(res.terminal_value_share_percent) },
                  ]}
                />
              </>
            ) : (
              <Card className="border-warning/50 bg-warning/10 p-4">
                <div className="mb-2 font-semibold text-warning">خارج از بازهٔ جستجو</div>
                <p className="text-sm text-foreground">{res.message}</p>
                <div className="mt-3 grid grid-cols-2 gap-2 text-sm">
                  <div>ارزش در کرانهٔ پایین: <span className="num">{fmt.number(res.value_per_share_at_min_growth)}</span></div>
                  <div>ارزش در کرانهٔ بالا: <span className="num">{fmt.number(res.value_per_share_at_max_growth)}</span></div>
                </div>
              </Card>
            )}
          </div>
        ) : null}
      </div>
    </>
  );
}

function GrowthRangeBar({ min, max, implied, own, gap }: { min: number; max: number; implied: number | null; own: number | null; gap: number | null }) {
  const fmt = useFormat();
  const span = max - min || 1;
  const pos = (v: number) => `${Math.max(0, Math.min(1, (v - min) / span)) * 100}%`;
  return (
    <Card className="p-4">
      <div className="relative mt-6 h-2 rounded-full bg-accent">
        {implied !== null && (
          <div className="absolute -top-6 -translate-x-1/2 text-center" style={{ left: pos(implied) }}>
            <div className="h-6 w-0.5 bg-primary" />
            <span className="num text-[10px] text-primary">{fmt.percent(implied * 100)}</span>
          </div>
        )}
        {own !== null && (
          <div className="absolute top-4 -translate-x-1/2 text-center" style={{ left: pos(own) }}>
            <div className="h-6 w-0.5 bg-warning" />
            <span className="num text-[10px] text-warning">نظر شما {fmt.percent(own * 100)}</span>
          </div>
        )}
      </div>
      <div className="mt-10 flex justify-between text-[10px] text-muted-foreground">
        <span className="num">{fmt.percent(min * 100)}</span>
        {gap !== null && <span className="num">اختلاف: {fmt.percent(gap * 100)}</span>}
        <span className="num">{fmt.percent(max * 100)}</span>
      </div>
    </Card>
  );
}

function TabGrid({ children }: { children: React.ReactNode }) {
  return <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.6fr)]">{children}</div>;
}

export function AnalysesPage() {
  const [tab, setTab] = React.useState("scenarios");
  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-xl font-bold">گام ۴: تحلیل‌های تکمیلی DCF</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          با همان سطرها و WACC، ریسک و حساسیت نتیجه و انتظارات بازار را بررسی کنید. بازه‌های حاصل را می‌توان به گام ۶ فرستاد.
        </p>
      </div>
      <Tabs value={tab} onValueChange={setTab} className="w-full">
        <TabsList className="justify-start">
          <TabsTrigger value="scenarios">سناریوها</TabsTrigger>
          <TabsTrigger value="sensitivity">حساسیت</TabsTrigger>
          <TabsTrigger value="reverse">DCF معکوس</TabsTrigger>
        </TabsList>
        <TabsContent value="scenarios"><TabGrid><ScenarioTab /></TabGrid></TabsContent>
        <TabsContent value="sensitivity"><TabGrid><SensitivityTab /></TabGrid></TabsContent>
        <TabsContent value="reverse"><TabGrid><ReverseTab /></TabGrid></TabsContent>
      </Tabs>
    </div>
  );
}
