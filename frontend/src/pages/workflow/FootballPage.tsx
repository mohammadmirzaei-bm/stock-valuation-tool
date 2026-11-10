import * as React from "react";
import { Plus, Trash2, Image as ImageIcon, Copy } from "lucide-react";
import { SplitLayout } from "@/components/layout/SplitLayout";
import { NumberField } from "@/components/model/NumberField";
import { Hero, ComponentCards, ResultStack } from "@/components/model/ResultParts";
import { Chip } from "@/components/common/Chip";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { FootballFieldChart } from "@/components/charts/FootballField";
import { EmptyState, ErrorState, ResultSkeleton } from "@/components/model/StateViews";
import { PrerequisiteChecklist } from "@/components/model/PrerequisiteChecklist";
import type { ChartInstance } from "@/components/charts/Chart";
import { postFootballField } from "@/api/endpoints";
import type { FootballFieldRequest, FootballFieldResult, ValuationRangeInput } from "@/api/types";
import { useAutoQuery } from "@/hooks/useAutoQuery";
import { useWorkflow } from "@/store/workflow";
import { useFormat } from "@/hooks/useFormat";
import { marketPositionView, toneText } from "@/lib/semantics";
import { exportChartPng } from "@/lib/png";
import { copyText } from "@/lib/clipboard";

export function FootballPage() {
  const fmt = useFormat();
  const wf = useWorkflow();
  const rows = wf.ranges;
  const chartRef = React.useRef<ChartInstance | null>(null);
  const [copied, setCopied] = React.useState(false);

  const uniqueMethods = new Set(rows.map((r) => r.method.trim())).size === rows.length;
  const ordered = rows.every((r) => r.low <= r.mid && r.mid <= r.high);
  const ready = rows.length >= 1 && rows.length <= 12 && uniqueMethods && ordered;

  // Ranges are collected on this page (or sent from steps 4/5) and market price
  // is optional, so nothing here links to another step — only local range rules.
  const local = [
    ...(uniqueMethods ? [] : ["نام روش‌ها باید یکتا باشد."]),
    ...(ordered ? [] : ["برای هر روش کمینه ≤ میانی ≤ بیشینه باشد."]),
    ...(rows.length <= 12 ? [] : ["حداکثر ۱۲ بازه مجاز است."]),
  ];

  const ranges: ValuationRangeInput[] = rows.map((r) => ({
    method: r.method.trim(),
    low: r.low,
    mid: r.mid,
    high: r.high,
  }));

  const body: FootballFieldRequest | null = ready
    ? { ranges, market_price: wf.marketPrice ?? null }
    : null;

  const query = useAutoQuery<FootballFieldResult>("football-field", body, postFootballField, ready);
  const res = query.data;

  // Step 6 is complete once the football-field result renders successfully.
  const completeStep = useWorkflow((s) => s.completeStep);
  React.useEffect(() => {
    if (res) completeStep("football");
  }, [res, completeStep]);

  const addRow = () =>
    wf.upsertRange({ method: `روش ${rows.length + 1}`, low: 0, mid: 0, high: 0, source: "دستی" });

  const summaryText = () => {
    if (!res) return "";
    const lines = [
      `زمین فوتبال — بازار: ${res.market_price ?? "بدون قیمت"}`,
      `بازه کلی: ${res.overall_low} تا ${res.overall_high}`,
      `میانهٔ میانی‌ها: ${res.median_of_mids}   میانگین میانی‌ها: ${res.mean_of_mids}`,
      res.has_overlap ? `ناحیهٔ همپوشانی: ${res.overlap_low} تا ${res.overlap_high}` : "هیچ ناحیهٔ همپوشانی مشترکی وجود ندارد",
      ...res.rows.map((r) => `- ${r.method}: ${r.low} – ${r.high} (میانی ${r.mid})${r.market_position ? ` [${marketPositionView(r.market_position)?.label}]` : ""}`),
    ];
    return lines.join("\n");
  };

  const inOverlapLabel =
    res?.market_price_in_overlap === null || res?.market_price_in_overlap === undefined
      ? "بدون قیمت بازار"
      : res.market_price_in_overlap
        ? "بله، داخل همپوشانی"
        : "خیر، خارج از همپوشانی";

  return (
    <SplitLayout
      title="گام ۶: زمین فوتبال (جمع‌بندی روش‌ها)"
      formula="Range per method: [low, mid, high]  →  overlap of all methods"
      whenSuitable="بازه‌های ارزش هر روش (DCF، سناریو، حساسیت، ضرایب) را در یک نمودار مقایسه می‌کند."
      howToRead="هر میله بازهٔ یک روش است؛ لوزی مقدار میانی و خط‌چین قیمت بازار. ناحیهٔ شفاف، همپوشانی همهٔ روش‌هاست."
      input={
        <>
          <NumberField label="قیمت بازار (اختیاری)" suffix={fmt.moneySuffix} value={wf.marketPrice ?? undefined} onChange={(v) => wf.setMarketPrice(v ?? null)} min={0} />
          <div className="text-sm text-muted-foreground">بازه‌ها (۱ تا ۱۲)</div>

          {!rows.length && (
            <p className="text-xs text-warning">هنوز بازه‌ای جمع نشده؛ از گام‌های ۴ و ۵ «ارسال به زمین فوتبال» را بزنید یا دستی بیفزایید.</p>
          )}

          <div className="space-y-3">
            {rows.map((r) => (
              <Card key={r.id} className="space-y-2 p-3">
                <div className="flex items-center justify-between gap-2">
                  <Input
                    value={r.method}
                    onChange={(e) => wf.updateRange(r.id, { method: e.target.value })}
                    aria-label="نام روش"
                    className="h-8 max-w-40"
                  />
                  <div className="flex items-center gap-2">
                    {r.source && <Chip tone="source">{r.source}</Chip>}
                    <Button type="button" variant="ghost" size="icon" aria-label="حذف بازه" onClick={() => wf.removeRange(r.id)}>
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-2">
                  <NumberField label="کمینه" value={r.low} onChange={(v) => wf.updateRange(r.id, { low: v ?? 0 })} compact />
                  <NumberField label="میانی" value={r.mid} onChange={(v) => wf.updateRange(r.id, { mid: v ?? 0 })} compact />
                  <NumberField label="بیشینه" value={r.high} onChange={(v) => wf.updateRange(r.id, { high: v ?? 0 })} compact />
                </div>
              </Card>
            ))}
          </div>

          <div className="flex flex-wrap gap-2">
            <Button type="button" variant="outline" size="sm" disabled={rows.length >= 12} onClick={addRow}>
              <Plus className="h-4 w-4" /> افزودن بازه
            </Button>
            <Button type="button" variant="secondary" size="sm" onClick={() => wf.loadSample()}>
              بارگذاری نمونه
            </Button>
          </div>
          {!uniqueMethods && <p className="text-xs text-negative">نام روش‌ها باید یکتا باشد.</p>}
          {!ordered && rows.length > 0 && <p className="text-xs text-negative">برای هر روش باید کمینه ≤ میانی ≤ بیشینه باشد.</p>}
        </>
      }
      results={
        rows.length === 0 ? (
          <EmptyState formula="چند بازه جمع کنید تا نمودار ساخته شود." whenSuitable="از گام‌های پیشین بازه بفرستید یا دستی وارد کنید." onLoadSample={() => wf.loadSample()} />
        ) : !ready ? (
          <PrerequisiteChecklist missing={[]} local={local} />
        ) : query.isPending && !res ? (
          <ResultSkeleton />
        ) : query.error ? (
          <ErrorState error={query.error} />
        ) : res ? (
          <ResultStack updating={query.isFetching}>
            <Hero label="بازهٔ کلی ارزش هر سهم" value={`${fmt.number(res.overall_low)} – ${fmt.number(res.overall_high)}`} />
            <ComponentCards
              items={[
                { label: "میانهٔ میانی‌ها", value: fmt.number(res.median_of_mids) },
                { label: "میانگین میانی‌ها", value: fmt.number(res.mean_of_mids) },
                { label: "قیمت داخل همپوشانی؟", value: inOverlapLabel, tone: res.market_price_in_overlap ? "positive" : res.market_price_in_overlap === false ? "warning" : "default" },
              ]}
            />
            <FootballFieldChart res={res} onInit={(chart) => (chartRef.current = chart)} format={(v) => fmt.number(v)} />

            <Card className="p-3">
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      {["روش", "کمینه", "میانی", "بیشینه", "موقعیت نسبت به بازار", "بازده میانی"].map((h) => (
                        <TableHead key={h}>{h}</TableHead>
                      ))}
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {res.rows.map((r) => {
                      const view = marketPositionView(r.market_position);
                      return (
                        <TableRow key={r.method}>
                          <TableCell>{r.method}</TableCell>
                          <TableCell className="num">{fmt.number(r.low)}</TableCell>
                          <TableCell className="num">{fmt.number(r.mid)}</TableCell>
                          <TableCell className="num">{fmt.number(r.high)}</TableCell>
                          <TableCell className={view ? toneText[view.tone] : "text-muted-foreground"}>
                            {view ? <span>{view.label}</span> : "—"}
                          </TableCell>
                          <TableCell className="num">{r.upside_of_mid_percent !== null ? fmt.signedPercent(r.upside_of_mid_percent) : "—"}</TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </div>
              {!res.has_overlap && <p className="mt-2 text-xs text-warning">روش‌ها ناحیهٔ همپوشانی مشترک ندارند؛ اختلاف فرضیات را بررسی کنید.</p>}
            </Card>

            <div className="flex flex-wrap gap-2">
              <Button type="button" variant="outline" size="sm" onClick={() => chartRef.current && exportChartPng(chartRef.current, "football-field.png")}>
                <ImageIcon className="h-4 w-4" /> خروجی PNG
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={async () => {
                  const ok = await copyText(summaryText());
                  if (ok) {
                    setCopied(true);
                    window.setTimeout(() => setCopied(false), 1200);
                  }
                }}
              >
                <Copy className="h-4 w-4" /> {copied ? "کپی شد" : "کپی خلاصه"}
              </Button>
            </div>
          </ResultStack>
        ) : null
      }
    />
  );
}
