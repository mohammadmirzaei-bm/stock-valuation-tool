/**
 * Model registry / information architecture.
 *
 * Defines the guided-workflow steps (with their stepper order and optional
 * flags), the standalone-tool sidebar groups, and per-model metadata (Persian
 * title, LTR formula, "when is this suitable", input fields) used by the pages,
 * the sidebar, the stepper and the home flow diagram.
 */

import { F, type FieldDef } from "./fields";

export interface NavItem {
  id: string;
  label: string;
  path: string;
}

export interface StepItem extends NavItem {
  step: number;
  optional?: boolean;
}

/** Six-step guided workflow. Steps 2 (WACC) and 4 (Analyses) are optional. */
export const WORKFLOW_STEPS: StepItem[] = [
  { id: "forecast", label: "پیش‌بینی", path: "/forecast", step: 1 },
  { id: "wacc", label: "WACC", path: "/wacc", step: 2, optional: true },
  { id: "dcf", label: "DCF", path: "/dcf", step: 3 },
  { id: "analyses", label: "تحلیل‌ها", path: "/analyses", step: 4, optional: true },
  { id: "multiples", label: "ضریب همتایان", path: "/multiples", step: 5 },
  { id: "football", label: "زمین فوتبال", path: "/football-field", step: 6 },
];

/** The three step-4 analyses rendered as tabs on one page. */
export const ANALYSIS_TABS: NavItem[] = [
  { id: "scenarios", label: "سناریوها", path: "/analyses?tab=scenarios" },
  { id: "sensitivity", label: "حساسیت", path: "/analyses?tab=sensitivity" },
  { id: "reverse", label: "DCF معکوس", path: "/analyses?tab=reverse" },
];

export const EQUITY_GROUP: NavItem[] = [
  { id: "single-period", label: "تک‌دوره‌ای", path: "/equity/single-period" },
  { id: "zero-growth", label: "رشد صفر", path: "/equity/zero-growth" },
  { id: "gordon", label: "گوردون", path: "/equity/gordon" },
  { id: "supernormal", label: "رشد غیرعادی", path: "/equity/supernormal" },
  { id: "dividend-projection", label: "پیش‌بینی سود", path: "/equity/dividend-projection" },
  { id: "expected-return", label: "بازده مورد انتظار", path: "/equity/expected-return" },
  { id: "capm", label: "CAPM", path: "/equity/capm" },
  { id: "preferred-stock", label: "سهام ممتاز", path: "/equity/preferred-stock" },
  { id: "risk-premium", label: "حق‌الریسک", path: "/equity/risk-premium" },
  { id: "growth-opportunities", label: "فرصت‌های رشد", path: "/equity/growth-opportunities" },
  { id: "sustainable-growth", label: "رشد پایدار", path: "/equity/sustainable-growth" },
  { id: "peg", label: "PEG", path: "/equity/peg" },
  { id: "annual-dividend-yield", label: "بازده سالانه سود", path: "/equity/annual-dividend-yield" },
];

export const PORTFOLIO_GROUP: NavItem[] = [
  { id: "portfolio-statistics", label: "آماره از قیمت", path: "/portfolio/statistics" },
  { id: "portfolio-optimizer", label: "بهینه‌ساز", path: "/portfolio/optimize" },
];

/** Equity model metadata keyed by id; drives the generic result page inputs. */
export interface EquityMeta {
  title: string;
  formula: string;
  whenSuitable: string;
  fields: FieldDef[];
}

export const EQUITY_META: Record<string, EquityMeta> = {
  "single-period": {
    title: "مدل تک‌دوره‌ای",
    formula: "P₀ = (D₁ + P₁) / (1 + r)",
    whenSuitable: "برای ارزش‌گذاری سهم با افق یک‌ساله و سود و قیمت مورد انتظار مشخص.",
    fields: [F.d1, F.p1, F.r],
  },
  "zero-growth": {
    title: "مدل رشد صفر",
    formula: "P = D / r",
    whenSuitable: "برای سهمی با سود تقسیمی ثابت و بدون رشد (مانند سهام ممتاز).",
    fields: [F.d, F.r],
  },
  "annual-dividend-yield": {
    title: "بازده سالانه سود تقسیمی",
    formula: "Yield = (D / P) × 100",
    whenSuitable: "برای محاسبهٔ بازده نقدی سهم در قیمت فعلی.",
    fields: [F.dividend, F.price],
  },
  gordon: {
    title: "مدل رشد ثابت گوردون",
    formula: "P = D₀(1+g) / (r − g)",
    whenSuitable: "برای سهمی با رشد سود پایدار و ثابت در بلندمدت.",
    fields: [F.d0, F.g, F.r],
  },
  supernormal: {
    title: "مدل رشد غیرعادی چندمرحله‌ای",
    formula: "P₀ = Σ Dₜ/(1+r)ᵗ + Pₙ/(1+r)ⁿ",
    whenSuitable: "برای سهمی با دورهٔ رشد بالا سپس رشد پایدار ثابت.",
    fields: [F.d0, F.years, F.g_constant, F.r],
  },
  "dividend-projection": {
    title: "پیش‌بینی سود تقسیمی",
    formula: "Dₜ = D₀(1+g)ᵗ",
    whenSuitable: "برای نمایش مسیر سود تقسیمی در دوره‌های آینده.",
    fields: [F.d0, F.g, F.periods],
  },
  "expected-return": {
    title: "بازده مورد انتظار",
    formula: "r = (D₁ / P₀) + g",
    whenSuitable: "برای برآورد بازده کل سهم از سود، قیمت و رشد.",
    fields: [F.d1, F.p0, F.g],
  },
  capm: {
    title: "مدل CAPM",
    formula: "r = r_f + β(r_m − r_f)",
    whenSuitable: "برای محاسبهٔ نرخ بازده مورد انتظار با بتا و ریسک بازار.",
    fields: [F.risk_free_rate, F.beta, F.market_return],
  },
  "preferred-stock": {
    title: "ارزش‌گذاری سهام ممتاز",
    formula: "P = D / r",
    whenSuitable: "برای سهام ممتاز با سود ثابت و نامحدود.",
    fields: [F.d, F.r],
  },
  "risk-premium": {
    title: "حق‌الریسک سهام",
    formula: "RP = r − r_bond",
    whenSuitable: "برای مقایسهٔ بازده سهام با نرخ اوراق قرضهٔ مشابه.",
    fields: [F.required_return, F.bond_rate_percent],
  },
  "growth-opportunities": {
    title: "فرصت‌های رشد (NPVGO)",
    formula: "P = (EPS / r) + NPVGO",
    whenSuitable: "برای تفکیک ارزش بدون رشد و ارزش فرصت‌های رشد.",
    fields: [F.eps, F.r, F.npvgo],
  },
  "sustainable-growth": {
    title: "رشد پایدار",
    formula: "g = b × ROE ;  P = D₁ / (r − g)",
    whenSuitable: "برای استخراج رشد و NPVGO از ROE و نسبت نگهداری سود.",
    fields: [F.eps, F.r, F.roe, F.retention_ratio],
  },
  peg: {
    title: "نسبت PEG",
    formula: "PEG = (P/E) / g%",
    whenSuitable: "برای سنجش گران‌یا ارزانی سهم نسبت به رشد سود.",
    fields: [F.pe_ratio, F.growth_rate_percent],
  },
};
