/**
 * Field catalog — the single source of truth for every numeric input across
 * all pages. Each field declares its `unit` (which drives the percent-to-
 * decimal conversion in lib/units) plus its Persian label, unit suffix, valid
 * range and ⓘ tooltip (meaning + typical range + example), exactly as the
 * "Page template / Teaching aids" sections require.
 *
 * Ranges are expressed in the units the student types: percent fields carry
 * their UI-percent bounds; `money`/`number`/`count` carry raw bounds.
 */

import type { FieldUnit } from "@/lib/units";

export interface FieldDef {
  /** Wire (JSON) field name. */
  key: string;
  label: string;
  unit: FieldUnit;
  /** Display suffix; defaults to the unit's natural suffix (% for rates). */
  suffix?: string;
  min?: number;
  max?: number;
  step?: number;
  /** Bounds are strict (>) rather than inclusive (>=) — shown in tooltip. */
  exclusiveMin?: boolean;
  exclusiveMax?: boolean;
  allowNegative?: boolean;
  /** Decimal precision for the input (defaults: 4 for rates, 2 otherwise). */
  decimals?: number;
  tooltip: string;
}

/** Suffix default per unit (overridable per field). Money fields take their
 *  suffix from the settings money unit at render time (see FieldInput), so no
 *  unit is hardcoded here. */
export function defaultSuffix(unit: FieldUnit): string | undefined {
  switch (unit) {
    case "rate":
    case "percent-raw":
      return "%";
    default:
      return undefined;
  }
}

export function resolveField(def: FieldDef): Required<
  Pick<FieldDef, "key" | "label" | "unit" | "step" | "decimals">
> & { suffix?: string; min?: number; max?: number } {
  return {
    key: def.key,
    label: def.label,
    unit: def.unit,
    suffix: def.suffix ?? defaultSuffix(def.unit),
    min: def.min,
    max: def.max,
    step: def.step ?? (def.unit === "rate" || def.unit === "percent-raw" ? 0.5 : 1),
    decimals: def.decimals ?? (def.unit === "rate" || def.unit === "percent-raw" ? 4 : 2),
  };
}

const rate = (
  key: string,
  label: string,
  tooltip: string,
  extra: Partial<FieldDef> = {},
): FieldDef => ({ key, label, unit: "rate", tooltip, ...extra });

const money = (
  key: string,
  label: string,
  tooltip: string,
  extra: Partial<FieldDef> = {},
): FieldDef => ({ key, label, unit: "money", tooltip, ...extra });

/** Catalog of reusable fields keyed by a stable id. */
export const F: Record<string, FieldDef> = {
  // Dividends & prices
  d0: money("d0", "سود تقسیمی فعلی (D₀)", "آخرین سود تقسیمی پرداختی. مثال: ۱٫۵"),
  d1: money("d1", "سود تقسیمی مورد انتظار (D₁)", "سود تقسیمی پایان سال آینده. مثال: ۲"),
  d: money("d", "سود تقسیمی ثابت (D)", "سود تقسیمی سالانهٔ ثابت. مثال: ۵"),
  p0: money("p0", "قیمت فعلی سهام (P₀)", "قیمت کنونی سهم. مثال: ۵۰"),
  p1: money("p1", "قیمت مورد انتظار پایان سال (P₁)", "قیمت انتظاری سهم در پایان سال. مثال: ۵۵"),
  price: money("price", "قیمت سهام (P)", "قیمت کنونی سهم. مثال: ۵۰"),
  dividend: money("dividend", "سود تقسیمی سالانه", "سود تقسیمی سالانه. مثال: ۳"),

  // Earnings & value
  eps: money("eps", "سود هر سهم (EPS)", "سود خالص به‌ازای هر سهم. مثال: ۴"),
  npvgo: money("npvgo", "ارزش فعلی خالص فرصت‌های رشد (NPVGO)", "ارزش فرصت‌های رشد؛ می‌تواند منفی باشد. مثال: ۱۰", { allowNegative: true }),

  // Rates (decimal on the wire)
  r: rate("r", "نرخ بازده مورد انتظار (r)", "نرخ بازده موردانتظار به درصد. مثال: ۱۲٪. باید از نرخ رشد حداقل ۰٫۵ واحد درصد بیشتر باشد.", { min: 0, exclusiveMin: true }),
  required_return: rate("required_return", "نرخ بازده مورد انتظار (r)", "بازده مورد انتظار سهام به درصد. مثال: ۱۲٪.", { min: 0, exclusiveMin: true }),
  g: rate("g", "نرخ رشد (g)", "نرخ رشد سود/درآمد به درصد. بازهٔ دامنه: ۰ تا ۲۰۰٪. مثال: ۵٪.", { min: 0, max: 200 }),
  g_constant: rate("g_constant", "نرخ رشد ثابت پس از دوره غیرعادی", "رشد دائمی پس از دورهٔ غیرعادی به درصد. مثال: ۵٪.", { min: 0, max: 200 }),
  roe: rate("roe", "بازده حقوق صاحبان سهام (ROE)", "ROE به درصد؛ حداکثر ۲۰۰٪. مثال: ۱۵٪.", { min: 0, max: 200, exclusiveMin: true }),
  retention_ratio: rate("retention_ratio", "نسبت نگهداری سود (b)", "سهمی از سود که نگهداری می‌شود؛ ۰ تا زیر ۱۰۰٪. مثال: ۶۰٪.", { min: 0, max: 100, exclusiveMax: true }),
  payout_ratio: rate("payout_ratio", "نسبت تقسیم سود", "سهمی از سود که تقسیم می‌شود؛ ۰ تا ۱۰۰٪.", { min: 0, max: 100 }),

  // CAPM / cost of capital
  beta: { key: "beta", label: "ضریب بتا (β)", unit: "number", step: 0.05, decimals: 2, tooltip: "حساسیت سهم به بازار. مثال: ۱٫۲." } as FieldDef,
  risk_free_rate: rate("risk_free_rate", "نرخ بدون ریسک (r_f)", "بازده دارایی بدون ریسک به درصد. مثال: ۴٪.", { min: 0, exclusiveMin: true }),
  market_return: rate("market_return", "بازده مورد انتظار بازار (r_m)", "بازده بازار به درصد؛ باید از نرخ بدون ریسک بیشتر باشد. مثال: ۱۲٪.", { min: 0, exclusiveMin: true }),
  cost_of_equity: rate("cost_of_equity", "هزینه حقوق صاحبان سهام (r_e)", "بازده مورد انتظار سهامداران به درصد. مثال: ۱۲٪.", { min: 0, exclusiveMin: true }),
  cost_of_debt: rate("cost_of_debt", "هزینه بدهی قبل از مالیات (r_d)", "نرخ بهرهٔ بدهی به درصد. مثال: ۶٪.", { min: 0 }),
  tax_rate: rate("tax_rate", "نرخ مالیات (t)", "نرخ مالیات شرکت؛ ۰ تا زیر ۱۰۰٪. مثال: ۲۵٪.", { min: 0, max: 100, exclusiveMax: true }),

  // Raw-percent exceptions (NOT divided by 100)
  bond_rate_percent: { key: "bond_rate_percent", label: "نرخ اوراق قرضه", unit: "percent-raw", tooltip: "نرخ اوراق قرضه به درصد؛ مستقیم ارسال می‌شود (۸ یعنی ۸٪). مثال: ۸.", min: 0, exclusiveMin: true } as FieldDef,
  growth_rate_percent: { key: "growth_rate_percent", label: "نرخ رشد سالانه سود", unit: "percent-raw", tooltip: "رشد سود به درصد؛ مستقیم ارسال می‌شود (۱۰ یعنی ۱۰٪). بازه: ۰ تا ۱۰۰. مثال: ۱۰.", min: 0, max: 100, exclusiveMin: true } as FieldDef,

  // Ratios / multiples (plain numbers)
  pe_ratio: { key: "pe_ratio", label: "نسبت قیمت به سود (P/E)", unit: "number", step: 0.1, decimals: 2, tooltip: "ضریب P/E. مثال: ۱۵." } as FieldDef,

  // Counts
  years: { key: "years", label: "تعداد سال‌ها", unit: "count", suffix: "سال", min: 1, max: 50, step: 1, decimals: 0, tooltip: "تعداد سال‌های پیش‌بینی: ۱ تا ۵۰." } as FieldDef,
  periods: { key: "periods", label: "تعداد دوره‌ها", unit: "count", suffix: "دوره", min: 1, max: 50, step: 1, decimals: 0, tooltip: "تعداد دوره‌های پیش‌بینی سود (۱ تا ۵۰)." } as FieldDef,
  shares_outstanding: { key: "shares_outstanding", label: "تعداد سهام", unit: "count", suffix: "سهم", min: 0, exclusiveMin: true, step: 1, decimals: 0, tooltip: "تعداد سهام منتشرشده. مثال: ۱۰۰۰." } as FieldDef,

  // Balance sheet (money)
  cash: money("cash", "موجودی نقد", "نقد و معادل‌های آن. مثال: ۵۰.", { min: 0 }),
  debt: money("debt", "بدهی بهره‌دار", "بدهی بهره‌دار؛ صفر مجاز است. مثال: ۲۰۰.", { min: 0 }),
  minority_interest: money("minority_interest", "منافع اقلیت", "حقوق صاحبان سهام اقلیت. مثال: ۰.", { min: 0 }),
  preferred_equity: money("preferred_equity", "سهام ممتاز", "ارزش سهام ممتاز. مثال: ۰.", { min: 0 }),
  market_price: money("market_price", "قیمت بازار", "قیمت جاری سهم در بازار. مثال: ۱۳۰.", { min: 0, exclusiveMin: true }),
  equity: money("equity", "ارزش بازار حقوق صاحبان سهام (E)", "ارزش بازار سهام. مثال: ۶۰۰.", { min: 0, exclusiveMin: true }),

  // DCF / forecast rates & fields
  wacc: rate("wacc", "نرخ WACC", "نرخ تنزیل به درصد؛ باید از رشد پایانی حداقل ۰٫۵ واحد درصد بیشتر باشد. مثال: ۹٪.", { min: 0, exclusiveMin: true }),
  terminal_growth: rate("terminal_growth", "نرخ رشد پایانی (g)", "رشد دائمی ارزش انتهای دوره به درصد. مثال: ۳٪.", { min: 0, max: 200 }),
  base_revenue: money("base_revenue", "درآمد پایه", "آخرین درآمد تاریخی (مثبت). مثال: ۸۰۰.", { min: 0, exclusiveMin: true }),
  revenue_growth: rate("revenue_growth", "نرخ رشد درآمد", "رشد درآمد هر سال به درصد؛ بیشتر از ۱۰۰−٪ تا ۲۰۰٪. مثال: ۲۵٪.", { min: -100, max: 200, allowNegative: true }),
  ebitda_margin: rate("ebitda_margin", "حاشیه EBITDA", "حاشیه سود عملیاتی؛ ۰ تا ۱۰۰٪. مثال: ۵۰٪.", { min: 0, max: 100 }),
  da_pct_revenue: rate("da_pct_revenue", "استهلاک به درآمد", "نسبت استهلاک به درآمد؛ ۰ تا ۱۰۰٪. مثال: ۱۲٫۵٪.", { min: 0, max: 100 }),
  capex_pct_revenue: rate("capex_pct_revenue", "مخارج سرمایه‌ای به درآمد", "نسبت Capex به درآمد؛ ۰ تا ۱۰۰٪. مثال: ۲۵٪.", { min: 0, max: 100 }),
  nwc_pct_incremental_revenue: rate("nwc_pct_incremental_revenue", "سرمایه در گردش به درآمد افزایشی", "نسبت ΔNWC به درآمد افزایشی؛ ۰ تا ۱۰۰٪. مثال: ۵۰٪.", { min: 0, max: 100 }),

  // Sensitivity grid
  wacc_step: rate("wacc_step", "گام محور WACC", "فاصله نقاط محور WACC به درصد؛ مثبت. پیش‌فرض ۱٪.", { min: 0, exclusiveMin: true, step: 0.1 }),
  growth_step: rate("growth_step", "گام محور رشد پایانی", "فاصله نقاط محور رشد به درصد؛ مثبت. پیش‌فرض ۰٫۵٪.", { min: 0, exclusiveMin: true, step: 0.1 }),
  wacc_points: { key: "wacc_points", label: "تعداد نقاط WACC", unit: "count", min: 3, max: 11, step: 2, decimals: 0, tooltip: "تعداد نقاط فرد محور WACC: ۳ تا ۱۱." } as FieldDef,
  growth_points: { key: "growth_points", label: "تعداد نقاط رشد", unit: "count", min: 3, max: 11, step: 2, decimals: 0, tooltip: "تعداد نقاط فرد محور رشد پایانی: ۳ تا ۱۱." } as FieldDef,

  // Portfolio
  risk_aversion: { key: "risk_aversion", label: "ریسک‌گریزی (A)", unit: "number", step: 0.5, decimals: 2, min: 0, exclusiveMin: true, tooltip: "ضریب ریسک‌گریزی؛ باید مثبت باشد. مثال: ۴." } as FieldDef,
  max_leverage: { key: "max_leverage", label: "حداکثر اهرم", unit: "number", step: 0.1, decimals: 2, min: 0, max: 3, tooltip: "سقف وزن سبد مماس؛ ۰ تا ۳. مثال: ۱." } as FieldDef,
  frontier_points: { key: "frontier_points", label: "تعداد نقاط مرز کارا", unit: "count", min: 5, max: 200, step: 1, decimals: 0, tooltip: "تعداد نقاط مرز کارا: ۵ تا ۲۰۰." } as FieldDef,
};
