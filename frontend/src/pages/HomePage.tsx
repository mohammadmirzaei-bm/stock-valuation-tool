import * as React from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, Download, RotateCcw, Sparkles, TrendingUp } from "lucide-react";
import type { EChartsOption } from "echarts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ConfirmDialog, RESET_DIALOG_COPY, useConfirmDialog } from "@/components/common/ConfirmDialog";
import { Skeleton } from "@/components/common/Skeleton";
import { MetricCard } from "@/components/dashboard/MetricCard";
import { TasksCard } from "@/components/dashboard/TasksCard";
import { DataStatusCard } from "@/components/dashboard/DataStatusCard";
import { NotificationsCard, type Insight } from "@/components/dashboard/NotificationsCard";
import { Chart } from "@/components/charts/Chart";
import { Donut } from "@/components/charts/Basic";
import { axisLabelStyle, axisStyle, baseOption, chartColors, legendStyle } from "@/components/charts/theme";
import { WORKFLOW_STEPS } from "@/config/models";
import { useWorkflow } from "@/store/workflow";
import { stepComplete } from "@/components/layout/Stepper";
import { useFormat } from "@/hooks/useFormat";
import { usePersistentState } from "@/hooks/usePersistentState";
import { useAutoQuery } from "@/hooks/useAutoQuery";
import { postDcf } from "@/api/endpoints";
import type { DcfRequest, DcfResult } from "@/api/types";
import { buildDcfBase } from "@/lib/dcfBase";
import { MIN_SPREAD_PP } from "@/lib/validation";
import { downloadCsv } from "@/lib/csv";

/** Time-of-day greeting (the workspace's "Good morning" header). */
function greeting(): string {
  const h = new Date().getHours();
  if (h < 12) return "صبح بخیر";
  if (h < 17) return "ظهر بخیر";
  if (h < 21) return "عصر بخیر";
  return "شب بخیر";
}

/** Overview: a live workspace dashboard over the shared workflow store. The
 *  DCF query shares its cache key with the DCF page, so metrics reflect the
 *  exact inputs the student last used there. */
export function HomePage() {
  const navigate = useNavigate();
  const fmt = useFormat();
  const wf = useWorkflow();
  const confirm = useConfirmDialog();
  // Same persisted key the DCF page writes, so the dashboard uses the student's
  // actual terminal-growth assumption rather than a hardcoded guess.
  const [terminalGrowth] = usePersistentState<number>("dcf-terminal-growth", 3);

  const bs = wf.balanceSheet;
  const wacc = wf.waccPercent;
  const projections = wf.projections;
  const spreadOk = wacc !== null && wacc - terminalGrowth >= MIN_SPREAD_PP;
  const ready =
    !!projections && projections.length >= 1 && projections.length <= 50 &&
    wacc !== null && wacc > 0 && spreadOk &&
    bs.sharesOutstanding > 0 && bs.taxRate >= 0 && bs.taxRate < 100;

  const body: DcfRequest | null = ready ? { ...buildDcfBase(wf), terminal_growth: terminalGrowth / 100 } : null;
  const dcfQuery = useAutoQuery<DcfResult>("dcf", body, postDcf, ready);
  const dcf = dcfQuery.data;

  const doneCount = WORKFLOW_STEPS.filter((s) => stepComplete(wf.completed, s.id)).length;
  const nextStep = WORKFLOW_STEPS.find((s) => !stepComplete(wf.completed, s.id));

  const upside = dcf && wf.marketPrice && wf.marketPrice > 0
    ? ((dcf.value_per_share - wf.marketPrice) / wf.marketPrice) * 100
    : null;

  const insights = React.useMemo<Insight[]>(() => {
    const list: Insight[] = [];
    if (!projections) {
      list.push({ id: "start", tone: "info", title: "گردش کار را شروع کنید", body: "با دادهٔ نمونه یا پیش‌بینی درآمد آغاز کنید.", to: "/forecast" });
    }
    if (projections && !wf.completed.dcf) {
      list.push({ id: "send-dcf", tone: "info", title: "پیش‌بینی آمادهٔ ارسال است", body: "سطرها را به DCF بفرستید تا ارزش هر سهم محاسبه شود.", to: "/dcf" });
    }
    if (dcf && dcf.terminal_value_share_percent > 80) {
      list.push({ id: "tv-high", tone: "warning", title: "سهم ارزش پایانی بیش از ۸۰٪", body: "بخش بزرگی از ارزش به فرضیات دورهٔ پایانی وابسته است.", to: "/dcf" });
    }
    if (dcf && dcf.equity_value < 0) {
      list.push({ id: "neg-equity", tone: "negative", title: "ارزش حقوق صاحبان سهام منفی است", body: "بدهی از ارزش بنگاه بیشتر شده؛ این نتیجه معتبر است، نه خطا.", to: "/dcf" });
    }
    if (upside !== null && upside > 0) {
      list.push({ id: "upside", tone: "positive", title: "قیمت بازار پایین‌تر از ارزش ذاتی", body: `حدود ${fmt.percent(upside)} فضای رشد نسبت به قیمت بازار.`, to: "/football-field" });
    }
    if (doneCount === WORKFLOW_STEPS.length) {
      list.push({ id: "complete", tone: "positive", title: "گردش کار کامل شد", body: "هر شش گام انجام شده — زمین فوتبال را بازبینی کنید.", to: "/football-field" });
    }
    return list;
  }, [projections, wf.completed.dcf, dcf, upside, doneCount, fmt]);

  const exportCsv = () => {
    downloadCsv("valuation-overview.csv", [
      ["بخش", "کلید", "مقدار"],
      ["سنجش", "ارزش هر سهم", dcf?.value_per_share ?? ""],
      ["سنجش", "ارزش بنگاه", dcf?.enterprise_value ?? ""],
      ["سنجش", "WACC (٪)", wacc ?? ""],
      ["سنجش", "سهم ارزش پایانی (٪)", dcf?.terminal_value_share_percent ?? ""],
      ["سنجش", "قیمت بازار", wf.marketPrice ?? ""],
      [],
      ["سال", "EBIT", "استهلاک", "Capex", "ΔNWC"],
      ...(projections ?? []).map((r, i) => [i + 1, r.ebit, r.depreciation, r.capex, r.delta_nwc]),
    ]);
  };

  const dash = "—";

  return (
    <div className="dashboard-home space-y-6">
      {/* Greeting + actions */}
      <section className="flex flex-wrap items-end justify-between gap-3">
        <div className="min-w-0">
          <h2 className="text-[26px] font-bold leading-tight">{greeting()}، دانشجوی عزیز</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            نمای کلی گردش کار ارزش‌گذاری — داده‌ها به‌صورت محلی روی همین دستگاه ذخیره می‌شوند.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {projections ? (
            <Button type="button" size="sm" onClick={() => navigate(nextStep ? nextStep.path : "/football-field")}>
              {nextStep ? `ادامه: ${nextStep.label}` : "زمین فوتبال"}
              <ArrowLeft className="h-4 w-4" />
            </Button>
          ) : (
            <Button type="button" size="sm" onClick={() => wf.loadSample()}>
              <Sparkles className="h-4 w-4" />
              شروع با نمونه
            </Button>
          )}
          <Button type="button" variant="outline" size="sm" onClick={exportCsv} disabled={!projections}>
            <Download className="h-4 w-4" />
            خروجی CSV
          </Button>
          <Button type="button" variant="ghost" size="sm" onClick={confirm.request}>
            <RotateCcw className="h-4 w-4" />
            بازنشانی
          </Button>
        </div>
      </section>

      {/* Metric cards */}
      <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="سنجه‌های کلیدی">
        <MetricCard
          label="ارزش هر سهم"
          badge="DCF"
          value={dcf ? fmt.number(dcf.value_per_share) : dash}
          tone={dcf && dcf.equity_value < 0 ? "negative" : "default"}
          delta={upside !== null ? { text: fmt.signedPercent(upside), dir: upside >= 0 ? "up" : "down", tone: upside >= 0 ? "positive" : "negative" } : null}
          hint={upside !== null ? "نسبت به بازار" : dcf ? "قیمت بازار را وارد کنید" : "پیش‌بینی را کامل کنید"}
          spark={dcf?.years.map((r) => r.present_value)}
        />
        <MetricCard
          label="ارزش بنگاه (EV)"
          badge="EV"
          value={dcf ? fmt.number(dcf.enterprise_value) : dash}
          hint={dcf ? "ارزش کل شرکت" : "پیش‌بینی را کامل کنید"}
          spark={dcf?.years.map((r) => r.fcff)}
          sparkTone="var(--chart-3)"
        />
        <MetricCard
          label="نرخ تنزیل (WACC)"
          badge="٪"
          value={wacc !== null ? fmt.percent(wacc) : dash}
          hint={wacc !== null ? `رشد پایانی ${fmt.percent(terminalGrowth)}` : "از گام ۲ وارد کنید"}
          spark={dcf?.years.map((r) => r.discount_factor)}
          sparkTone="var(--warning)"
        />
        <MetricCard
          label="سهم ارزش پایانی"
          badge="TV"
          value={dcf ? fmt.percent(dcf.terminal_value_share_percent) : dash}
          tone={dcf && dcf.terminal_value_share_percent > 80 ? "warning" : "default"}
          hint={dcf ? (dcf.terminal_value_share_percent > 80 ? "وابستگی بالا به فرض پایانی" : "از ارزش بنگاه") : "پیش‌بینی را کامل کنید"}
        />
      </section>

      {/* Charts */}
      <section className="grid grid-cols-1 gap-4 xl:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">روند جریان نقدی</CardTitle>
              <span className="text-xs text-muted-foreground">ارزش فعلی و جریان نقدی آزاد هر سال</span>
            </div>
          </CardHeader>
          <CardContent>
            {dcf ? (
              <CashflowTrend res={dcf} />
            ) : dcfQuery.isPending && ready ? (
              <Skeleton className="h-[300px] w-full rounded-lg" />
            ) : (
              <EmptyChart
                title="هنوز جریان نقدی محاسبه نشده"
                body="پیش‌بینی را کامل کنید یا دادهٔ نمونه را بارگذاری کنید تا روند اینجا نمایش داده شود."
                onSample={() => wf.loadSample()}
              />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">ترکیب ارزش بنگاه</CardTitle>
              {dcf && <span className="num text-xs text-muted-foreground">{fmt.number(dcf.enterprise_value)}</span>}
            </div>
          </CardHeader>
          <CardContent>
            {dcf ? (
              <>
                <Donut
                  height={220}
                  data={[
                    { name: "دورهٔ صریح", value: dcf.pv_fcff_total, color: "var(--primary)" },
                    { name: "ارزش پایانی", value: dcf.pv_terminal_value, color: "var(--chart-2)" },
                  ]}
                  summary={`سهم دورهٔ صریح ${fmt.percent(100 - dcf.terminal_value_share_percent)} و سهم ارزش پایانی ${fmt.percent(dcf.terminal_value_share_percent)} از ارزش بنگاه.`}
                />
                <p className="mt-2 text-xs leading-5 text-muted-foreground">
                  {dcf.terminal_value_share_percent > 80
                    ? "بیشتر ارزش از فرض دورهٔ پایانی می‌آید؛ آن را با احتیاط بررسی کنید."
                    : "بخش عمدهٔ ارزش از جریان‌های نقدی دورهٔ صریح تأمین می‌شود."}
                </p>
              </>
            ) : (
              <EmptyChart
                title="ترکیب ارزش نامشخص"
                body="پس از محاسبهٔ DCF، سهم دورهٔ صریح و ارزش پایانی اینجا دیده می‌شود."
                onSample={() => wf.loadSample()}
              />
            )}
          </CardContent>
        </Card>
      </section>

      {/* Tasks / data status / notifications */}
      <section className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <TasksCard />
        <DataStatusCard />
        <NotificationsCard insights={insights} />
      </section>

      <ConfirmDialog
        open={confirm.open}
        onOpenChange={confirm.onOpenChange}
        {...RESET_DIALOG_COPY}
        onConfirm={() => { wf.reset(); navigate("/"); }}
      />
    </div>
  );
}

/** Area (present value) + line (FCFF) per forecast year, from the DCF result. */
function CashflowTrend({ res }: { res: DcfResult }) {
  const fmt = useFormat();
  const c = chartColors();
  const option = React.useMemo<EChartsOption>(() => {
    const years = res.years.map((r) => `سال ${fmt.number(r.year)}`);
    return {
      ...baseOption(c),
      legend: legendStyle(c),
      grid: { left: 8, right: 16, top: 36, bottom: 8, containLabel: true },
      tooltip: { ...baseOption(c).tooltip, trigger: "axis", valueFormatter: (v: any) => fmt.number(v as number) },
      xAxis: { type: "category", boundaryGap: false, data: years, ...axisStyle(c) },
      yAxis: { type: "value", ...axisStyle(c), axisLabel: { ...axisLabelStyle(c), formatter: (v: number) => fmt.number(v) } },
      series: [
        {
          name: "ارزش فعلی",
          type: "line",
          data: res.years.map((r) => r.present_value),
          smooth: true,
          showSymbol: false,
          lineStyle: { color: c.primary, width: 2 },
          itemStyle: { color: c.primary },
          areaStyle: { color: c.primary, opacity: 0.07 },
        },
        {
          name: "جریان نقدی آزاد",
          type: "line",
          data: res.years.map((r) => r.fcff),
          smooth: true,
          showSymbol: true,
          symbolSize: 5,
          lineStyle: { color: c.warning, width: 2 },
          itemStyle: { color: c.warning },
        },
      ],
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [res, fmt.digits]);
  return (
    <Chart
      option={option}
      height={300}
      summary={`روند ارزش فعلی و جریان نقدی آزاد در ${fmt.number(res.years.length)} سال پیش‌بینی.`}
    />
  );
}

/** Empty chart placeholder with a sample-data action (no empty chart frame). */
function EmptyChart({ title, body, onSample }: { title: string; body: string; onSample: () => void }) {
  return (
    <div className="flex h-[300px] flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-border bg-surface-2/40 px-6 text-center">
      <span className="tool-icon flex h-11 w-11 items-center justify-center rounded-xl">
        <TrendingUp className="h-5 w-5" />
      </span>
      <div className="text-sm font-semibold text-foreground">{title}</div>
      <p className="max-w-xs text-xs leading-5 text-muted-foreground">{body}</p>
      <Button type="button" variant="secondary" size="sm" onClick={onSample}>
        <Sparkles className="h-4 w-4" />
        بارگذاری دادهٔ نمونه
      </Button>
    </div>
  );
}