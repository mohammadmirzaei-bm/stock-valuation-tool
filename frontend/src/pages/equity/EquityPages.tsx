import * as React from "react";
import { useWatch, type Control } from "react-hook-form";
import { ModelPage } from "@/components/model/ModelPage";
import { Hero, ComponentCards } from "@/components/model/ResultParts";
import { InsightCallout } from "@/components/model/InsightCallout";
import { CopyButton } from "@/components/common/ExportButtons";
import { Badge } from "@/components/ui/badge";
import { BarSeriesChart, LineChart } from "@/components/charts/Basic";
import { SecurityMarketLine, type SmlPoint } from "@/components/charts/SecurityMarketLine";
import { chartColors } from "@/components/charts/theme";
import { FieldInput } from "@/components/model/FieldInput";
import { EQUITY_META } from "@/config/models";
import { F } from "@/config/fields";
import { useFormat, type FormatApi } from "@/hooks/useFormat";
import { useAutoQuery } from "@/hooks/useAutoQuery";
import { toWire } from "@/lib/units";
import type { FormValues } from "@/lib/request";
import type { ValidationOptions } from "@/lib/validation";
import type {
  CapmResult,
  DividendProjectionRequest,
  DividendProjectionResult,
  SupernormalScheduleRow,
} from "@/api/types";
import { pegLevelView, toneSurface, toneText } from "@/lib/semantics";
import { cn } from "@/lib/utils";
import * as E from "@/api/endpoints";

/**
 * One registry row as {@link EquityPage} consumes it: the result type is erased
 * because the page only forwards it to the matching `render`. Callers never
 * write an entry in this shape — they call {@link defineEntry}, which keeps the
 * endpoint's generated request/result types on `result`/`actions`.
 */
interface Entry {
  endpoint: string;
  call: (body: unknown, signal?: AbortSignal) => Promise<unknown>;
  sample: FormValues;
  render: (res: unknown, values: FormValues, fmt: FormatApi) => React.ReactNode;
  validation?: ValidationOptions;
  buildBody?: (values: FormValues) => unknown;
  inputExtras?: (args: { control: Control<FormValues>; values: FormValues }) => React.ReactNode;
  actions?: (res: unknown, fmt: FormatApi) => React.ReactNode;
  howToRead?: string;
}

/** An entry authored against one endpoint, so `res` is its real result type. */
interface EntryConfig<Req, Res> extends Omit<Entry, "call" | "render" | "actions"> {
  call: (body: Req, signal?: AbortSignal) => Promise<Res>;
  result: (res: Res, values: FormValues, fmt: FormatApi) => React.ReactNode;
  actions?: (res: Res, fmt: FormatApi) => React.ReactNode;
}

/**
 * Type an entry from the endpoint function itself: `Req`/`Res` are inferred from
 * `call`, so every `result`/`actions` body is checked against the generated
 * request/result types. The two casts below are the only place the result type
 * is erased, and they are safe because the route picks `render` from the same
 * entry that produced the response.
 */
function defineEntry<Req, Res>(cfg: EntryConfig<Req, Res>): Entry {
  return {
    endpoint: cfg.endpoint,
    call: (body, signal) => cfg.call(body as Req, signal),
    sample: cfg.sample,
    render: (res, values, fmt) => cfg.result(res as Res, values, fmt),
    validation: cfg.validation,
    buildBody: cfg.buildBody,
    inputExtras: cfg.inputExtras,
    actions: cfg.actions ? (res, fmt) => cfg.actions!(res as Res, fmt) : undefined,
    howToRead: cfg.howToRead,
  };
}

/** Per-year growth-rate inputs for the supernormal model. */
function GrowthRateList({ control }: { control: Control<FormValues> }) {
  const years = useWatch({ control, name: "years" }) as number | undefined;
  const n = Math.min(Math.max(years ?? 0, 0), 50);
  return (
    <div className="space-y-3">
      <div className="text-sm font-medium text-foreground">نرخ رشد هر سال دورهٔ غیرعادی (٪)</div>
      {Array.from({ length: n }, (_, i) => (
        <FieldInput
          key={i}
          control={control}
          field={{ ...F.g, key: `growth_${i}`, label: `سال ${i + 1}` }}
        />
      ))}
    </div>
  );
}

const copy = (label: string, text: () => string) => <CopyButton getText={text} label={label} />;

/** SML chart heading (spec term: security market line). */
export const SML_LABEL = "خط بازار اوراق بهادار (SML)";

type CapmSmlFields = Pick<
  CapmResult,
  "beta" | "risk_free_rate_percent" | "market_return_percent" | "required_return_percent"
>;

/** The three SML points on a numeric beta axis: β=0 (r_f), β=1 (r_m), β=stock (r). */
export function capmSmlPoints(res: CapmSmlFields, marketReturnFallback: number): SmlPoint[] {
  return [
    { beta: 0, ret: res.risk_free_rate_percent, label: "r_f" },
    { beta: 1, ret: res.market_return_percent ?? marketReturnFallback, label: "r_m" },
    { beta: res.beta, ret: res.required_return_percent, label: "سهم" },
  ];
}

/**
 * Body for the Gordon companion dividend chart: the same D₀ and g the student
 * typed, projected 10 years. The growth rate goes through the shared unit layer
 * (percent → decimal), never a hand-written ÷100. Null until both inputs exist.
 */
export function gordonDividendBody(
  d0: number | undefined,
  gPercent: number | undefined,
): DividendProjectionRequest | null {
  if (d0 === undefined || gPercent === undefined) return null;
  return { d0, g: toWire(F.g.unit, gPercent), periods: 10 };
}

/** Gordon companion: the 10-year dividend path with the same D₀ and g. */
function GordonDividendChart({ d0, gPercent, fmt }: { d0?: number; gPercent?: number; fmt: FormatApi }) {
  const body = React.useMemo(() => gordonDividendBody(d0, gPercent), [d0, gPercent]);
  const query = useAutoQuery<DividendProjectionResult>("gordon-dividends", body, E.postDividendProjection, body !== null);
  const divs = query.data?.dividends ?? [];
  if (!body || divs.length === 0) return null;
  return (
    <div className="card-surface p-3">
      <div className="mb-1 text-sm font-medium text-foreground">مسیر سود تقسیمی ۱۰ ساله</div>
      <p className="mb-2 text-xs text-muted-foreground">با همان D₀ و gِ مدل گوردون؛ رشد سالانهٔ سود تقسیمی را نشان می‌دهد.</p>
      <LineChart
        categories={divs.map((_, i) => fmt.number(i + 1))}
        series={[{ name: "Dₜ", data: divs }]}
        yName="سود تقسیمی"
        height={240}
        summary={`سود تقسیمی ۱۰ سال آینده با رشد ثابت: از ${fmt.number(divs[0])} تا ${fmt.number(divs[divs.length - 1])}.`}
      />
    </div>
  );
}

export const ENTRIES: Record<string, Entry> = {
  "single-period": defineEntry({
    endpoint: "single-period",
    call: E.postSinglePeriod,
    sample: { d1: 1.0, p1: 50.0, r: 10 },
    result: (res, _v, fmt) => (
      <>
        <Hero label="قیمت فعلی (P₀)" value={fmt.number(res.p0)} />
        <BarSeriesChart
          categories={["ترکیب P₀"]}
          stacked
          series={[
            { name: "ارزش فعلی سود", data: [res.pv_dividend], color: chartColors().primary },
            { name: "ارزش فعلی قیمت", data: [res.pv_terminal_price], color: chartColors().warning },
          ]}
          valueLabel={(x) => fmt.number(x as number)}
          summary={`تفکیک P₀ به سود (${fmt.number(res.pv_dividend)}) و قیمت پایانی (${fmt.number(res.pv_terminal_price)}).`}
        />
      </>
    ),
    actions: (res, fmt) => copy("کپی P₀", () => `P₀ = ${fmt.number(res.p0)}`),
  }),
  "zero-growth": defineEntry({
    endpoint: "zero-growth",
    call: E.postZeroGrowth,
    sample: { d: 2.0, r: 8 },
    result: (res, _v, fmt) => (
      <>
        <Hero label="قیمت سهام (P)" value={fmt.number(res.price)} />
        <ComponentCards items={[{ label: "بازده سود تقسیمی", value: fmt.percent(res.dividend_yield_percent) }]} />
      </>
    ),
    actions: (res, fmt) => copy("کپی قیمت", () => `P = ${fmt.number(res.price)}`),
  }),
  "annual-dividend-yield": defineEntry({
    endpoint: "annual-dividend-yield",
    call: E.postAnnualDividendYield,
    sample: { dividend: 2.25, price: 25.0 },
    result: (res, _v, fmt) => <Hero label="بازده سالانه سود تقسیمی" value={fmt.percent(res.dividend_yield_percent)} />,
    actions: (res, fmt) => copy("کپی بازده", () => `${fmt.percent(res.dividend_yield_percent)}`),
  }),
  gordon: defineEntry({
    endpoint: "gordon",
    call: E.postGordon,
    sample: { d0: 1.5, g: 5, r: 12 },
    validation: { spread: [{ higher: "r", lower: "g" }] },
    howToRead:
      "قیمت، ارزش آتی سودهای تقسیمی با رشد ثابت است. مجموع بازده سود تقسیمی و بازده رشد سرمایه با نرخ بازده مورد انتظار برابر می‌شود.",
    result: (res, values, fmt) => (
      <>
        <Hero label="قیمت سهام (P)" value={fmt.number(res.price)} />
        <ComponentCards
          items={[
            { label: "بازده سود تقسیمی", value: fmt.percent(res.dividend_yield_percent) },
            { label: "بازده رشد سرمایه", value: fmt.percent(res.capital_gains_yield_percent) },
            { label: "D₁", value: fmt.number(res.d1) },
          ]}
        />
        <GordonDividendChart d0={values.d0} gPercent={values.g} fmt={fmt} />
      </>
    ),
    actions: (res) => copy("کپی قیمت", () => `P = ${res.price}`),
  }),
  supernormal: defineEntry({
    endpoint: "supernormal",
    call: E.postSupernormal,
    sample: { d0: 1.0, years: 3, g_constant: 5, r: 12, growth_0: 25, growth_1: 20, growth_2: 15 },
    validation: { spread: [{ higher: "r", lower: "g_constant" }] },
    inputExtras: ({ control }) => <GrowthRateList control={control} />,
    buildBody: (values) => {
      const years = values.years ?? 0;
      return {
        d0: values.d0,
        years,
        g_constant: (values.g_constant ?? 0) / 100,
        r: (values.r ?? 0) / 100,
        growth_rates: Array.from({ length: years }, (_, i) => (values[`growth_${i}`] ?? 0) / 100),
      };
    },
    result: (res, _v, fmt) => (
      <>
        <Hero label="قیمت فعلی (P₀)" value={fmt.number(res.p0)} />
        <BarSeriesChart
          categories={["ترکیب P₀"]}
          stacked
          series={[
            { name: "PV سودها", data: [res.pv_dividends_total], color: chartColors().primary },
            { name: "PV قیمت پایانی", data: [res.pv_p_terminal], color: chartColors().warning },
          ]}
          valueLabel={(x) => fmt.number(x as number)}
        />
        <ScheduleTable rows={res.schedule} fmt={fmt} />
      </>
    ),
    actions: (res) => copy("کپی P₀", () => `P₀ = ${res.p0}`),
  }),
  "dividend-projection": defineEntry({
    endpoint: "dividend-projection",
    call: E.postDividendProjection,
    sample: { d0: 1.0, g: 5, periods: 10 },
    result: (res, _v, fmt) => {
      const divs: number[] = res.dividends ?? [];
      return (
        <>
          <Hero label="آخرین سود تقسیمی پیش‌بینی‌شده" value={fmt.number(divs[divs.length - 1])} />
          <LineChart
            categories={divs.map((_, i) => fmt.number(i + 1))}
            series={[{ name: "Dₜ", data: divs }]}
            yName="سود تقسیمی"
            summary="نمودار رشد سود تقسیمی در دوره‌های آینده."
          />
        </>
      );
    },
  }),
  "expected-return": defineEntry({
    endpoint: "expected-return",
    call: E.postExpectedReturn,
    sample: { d1: 1.0, p0: 20.0, g: 10 },
    result: (res, _v, fmt) => (
      <>
        <Hero label="بازده کل مورد انتظار" value={fmt.percent(res.total_percent)} />
        <BarSeriesChart
          categories={["بازده کل"]}
          stacked
          series={[
            { name: "بازده سود تقسیمی", data: [res.dividend_yield_percent], color: chartColors().primary },
            { name: "بازده رشد سرمایه", data: [res.capital_gains_yield_percent], color: chartColors().warning },
          ]}
          valueLabel={(x) => fmt.percent(x as number)}
        />
      </>
    ),
    actions: (res, fmt) => copy("کپی بازده", () => fmt.percent(res.total_percent)),
  }),
  capm: defineEntry({
    endpoint: "capm",
    call: E.postCapm,
    sample: { risk_free_rate: 4, beta: 1.5, market_return: 10 },
    validation: { greaterThan: [{ greater: "market_return", smaller: "risk_free_rate" }] },
    result: (res, values, fmt) => (
      <>
        <Hero label="بازده مورد انتظار (r)" value={fmt.percent(res.required_return_percent)} />
        <ComponentCards
          items={[
            { label: "صرف ریسک بازار", value: fmt.percent(res.market_risk_premium_percent) },
            { label: "صرف ریسک سهام", value: fmt.percent(res.risk_premium_percent) },
          ]}
        />
        <div className="card-surface p-3">
          <div className="mb-2 text-sm font-medium text-foreground">{SML_LABEL}</div>
          <SecurityMarketLine
            points={capmSmlPoints(res, values.market_return ?? 0)}
            summary={`SML: نرخ بدون ریسک ${fmt.percent(res.risk_free_rate_percent)}، بازده بازار ${fmt.percent(res.market_return_percent ?? values.market_return)}، بازده سهم ${fmt.percent(res.required_return_percent)}.`}
          />
        </div>
      </>
    ),
  }),
  "preferred-stock": defineEntry({
    endpoint: "preferred-stock",
    call: E.postPreferredStock,
    sample: { d: 2.25, r: 9 },
    result: (res, _v, fmt) => (
      <>
        <Hero label="قیمت سهام ممتاز (P)" value={fmt.number(res.price)} />
        <ComponentCards items={[{ label: "بازده سود تقسیمی", value: fmt.percent(res.dividend_yield_percent) }]} />
      </>
    ),
    actions: (res, fmt) => copy("کپی قیمت", () => fmt.number(res.price)),
  }),
  "risk-premium": defineEntry({
    endpoint: "risk-premium",
    call: E.postRiskPremium,
    sample: { required_return: 9, bond_rate_percent: 8 },
    result: (res, _v, fmt) => (
      <>
        <Hero
          label="حق‌الریسک سهام"
          value={fmt.percent(res.risk_premium_percent)}
          tone={res.risk_premium_percent >= 0 ? "positive" : "negative"}
        />
        <BarSeriesChart
          categories={["بازده سهام", "نرخ اوراق قرضه"]}
          series={[{ name: "٪", data: [res.required_return_percent, res.bond_rate_percent] }]}
          valueLabel={(x) => fmt.percent(x as number)}
        />
      </>
    ),
  }),
  "growth-opportunities": defineEntry({
    endpoint: "growth-opportunities",
    call: E.postGrowthOpportunities,
    sample: { eps: 3.0, r: 10, npvgo: 5.0 },
    result: (res, _v, fmt) => (
      <>
        <Hero label="ارزش کل سهام" value={fmt.number(res.total_value)} />
        <ComponentCards items={[{ label: "سهم فرصت‌های رشد", value: fmt.percent(res.growth_share_percent) }]} />
        <BarSeriesChart
          categories={["ترکیب ارزش"]}
          stacked
          series={[
            { name: "ارزش بدون رشد", data: [res.no_growth_value], color: chartColors().primary },
            { name: "NPVGO", data: [res.npvgo], color: chartColors().positive },
          ]}
          valueLabel={(x) => fmt.number(x as number)}
        />
      </>
    ),
  }),
  "sustainable-growth": defineEntry({
    endpoint: "sustainable-growth",
    call: E.postSustainableGrowth,
    sample: { eps: 5.0, r: 12, roe: 15, retention_ratio: 40 },
    validation: { spread: [{ higher: "r", lower: "retention_ratio" }] },
    result: (res, _v, fmt) => {
      const curve = res.retention_curve ?? [];
      return (
        <>
          <Hero label="قیمت سهام (P)" value={fmt.number(res.price)} />
          <div className="space-y-2">
            <div className="flex">
              <Badge variant={res.growth_creates_value ? "positive" : "negative"}>
                {res.growth_creates_value ? "رشد ارزش‌آفرین است" : "رشد ارزش‌ساز نیست"}
              </Badge>
            </div>
            {!res.growth_creates_value && (
              <InsightCallout
                tone="warning"
                title="ROE کمتر از بازده مورد انتظار است"
                explanation="در این حالت نگهداری سود به‌جای افزودن به ارزش، آن را می‌کاهد."
              />
            )}
          </div>
          <ComponentCards
            items={[
              { label: "نسبت تقسیم سود", value: fmt.percent(res.payout_ratio_percent) },
              { label: "رشد پایدار", value: fmt.percent(res.sustainable_growth_percent) },
              { label: "NPVGO", value: fmt.number(res.npvgo) },
              { label: "P/E توجیه‌شده", value: fmt.number(res.justified_pe) },
            ]}
          />
          <div className="text-sm text-muted-foreground">منحنی نگهداری سود</div>
          <LineChart
            categories={curve.map((p) => fmt.percent(p.retention_ratio_percent))}
            series={[{ name: "قیمت", data: curve.map((p) => p.price) }]}
            yName="قیمت"
            summary="منحنی قیمت نسبت به نسبت نگهداری سود؛ نقاط نامعتبر به‌صورت فاصله نمایش داده می‌شوند."
          />
        </>
      );
    },
  }),
  peg: defineEntry({
    endpoint: "peg",
    call: E.postPeg,
    sample: { pe_ratio: 15.0, growth_rate_percent: 10 },
    result: (res, _v, fmt) => {
      const view = pegLevelView(res.interpretation?.level ?? "info");
      return (
        <>
          <Hero label="نسبت PEG" value={fmt.number(res.peg, { maxFractionDigits: 2 })} />
          <div className={cn("rounded-md border p-3 text-sm", toneSurface[view.tone])}>
            <div className={cn("mb-1 font-semibold", toneText[view.tone])}>{view.label}</div>
            <p>{res.interpretation?.message}</p>
          </div>
        </>
      );
    },
    actions: (res, fmt) => copy("کپی PEG", () => fmt.number(res.peg)),
  }),
};

/** Supernormal schedule table (terminal row highlighted). */
function ScheduleTable({ rows, fmt }: { rows: SupernormalScheduleRow[] | null | undefined; fmt: FormatApi }) {
  if (!rows?.length) return null;
  return (
    <div className="overflow-x-auto rounded-md border border-border">
      <table dir="ltr" className="ltr-table w-full text-table-num">
        <thead className="bg-muted text-muted-foreground">
          <tr>
            <th className="px-3 py-2 text-right">دوره</th>
            <th className="px-3 py-2">رشد ٪</th>
            <th className="px-3 py-2">سود</th>
            <th className="px-3 py-2">ارزش فعلی</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className={cn("border-b border-border", r.is_terminal && "bg-primary/10")}>
              <td className="px-3 py-1.5 text-right">{r.is_terminal ? "Pₙ" : r.period}</td>
              <td className="num px-3 py-1.5">{fmt.percent(r.growth_rate_percent)}</td>
              <td className="num px-3 py-1.5">{fmt.number(r.dividend)}</td>
              <td className="num px-3 py-1.5">{fmt.number(r.present_value)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function EquityPage({ id }: { id: string }) {
  const fmt = useFormat();
  const meta = EQUITY_META[id];
  const entry = ENTRIES[id];
  if (!meta || !entry) {
    return <div className="text-muted-foreground">مدل «{id}» یافت نشد.</div>;
  }
  return (
    <ModelPage<unknown>
      pageKey={id}
      title={meta.title}
      formula={meta.formula}
      whenSuitable={meta.whenSuitable}
      howToRead={entry.howToRead}
      fields={meta.fields}
      endpoint={entry.endpoint}
      call={entry.call}
      sample={entry.sample}
      validation={entry.validation}
      buildBody={entry.buildBody}
      inputExtras={entry.inputExtras ? (v) => entry.inputExtras!({ control: v.control, values: v.values }) : undefined}
      renderResult={(res, values) => entry.render(res, values, fmt)}
      renderActions={entry.actions ? (res) => entry.actions!(res, fmt) : undefined}
    />
  );
}
