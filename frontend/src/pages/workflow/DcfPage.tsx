import * as React from "react";
import { PencilLine } from "lucide-react";
import { SplitLayout } from "@/components/layout/SplitLayout";
import { NumberField } from "@/components/model/NumberField";
import { Hero, ComponentCards, ResultStack } from "@/components/model/ResultParts";
import { InsightCallout } from "@/components/model/InsightCallout";
import { Chip } from "@/components/common/Chip";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { CopyButton, CsvButton } from "@/components/common/ExportButtons";
import { ProjectionsEditor } from "@/components/model/ProjectionsEditor";
import { DcfWaterfall } from "@/components/charts/Waterfall";
import { EmptyState, ErrorState, ResultSkeleton } from "@/components/model/StateViews";
import { PrerequisiteChecklist } from "@/components/model/PrerequisiteChecklist";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { postDcf } from "@/api/endpoints";
import type { DcfRequest, DcfResult } from "@/api/types";
import { useAutoQuery } from "@/hooks/useAutoQuery";
import { usePersistentState } from "@/hooks/usePersistentState";
import { useWorkflow } from "@/store/workflow";
import { useFormat } from "@/hooks/useFormat";
import { missingPrereqs, PREREQ_META } from "@/lib/prerequisites";
import { buildDcfBase } from "@/lib/dcfBase";
import { MIN_SPREAD_PP } from "@/lib/validation";

export function DcfPage() {
  const fmt = useFormat();
  const wf = useWorkflow();
  const [terminalGrowth, setTerminalGrowth] = usePersistentState<number>("dcf-terminal-growth", 3);
  const [editingRows, setEditingRows] = React.useState(false);

  const projections = wf.projections ?? [];
  const bs = wf.balanceSheet;
  const wacc = wf.waccPercent ?? undefined;

  const spreadOk = wacc !== undefined && terminalGrowth !== undefined && wacc - terminalGrowth >= MIN_SPREAD_PP;
  const ready =
    projections.length >= 1 &&
    projections.length <= 50 &&
    wacc !== undefined &&
    wacc > 0 &&
    spreadOk &&
    bs.sharesOutstanding > 0 &&
    bs.taxRate >= 0 &&
    bs.taxRate < 100;

  // Result-column checklist: the shared prerequisites this page still needs
  // (each links to the step that provides it) plus any DCF-only local blocker.
  const missing = missingPrereqs(["forecast", "wacc", "shares", "taxRate"], {
    forecast: wf.projections,
    wacc: wf.waccPercent,
    shares: bs.sharesOutstanding,
    taxRate: bs.taxRate,
    marketPrice: wf.marketPrice,
  });
  const local = [
    ...(projections.length > 50 ? ["تعداد سطرهای پیش‌بینی باید بین ۱ تا ۵۰ باشد."] : []),
    ...(wacc !== undefined && wacc > 0 && !spreadOk
      ? ["WACC باید دست‌کم ۰٫۵ واحد درصد از رشد پایانی بیشتر باشد."]
      : []),
  ];

  const body: DcfRequest | null = ready
    ? { ...buildDcfBase(wf), terminal_growth: terminalGrowth / 100 }
    : null;

  const query = useAutoQuery<DcfResult>("dcf", body, postDcf, ready);
  const res = query.data;

  // Step 3 is complete once a DCF result renders successfully.
  const completeStep = useWorkflow((s) => s.completeStep);
  React.useEffect(() => {
    if (res) completeStep("dcf");
  }, [res, completeStep]);

  const balance = (
    <>
      {wf.projections && (
        <div className="flex items-center justify-between">
          {!wf.projectionsDetached ? (
            <Chip tone="store">پیش‌بینی از گام ۱ ✓</Chip>
          ) : (
            <Chip tone="neutral">ویرایش دستی</Chip>
          )}
          <Button type="button" variant="ghost" size="sm" onClick={() => setEditingRows((e) => !e)}>
            <PencilLine className="h-4 w-4" />
            ویرایش سطرها
          </Button>
        </div>
      )}
      {editingRows && (
        <ProjectionsEditor
          rows={wf.projections ?? []}
          onChange={(rows) => wf.overrideProjections(rows)}
        />
      )}
    </>
  );

  return (
    <SplitLayout
      title="گام ۳: ارزش‌گذاری جریان نقدی تنزیل‌شده (DCF)"
      formula="EV = Σ PV(FCFF) + PV(TV) ;  Equity = EV + Cash − Debt − MI − Preferred"
      whenSuitable="سطرهای پیش‌بینی و WACC را مصرف می‌کند و ارزش بنگاه و ارزش هر سهم را می‌سازد."
      howToRead="ارزش هر سهم، ارزش حقوق صاحبان سهام تقسیم بر تعداد سهام است. ارزش منفی هم معتبر است (بدهی می‌تواند از ارزش بنگاه بیشتر شود)."
      input={
        <>
          {balance}
          <div className="flex flex-wrap gap-2">
            <Chip tone={wf.waccDetached || wf.waccPercent === null ? "neutral" : "store"}>
              WACC {wf.waccDetached ? "(دستی)" : wf.waccPercent === null ? "(وارد کنید)" : "از گام ۲ ✓"}
            </Chip>
          </div>
          <NumberField label="WACC" suffix="٪" value={wacc} onChange={(v) => v !== undefined && wf.overrideWacc(v)} info="نرخ تنزیل (٪)؛ باید از رشد پایانی حداقل ۰٫۵ واحد درصد بیشتر باشد." min={0} />
          <NumberField label="رشد پایانی" suffix="٪" value={terminalGrowth} onChange={(v) => setTerminalGrowth(v ?? 0)} min={0} max={200} />
          <NumberField label="نرخ مالیات" suffix="٪" id={PREREQ_META.taxRate.focusId} value={bs.taxRate} onChange={(v) => wf.setBalanceSheet({ taxRate: v ?? 0 })} min={0} max={100} />
          <NumberField label="تعداد سهام" suffix="سهم" id={PREREQ_META.shares.focusId} value={bs.sharesOutstanding} onChange={(v) => wf.setBalanceSheet({ sharesOutstanding: v ?? 0 })} min={0} />
          <div className="grid grid-cols-2 gap-3">
            <NumberField label="نقد" suffix={fmt.moneySuffix} value={bs.cash} onChange={(v) => wf.setBalanceSheet({ cash: v ?? 0 })} min={0} />
            <NumberField label="بدهی" suffix={fmt.moneySuffix} value={bs.debt} onChange={(v) => wf.setBalanceSheet({ debt: v ?? 0 })} min={0} />
            <NumberField label="منافع اقلیت" suffix={fmt.moneySuffix} value={bs.minorityInterest} onChange={(v) => wf.setBalanceSheet({ minorityInterest: v ?? 0 })} min={0} />
            <NumberField label="سهام ممتاز" suffix={fmt.moneySuffix} value={bs.preferredEquity} onChange={(v) => wf.setBalanceSheet({ preferredEquity: v ?? 0 })} min={0} />
          </div>
          <NumberField label="قیمت بازار (اختیاری)" suffix={fmt.moneySuffix} value={wf.marketPrice ?? undefined} onChange={(v) => wf.setMarketPrice(v ?? null)} min={0} />
        </>
      }
      results={
        !ready ? (
          <PrerequisiteChecklist missing={missing} local={local} />
        ) : query.isPending && !res ? (
          <ResultSkeleton />
        ) : query.error ? (
          <ErrorState error={query.error} />
        ) : res ? (
          <ResultStack updating={query.isFetching}>
            <Hero
              label="ارزش هر سهم"
              value={fmt.number(res.value_per_share)}
              tone={res.equity_value < 0 ? "negative" : "default"}
            />
            {res.equity_value < 0 && (
              <InsightCallout
                tone="negative"
                title="ارزش حقوق صاحبان سهام منفی است"
                explanation="بدهی از ارزش بنگاه بیشتر شده است؛ این یک نتیجهٔ معتبر است، نه خطا."
              />
            )}
            <ComponentCards
              items={[
                { label: "ارزش بنگاه (EV)", value: fmt.number(res.enterprise_value) },
                { label: "ارزش سهام", value: fmt.number(res.equity_value) },
              ]}
            />
            <DcfWaterfall res={res} />
            <TerminalValueBar share={res.terminal_value_share_percent} />
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    {["سال", "EBIT", "NOPAT", "استهلاک", "Capex", "ΔNWC", "FCFF", "ضریب تنزیل", "ارزش فعلی"].map((h) => (
                      <TableHead key={h}>{h}</TableHead>
                    ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {res.years.map((r) => (
                    <TableRow key={r.year}>
                      <TableCell className="num">{r.year}</TableCell>
                      <TableCell className="num">{fmt.number(r.ebit)}</TableCell>
                      <TableCell className="num">{fmt.number(r.nopat)}</TableCell>
                      <TableCell className="num">{fmt.number(r.depreciation)}</TableCell>
                      <TableCell className="num">{fmt.number(r.capex)}</TableCell>
                      <TableCell className="num">{fmt.number(r.delta_nwc)}</TableCell>
                      <TableCell className="num">{fmt.number(r.fcff)}</TableCell>
                      <TableCell className="num">{fmt.number(r.discount_factor, { maxFractionDigits: 4 })}</TableCell>
                      <TableCell className="num">{fmt.number(r.present_value)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
            <div className="flex flex-wrap gap-2">
              <CopyButton getText={() => `Value/share = ${res.value_per_share}`} label="کپی ارزش هر سهم" />
              <CsvButton
                filename="dcf-years.csv"
                getRows={() => [
                  ["year", "ebit", "nopat", "depreciation", "capex", "delta_nwc", "fcff", "discount_factor", "present_value"],
                  ...res.years.map((r) => [r.year, r.ebit, r.nopat, r.depreciation, r.capex, r.delta_nwc, r.fcff, r.discount_factor, r.present_value]),
                ]}
              />
            </div>
          </ResultStack>
        ) : (
          <EmptyState formula="EV = Σ PV(FCFF) + PV(TV)" whenSuitable="پیش‌بینی از گام ۱ بفرستید یا سطرها را وارد کنید." onLoadSample={() => wf.loadSample()} />
        )
      }
    />
  );
}

function TerminalValueBar({ share }: { share: number }) {
  const fmt = useFormat();
  const warn = share > 80;
  return (
    <div className="space-y-2">
      <Card className="p-3">
        <div className="mb-1 flex items-center justify-between text-sm">
          <span className="text-muted-foreground">سهم ارزش انتهایی از بنگاه</span>
          <span className="num" style={{ color: warn ? "var(--warning)" : undefined }}>
            {fmt.percent(share)}
          </span>
        </div>
        <div className="h-2 w-full overflow-hidden rounded-full bg-accent">
          <div
            className="h-full rounded-full"
            style={{ width: `${Math.min(share, 100)}%`, background: warn ? "var(--warning)" : "var(--primary)" }}
          />
        </div>
      </Card>
      {warn && (
        <InsightCallout
          tone="warning"
          title="سهم ارزش انتهایی بیش از ۸۰٪ است"
          explanation="بخش بزرگی از ارزش به فرضیات دورهٔ پایانی وابسته است؛ آن را با دقت بررسی کنید."
        />
      )}
    </div>
  );
}
