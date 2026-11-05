import * as React from "react";
import { Plus, Trash2, Image as ImageIcon, FlaskConical } from "lucide-react";
import { SplitLayout } from "@/components/layout/SplitLayout";
import { NumberField } from "@/components/model/NumberField";
import { Hero, ComponentCards } from "@/components/model/ResultParts";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import { PortfolioScatter } from "@/components/charts/PortfolioScatter";
import { WeightBars } from "@/components/charts/WeightBars";
import { ErrorState, IncompleteState, ResultSkeleton } from "@/components/model/StateViews";
import type { ChartInstance } from "@/components/charts/Chart";
import { postPortfolioOptimize } from "@/api/endpoints";
import type { PortfolioOptimizeRequest, PortfolioAnalysisResult } from "@/api/types";
import { useAutoQuery } from "@/hooks/useAutoQuery";
import { useFormat } from "@/hooks/useFormat";
import { usePortfolio } from "@/store/portfolio";
import { exportChartPng } from "@/lib/png";
import { PORTFOLIO_OPTIMIZE_SAMPLE } from "@/lib/samples";

interface OptState {
  names: string[];
  meanReturnsPercent: number[];
  covariance: number[][];
  riskFreeRatePercent: number;
  riskAversion: number;
  allowShort: boolean;
  maxLeverage: number;
  frontierPoints: number;
}

const emptyState = (): OptState => ({
  names: ["الف", "ب"],
  meanReturnsPercent: [0, 0],
  covariance: [
    [0, 0],
    [0, 0],
  ],
  riskFreeRatePercent: 0,
  riskAversion: 3,
  allowShort: false,
  maxLeverage: 1,
  frontierPoints: 50,
});

export function PortfolioOptimizerPage() {
  const fmt = useFormat();
  const handoff = usePortfolio((s) => s.handoff);

  const [state, setState] = React.useState<OptState>(() =>
    handoff
      ? {
          names: handoff.assetNames,
          meanReturnsPercent: handoff.meanReturnsPercent,
          covariance: handoff.covariance,
          riskFreeRatePercent: 0,
          riskAversion: 3,
          allowShort: false,
          maxLeverage: 1,
          frontierPoints: 50,
        }
      : emptyState(),
  );

  const patch = (p: Partial<OptState>) => setState((s) => ({ ...s, ...p }));
  const n = state.names.length;

  const setName = (i: number, v: string) =>
    patch({ names: state.names.map((x, idx) => (idx === i ? v : x)) });
  const setMean = (i: number, v: number) =>
    patch({ meanReturnsPercent: state.meanReturnsPercent.map((x, idx) => (idx === i ? v : x)) });
  // mirror off-diagonal edits so the matrix stays symmetric
  const setCellSymmetric = (i: number, j: number, v: number) => {
    setState((s) => {
      const cov = s.covariance.map((r) => [...r]);
      cov[i][j] = v;
      cov[j][i] = v;
      return { ...s, covariance: cov };
    });
  };

  const addAsset = () => {
    if (n >= (state.allowShort ? 30 : 8)) return;
    setState((s) => ({
      ...s,
      names: [...s.names, `دارایی ${s.names.length + 1}`],
      meanReturnsPercent: [...s.meanReturnsPercent, 0],
      covariance: [...s.covariance.map((r) => [...r, 0]), Array.from({ length: s.names.length + 1 }, () => 0)],
    }));
  };
  const removeAsset = (i: number) => {
    if (n <= 2) return;
    setState((s) => ({
      ...s,
      names: s.names.filter((_, idx) => idx !== i),
      meanReturnsPercent: s.meanReturnsPercent.filter((_, idx) => idx !== i),
      covariance: s.covariance
        .filter((_, ri) => ri !== i)
        .map((r) => r.filter((_, ci) => ci !== i)),
    }));
  };

  const loadSample = () =>
    setState({
      names: [...PORTFOLIO_OPTIMIZE_SAMPLE.asset_names],
      meanReturnsPercent: [...PORTFOLIO_OPTIMIZE_SAMPLE.mean_returns],
      covariance: PORTFOLIO_OPTIMIZE_SAMPLE.covariance.map((r) => [...r]),
      riskFreeRatePercent: PORTFOLIO_OPTIMIZE_SAMPLE.risk_free_rate,
      riskAversion: PORTFOLIO_OPTIMIZE_SAMPLE.risk_aversion,
      allowShort: PORTFOLIO_OPTIMIZE_SAMPLE.allow_short,
      maxLeverage: PORTFOLIO_OPTIMIZE_SAMPLE.max_leverage,
      frontierPoints: PORTFOLIO_OPTIMIZE_SAMPLE.frontier_points,
    });

  const dimsOk =
    state.meanReturnsPercent.length === n &&
    state.covariance.length === n &&
    state.covariance.every((row) => row.length === n);
  const uniqueNames = new Set(state.names.map((x) => x.trim())).size === n && state.names.every((x) => x.trim());
  const covFinite = dimsOk && state.covariance.every((row) => row.every((v) => Number.isFinite(v)));
  const diagonalNonNeg = dimsOk && state.covariance.every((row, i) => row[i] >= 0);
  const symmetric = dimsOk && state.covariance.every((row, i) => row.every((v, j) => v === state.covariance[j][i]));

  const ready =
    dimsOk &&
    uniqueNames &&
    n >= 2 &&
    n <= (state.allowShort ? 30 : 8) &&
    Number.isFinite(state.riskAversion) &&
    state.riskAversion > 0 &&
    state.maxLeverage >= 0 &&
    state.maxLeverage <= 3 &&
    state.frontierPoints >= 5 &&
    state.frontierPoints <= 200 &&
    state.riskFreeRatePercent >= 0 &&
    covFinite &&
    symmetric &&
    diagonalNonNeg;

  const body: PortfolioOptimizeRequest | null = ready
    ? {
        asset_names: state.names.map((x) => x.trim()),
        mean_returns: state.meanReturnsPercent.map((x) => x / 100),
        covariance: state.covariance,
        risk_free_rate: state.riskFreeRatePercent / 100,
        risk_aversion: state.riskAversion,
        allow_short: state.allowShort,
        max_leverage: state.maxLeverage,
        frontier_points: state.frontierPoints,
      }
    : null;

  const query = useAutoQuery<PortfolioAnalysisResult>("portfolio-optimize", body, postPortfolioOptimize, ready);
  const res = query.data;
  const chartRef = React.useRef<ChartInstance | null>(null);

  const cp = res?.complete_portfolio;
  const assetLabels = res?.assets.map((a) => a.name) ?? [];

  return (
    <SplitLayout
      title="بهینه‌ساز سبد (میانگین-واریانس)"
      formula="max Sharpe → سبد مماس ;  y* = (μₜ − r_f) / (A σₜ²) ;  سبد کامل = y*·تماس + (1−y*)·بدون‌ریسک"
      whenSuitable="با بازده مورد انتظار و کوواریانس سالانه، مرز کارا، سبد مماس و سبد کامل متناسب با ریسک‌گریزی را می‌سازد."
      howToRead="نقطه‌ها دارایی‌ها، منحنی مرز کارا و خط‌چین تخصیص سرمایه‌اند. وزن‌های منفی فقط با فروش استقراضی مجازاند."
      input={
        <>
          <div className="space-y-2">
            <div className="text-sm text-muted-foreground">دارایی‌ها (بازده ٪ و کوواریانس)</div>
            {state.names.map((name, i) => (
              <div key={i} className="flex items-end gap-2">
                <div className="grid flex-1 gap-1">
                  {i === 0 && <span className="text-xs text-muted-foreground">نام</span>}
                  <Input value={name} onChange={(e) => setName(i, e.target.value)} aria-label="نام دارایی" className="h-8" />
                </div>
                <div className="w-28">
                  <NumberField label={i === 0 ? "بازده ٪" : ""} value={state.meanReturnsPercent[i]} onChange={(v) => setMean(i, v ?? 0)} compact suffix="٪" />
                </div>
                <Button type="button" variant="ghost" size="icon" aria-label="حذف دارایی" onClick={() => removeAsset(i)} disabled={n <= 2}>
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            ))}
            <Button type="button" variant="outline" size="sm" onClick={addAsset} disabled={n >= (state.allowShort ? 30 : 8)}>
              <Plus className="h-4 w-4" /> افزودن دارایی
            </Button>
            {!uniqueNames && <p className="text-xs text-negative">نام دارایی‌ها باید یکتا و پر باشد.</p>}
          </div>

          <div className="space-y-2">
            <div className="text-sm text-muted-foreground">ماتریس کوواریانس سالانه (متقارن)</div>
            <div dir="ltr" className="overflow-x-auto">
              <div className="inline-grid gap-1" style={{ gridTemplateColumns: `repeat(${n + 1}, minmax(0, 1fr))` }}>
                <span />
                {state.names.map((nm, j) => <span key={`h${j}`} className="px-1 text-center text-[10px] text-muted-foreground">{nm || j + 1}</span>)}
                {state.covariance.map((row, i) => (
                  <React.Fragment key={`r${i}`}>
                    <span className="flex items-center text-[10px] text-muted-foreground">{state.names[i] || i + 1}</span>
                    {row.map((v, j) => (
                      <div key={`c${i}-${j}`} className="w-20">
                        <NumberField label="" value={v} onChange={(nv) => setCellSymmetric(i, j, nv ?? 0)} compact step={0.0001} />
                      </div>
                    ))}
                  </React.Fragment>
                ))}
              </div>
            </div>
            {covFinite === false && dimsOk && <p className="text-xs text-warning">مقادیر کوواریانس باید عددی باشند.</p>}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <NumberField label="نرخ بدون ریسک" suffix="٪" value={state.riskFreeRatePercent} onChange={(v) => patch({ riskFreeRatePercent: v ?? 0 })} min={0} />
            <NumberField label="ریسک‌گریزی (A)" value={state.riskAversion} onChange={(v) => patch({ riskAversion: v ?? 0 })} min={0} info="عدد مثبت." />
            <NumberField label="سقف اهرم" value={state.maxLeverage} onChange={(v) => patch({ maxLeverage: v ?? 0 })} min={0} max={3} step={0.1} info="سقف وزن سبد مماس؛ ۰ تا ۳." />
            <NumberField label="نقاط مرز کارا" value={state.frontierPoints} onChange={(v) => patch({ frontierPoints: Math.round(v ?? 5) })} min={5} max={200} />
          </div>

          <div className="flex items-center gap-2">
            <Switch id="allow-short" checked={state.allowShort} onCheckedChange={(v) => patch({ allowShort: v })} />
            <label htmlFor="allow-short" className="text-sm text-muted-foreground">اجازهٔ فروش استقراضی</label>
          </div>
          {!state.allowShort && n > 8 && <p className="text-xs text-warning">در حالت فقط-طولانی تا ۸ دارایی مجاز است.</p>}

          <Button type="button" variant="secondary" size="sm" onClick={loadSample}>
            <FlaskConical className="h-4 w-4" /> مقادیر نمونه
          </Button>
        </>
      }
      results={
        !ready ? (
          <IncompleteState />
        ) : query.isPending && !res ? (
          <ResultSkeleton />
        ) : query.error ? (
          <ErrorState error={query.error} />
        ) : res ? (
          <div className={query.isFetching ? "is-updating space-y-4" : "space-y-4"}>
            <Hero label="بازده سبد کامل" value={fmt.percent(cp?.expected_return_percent ?? 0)} hint={`نوسان: ${fmt.percent(cp?.volatility_percent ?? 0)}`} />

            {cp && (
              <Card className="space-y-2 p-3">
                <div className="text-sm text-muted-foreground">سبد کامل</div>
                <ComponentCards
                  items={[
                    { label: "وزن سبد مماس", value: fmt.percent(cp.tangency_weight_percent) },
                    { label: "وزن بدون ریسک", value: fmt.percent(cp.risk_free_weight_percent) },
                    { label: "بازده", value: fmt.percent(cp.expected_return_percent) },
                    { label: "نوسان", value: fmt.percent(cp.volatility_percent) },
                  ]}
                />
                <div className="flex flex-wrap gap-2 pt-1">
                  {cp.leverage_capped && <Badge variant="outline" className="border-warning/50 text-warning">به سقف اهرم رسید (بریده شد)</Badge>}
                  {cp.clipped_to_zero && <Badge variant="outline" className="border-primary/50 text-primary">بازده مازاد منفی: y* = 0</Badge>}
                </div>
              </Card>
            )}

            <PortfolioScatter res={res} onInit={(chart) => (chartRef.current = chart)} />

            <Card className="space-y-2 p-3">
              <div className="text-sm text-muted-foreground">وزن دارایی‌های ریسک‌دار در سبد کامل (٪)</div>
              <WeightBars names={assetLabels} weightsPercent={cp?.risky_weights_percent ?? []} />
              {res.equal_weight && (
                <p className="text-xs text-muted-foreground">
                  وزن برابر: بازده {fmt.percent(res.equal_weight.expected_return_percent)}٪، نوسان {fmt.percent(res.equal_weight.volatility_percent)}٪.
                </p>
              )}
            </Card>

            <Button type="button" variant="outline" size="sm" onClick={() => chartRef.current && exportChartPng(chartRef.current, "portfolio-optimize.png")}>
              <ImageIcon className="h-4 w-4" /> خروجی PNG
            </Button>
          </div>
        ) : null
      }
    />
  );
}
