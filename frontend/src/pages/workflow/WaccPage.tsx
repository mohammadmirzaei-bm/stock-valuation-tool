import * as React from "react";
import { Calculator, Wrench } from "lucide-react";
import { ModelPage } from "@/components/model/ModelPage";
import { Hero, ComponentCards } from "@/components/model/ResultParts";
import { Donut } from "@/components/charts/Basic";
import { CopyButton } from "@/components/common/ExportButtons";
import { NumberField } from "@/components/model/NumberField";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Button } from "@/components/ui/button";
import { F } from "@/config/fields";
import { postWacc, postCapm } from "@/api/endpoints";
import type { WaccRequest, WaccResult, CapmRequest, CapmResult } from "@/api/types";
import { WACC_SAMPLE } from "@/lib/samples";
import { useAutoQuery } from "@/hooks/useAutoQuery";
import { useWorkflow } from "@/store/workflow";
import { useFormat } from "@/hooks/useFormat";
import type { UseValuationResult } from "@/hooks/useValuation";

/** CAPM helper: a small popover that calls /capm and fills cost of equity. */
function CapmHelper({ onFill }: { onFill: (requiredReturnPercent: number) => void }) {
  const fmt = useFormat();
  const [open, setOpen] = React.useState(false);
  const [rf, setRf] = React.useState(4);
  const [beta, setBeta] = React.useState(1.2);
  const [rm, setRm] = React.useState(10);

  const ready = rf >= 0 && beta > 0 && rm > rf;
  const body: CapmRequest | null = ready ? { risk_free_rate: rf / 100, beta, market_return: rm / 100 } : null;
  const query = useAutoQuery<CapmResult>("capm-helper", body, postCapm, ready);
  const value = query.data?.required_return_percent;

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button type="button" variant="outline" size="sm">
          <Calculator className="h-4 w-4" />
          کمک CAPM
        </Button>
      </PopoverTrigger>
      <PopoverContent className="space-y-3">
        <div className="text-sm font-medium">محاسبهٔ هزینهٔ سهام با CAPM</div>
        <NumberField label="نرخ بدون ریسک" suffix="٪" value={rf} onChange={(v) => setRf(v ?? 0)} min={0} />
        <NumberField label="بتا" value={beta} onChange={(v) => setBeta(v ?? 0)} min={0} step={0.05} />
        <NumberField label="بازده بازار" suffix="٪" value={rm} onChange={(v) => setRm(v ?? 0)} min={0} />
        {query.error && <div className="text-xs text-negative">مقادیر نامعتبر</div>}
        <div className="flex items-center justify-between">
          <span className="num text-sm text-muted-foreground">{value !== undefined ? fmt.percent(value) : "—"}</span>
          <Button type="button" size="sm" disabled={value === undefined} onClick={() => { if (value !== undefined) { onFill(value); setOpen(false); } }}>
            <Wrench className="h-4 w-4" />
            پر کردن هزینهٔ سهام
          </Button>
        </div>
      </PopoverContent>
    </Popover>
  );
}

export function WaccPage() {
  const fmt = useFormat();
  const useInDcf = useWorkflow((s) => s.useInDcf);

  return (
    <ModelPage<WaccResult>
      pageKey="wacc"
      title="گام ۲: میانگین موزون هزینهٔ سرمایه (WACC)"
      formula="WACC = (E/V)·rₑ + (D/V)·r_d·(1 − t)"
      whenSuitable="ساختار سرمایه و هزینه‌ها را وارد کنید تا نرخ تنزیل برای DCF ساخته شود."
      howToRead="وزن‌ها نسبت سهام و بدهی به کل سرمایه‌اند. هزینهٔ بدهی پس از کسر سپر مالیاتی در WACC وارد می‌شود."
      fields={[F.equity, F.debt, F.cost_of_equity, F.cost_of_debt, F.tax_rate]}
      endpoint="wacc"
      call={(body, signal) => postWacc(body as WaccRequest, signal)}
      sample={WACC_SAMPLE}
      inputExtras={(v: UseValuationResult<WaccResult>) => (
        <CapmHelper onFill={(pct) => v.form.setValue("cost_of_equity", pct, { shouldValidate: true })} />
      )}
      renderResult={(res) => (
        <>
          <Hero label="WACC" value={fmt.percent(res.wacc_percent)} />
          <Donut
            data={[
              { name: "سهام", value: res.equity_weight_percent },
              { name: "بدهی", value: res.debt_weight_percent },
            ]}
            summary={`وزن سهام ${fmt.percent(res.equity_weight_percent)} و بدهی ${fmt.percent(res.debt_weight_percent)}.`}
          />
          <ComponentCards
            items={[
              { label: "هزینهٔ بدهی پس از مالیات", value: fmt.percent(res.after_tax_cost_of_debt_percent) },
              { label: "کل سرمایه", value: fmt.number(res.total_capital) },
            ]}
          />
        </>
      )}
      renderActions={(res) => (
        <div className="flex flex-wrap items-center gap-2">
          <Button type="button" size="sm" onClick={() => useInDcf(res.wacc_percent)}>
            استفاده در DCF
          </Button>
          <CopyButton getText={() => `WACC = ${res.wacc_percent}`} label="کپی WACC" />
        </div>
      )}
    />
  );
}
