import * as React from "react";
import { useNavigate } from "react-router-dom";
import { Upload, Send, FlaskConical } from "lucide-react";
import { SplitLayout } from "@/components/layout/SplitLayout";
import { NumberField } from "@/components/model/NumberField";
import { ComponentCards } from "@/components/model/ResultParts";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ErrorState, IncompleteState, ResultSkeleton } from "@/components/model/StateViews";
import { postPortfolioStatistics } from "@/api/endpoints";
import type { PortfolioStatisticsRequest, PortfolioStatisticsResult, PriceSeriesInput } from "@/api/types";
import { useAutoQuery } from "@/hooks/useAutoQuery";
import { useFormat } from "@/hooks/useFormat";
import { parsePriceGrid, type ParsedSeries } from "@/lib/parsePrices";
import { usePortfolio } from "@/store/portfolio";
import { PORTFOLIO_STATISTICS_SAMPLE } from "@/lib/samples";

const PRESETS = [252, 52, 12, 1];

/** Diverging background for a correlation value in [-1, 1]. */
function corrBg(v: number): React.CSSProperties {
  const clamped = Math.max(-1, Math.min(1, v));
  const intensity = Math.abs(clamped) * 0.5 + 0.05;
  const rgb = clamped >= 0 ? "76, 175, 122" : "229, 100, 95"; // positive / negative
  return { backgroundColor: `rgba(${rgb}, ${intensity})` };
}

export function PortfolioStatisticsPage() {
  const fmt = useFormat();
  const navigate = useNavigate();
  const setHandoff = usePortfolio((s) => s.setHandoff);

  const [text, setText] = React.useState("");
  const [series, setSeries] = React.useState<ParsedSeries[]>([]);
  const [parseError, setParseError] = React.useState<string | null>(null);
  const [periods, setPeriods] = React.useState(52);

  const parse = React.useCallback((raw: string) => {
    setText(raw);
    const result = parsePriceGrid(raw);
    if (result.error) {
      setParseError(result.error);
      setSeries([]);
    } else {
      setParseError(null);
      setSeries(result.series);
    }
  }, []);

  const onFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    parse(await file.text());
  };

  const n = series.length;
  const aligned = series.every((s) => s.prices.length === series[0]?.prices.length);
  const ready = !parseError && n >= 2 && n <= 30 && aligned && series.every((s) => s.prices.length >= 3);

  const assets: PriceSeriesInput[] = series.map((s) => ({ name: s.name, prices: s.prices }));
  const body: PortfolioStatisticsRequest | null = ready ? { assets, periods_per_year: periods } : null;

  const query = useAutoQuery<PortfolioStatisticsResult>("portfolio-statistics", body, postPortfolioStatistics, ready);
  const res = query.data;

  const loadSample = () => {
    const grid = [
      PORTFOLIO_STATISTICS_SAMPLE.assets.map((a) => a.name).join("\t"),
      ...Array.from({ length: PORTFOLIO_STATISTICS_SAMPLE.assets[0].prices.length }, (_, r) =>
        PORTFOLIO_STATISTICS_SAMPLE.assets.map((a) => String(a.prices[r])).join("\t"),
      ),
    ].join("\n");
    setPeriods(PORTFOLIO_STATISTICS_SAMPLE.periods_per_year);
    parse(grid);
  };

  const useInOptimizer = () => {
    if (!res) return;
    setHandoff({
      assetNames: series.map((s) => s.name),
      meanReturnsPercent: res.mean_returns_percent,
      covariance: res.covariance,
    });
    navigate("/portfolio/optimize");
  };

  return (
    <SplitLayout
      title="آماره سبد از قیمت‌ها"
      formula="rₜ = Pₜ / Pₜ₋₁ − 1 ;  σ_annual = σ_period × √m ;  cov, corr over returns"
      whenSuitable="از یک جدول قیمت (سطر اول نام دارایی‌ها، هر ستون یک دارایی) میانگین، نوسان، کوواریانس و همبستگی سالانه می‌سازد."
      howToRead="مشاهدات، تعداد بازده است (یکی کمتر از تعداد قیمت). برای بهینه‌ساز، ورودی‌ها باید هم‌تراز و هم‌طول باشند."
      input={
        <>
          <textarea
            dir="ltr"
            value={text}
            onChange={(e) => parse(e.target.value)}
            rows={8}
            placeholder={"الف\tب\n8\t8\n12\t8\n6\t12\n6\t6"}
            className="num w-full rounded-md border border-input bg-bg p-2 text-sm"
            aria-label="جدول قیمت (چسبانی)"
          />
          <div className="flex flex-wrap items-center gap-2">
            <label className="inline-flex cursor-pointer items-center gap-2 rounded-md border border-input px-3 py-1.5 text-sm text-muted-foreground hover:text-foreground">
              <Upload className="h-4 w-4" />
              بارگذاری CSV
              <input type="file" accept=".csv,.txt,text/csv,text/plain" className="hidden" onChange={onFile} />
            </label>
            <Button type="button" variant="secondary" size="sm" onClick={loadSample}>
              <FlaskConical className="h-4 w-4" /> مقادیر نمونه
            </Button>
          </div>
          {parseError && <p className="text-xs text-negative">{parseError}</p>}
          {series.length > 0 && !aligned && <p className="text-xs text-negative">طول ستون‌ها یکسان نیست.</p>}

          <div className="space-y-2">
            <div className="text-sm text-muted-foreground">دوره در سال (m)</div>
            <div className="flex flex-wrap items-center gap-2">
              {PRESETS.map((p) => (
                <Button
                  key={p}
                  type="button"
                  variant={periods === p ? "default" : "outline"}
                  size="sm"
                  onClick={() => setPeriods(p)}
                >
                  {p}
                </Button>
              ))}
              <div className="w-28">
                <NumberField label="سفارشی" value={periods} onChange={(v) => setPeriods(Math.round(v ?? 1))} min={1} max={366} compact />
              </div>
            </div>
          </div>
        </>
      }
      results={
        series.length === 0 ? (
          <Card className="p-6 text-center text-sm text-muted-foreground">جدول قیمت را بچسبانید یا فایل CSV بارگذاری کنید.</Card>
        ) : !ready ? (
          <IncompleteState />
        ) : query.isPending && !res ? (
          <ResultSkeleton />
        ) : query.error ? (
          <ErrorState error={query.error} />
        ) : res ? (
          <div className={query.isFetching ? "is-updating space-y-4" : "space-y-4"}>
            <ComponentCards
              items={[
                ...series.map((s, i) => ({
                  label: `بازده سالانهٔ ${s.name}`,
                  value: fmt.percent(res.mean_returns_percent[i]),
                  hint: `نوسان: ${fmt.percent(res.volatilities_percent[i])}`,
                })),
                { label: "مشاهدات (بازده‌ها)", value: fmt.number(res.observations) },
              ]}
            />

            <Card className="p-3">
              <div className="mb-2 text-sm text-muted-foreground">ماتریس همبستگی</div>
              <div dir="ltr" className="overflow-x-auto">
                <table className="border-separate border-spacing-0.5 text-table-num">
                  <thead>
                    <tr>
                      <th className="p-1 text-[10px] text-muted-foreground" />
                      {series.map((s) => (
                        <th key={s.name} className="min-w-12 p-1 text-[10px] font-medium text-muted-foreground">{s.name}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {res.correlation.map((row, i) => (
                      <tr key={i}>
                        <th className="whitespace-nowrap p-1 text-right text-[10px] font-medium text-muted-foreground">{series[i]?.name}</th>
                        {row.map((v, j) => (
                          <td key={j}>
                            <div className="num flex h-8 min-w-12 items-center justify-center rounded-sm border border-border text-[11px]" style={corrBg(v)}>
                              {fmt.number(v, { maxFractionDigits: 2 })}
                            </div>
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>

            <Card className="p-3">
              <div className="mb-2 text-sm text-muted-foreground">ماتریس کوواریانس سالانه</div>
              <div className="overflow-x-auto" dir="ltr">
                <Table className="text-table-num">
                  <TableHeader>
                    <TableRow>
                      <TableHead />
                      {series.map((s) => <TableHead key={s.name}>{s.name}</TableHead>)}
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {res.covariance.map((row, i) => (
                      <TableRow key={i}>
                        <TableCell className="font-medium">{series[i]?.name}</TableCell>
                        {row.map((v, j) => (
                          <TableCell key={j} className="num">{fmt.number(v, { maxFractionDigits: 4 })}</TableCell>
                        ))}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </Card>

            <Button type="button" size="sm" onClick={useInOptimizer} disabled={series.length > 8}>
              <Send className="h-4 w-4" /> استفاده در بهینه‌ساز
            </Button>
            {series.length > 8 && <p className="text-xs text-warning">بهینه‌ساز با وزن مثبت تا ۸ دارایی را پشتیبانی می‌کند.</p>}
          </div>
        ) : null
      }
    />
  );
}
