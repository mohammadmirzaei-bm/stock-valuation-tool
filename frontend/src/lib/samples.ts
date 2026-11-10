/**
 * Reference sample inputs — every "Sample values" button and the Home
 * "Start with a sample" action reproduces the numbers used by the backend
 * tests (spec acceptance: samples must reproduce the reference results, e.g.
 * Gordon 1.5 / 5% / 12% -> 22.50; WACC 600 / 400 / 12% / 6% / 25% -> 9.00%).
 *
 * Rate fields are stored in UI-percent form (the form divides by 100 on send);
 * the two raw-percent exceptions and non-rate fields are stored as typed.
 */

import type { CashFlowProjectionInput } from "@/api/types";

/** The 5-year reference FCFF rows from `tests/domain/_fixtures.py`. */
export const REFERENCE_PROJECTIONS: CashFlowProjectionInput[] = [
  { ebit: 1000.0, depreciation: 200.0, capex: 250.0, delta_nwc: 50.0 },
  { ebit: 1100.0, depreciation: 210.0, capex: 260.0, delta_nwc: 55.0 },
  { ebit: 1200.0, depreciation: 220.0, capex: 270.0, delta_nwc: 60.0 },
  { ebit: 1300.0, depreciation: 230.0, capex: 280.0, delta_nwc: 65.0 },
  { ebit: 1400.0, depreciation: 240.0, capex: 290.0, delta_nwc: 70.0 },
];

export type FormValues = Record<string, number>;

/** Standalone equity samples (UI units; rates are percent). */
export const EQUITY_SAMPLES: Record<string, FormValues> = {
  "single-period": { d1: 1.0, p1: 50.0, r: 10 },
  "zero-growth": { d: 2.0, r: 8 },
  "annual-dividend-yield": { dividend: 2.25, price: 25.0 },
  gordon: { d0: 1.5, g: 5, r: 12 },
  // supernormal's per-year growth rates are assembled inline on its page.
  supernormal: { d0: 1.0, years: 3, g_constant: 5, r: 12 },
  "dividend-projection": { d0: 1.0, g: 5, periods: 10 },
  "expected-return": { d1: 1.0, p0: 20.0, g: 10 },
  capm: { risk_free_rate: 4, beta: 1.5, market_return: 10 },
  "preferred-stock": { d: 2.25, r: 9 },
  "risk-premium": { required_return: 9, bond_rate_percent: 8 },
  "growth-opportunities": { eps: 3.0, r: 10, npvgo: 5.0 },
  "sustainable-growth": { eps: 5.0, r: 12, roe: 15, retention_ratio: 40 },
  peg: { pe_ratio: 15.0, growth_rate_percent: 10 },
};

/** Forecast driver input can be a single value or a per-year list. */
export interface DriverInput {
  mode: "all" | "year";
  value: number;
  perYear: number[];
}

export interface ForecastSample {
  base_revenue: number;
  years: number;
  drivers: Record<
    "revenue_growth" | "ebitda_margin" | "da_pct_revenue" | "capex_pct_revenue" | "nwc_pct_incremental_revenue",
    DriverInput
  >;
  normalize_terminal_year: boolean;
  terminal_growth: number;
}

const flat = (value: number, years: number): DriverInput => ({
  mode: "all",
  value,
  perYear: Array.from({ length: years }, () => value),
});

/** Workflow-step 1 forecast sample (matches the /forecast route test). */
export const FORECAST_SAMPLE: ForecastSample = {
  base_revenue: 1024.0,
  years: 3,
  drivers: {
    revenue_growth: flat(25, 3),
    ebitda_margin: flat(50, 3),
    da_pct_revenue: flat(12.5, 3),
    capex_pct_revenue: flat(25, 3),
    nwc_pct_incremental_revenue: flat(50, 3),
  },
  normalize_terminal_year: false,
  terminal_growth: 2,
};

/** Workflow-step 2 WACC sample (-> 9.00%, weights 60/40). */
export const WACC_SAMPLE = {
  equity: 600.0,
  debt: 400.0,
  cost_of_equity: 12,
  cost_of_debt: 6,
  tax_rate: 25,
};

/** Shared balance-sheet + DCF sample (-> VPS 124.02, TV share 77.42%). */
export const BALANCE_SHEET_SAMPLE = {
  cash: 500.0,
  debt: 1500.0,
  minority_interest: 50.0,
  preferred_equity: 25.0,
  shares_outstanding: 100.0,
  tax_rate: 25,
};

export const DCF_SAMPLE = {
  wacc: 9,
  terminal_growth: 3,
  ...BALANCE_SHEET_SAMPLE,
  projections: REFERENCE_PROJECTIONS,
};

/** Scenario sample: bear / base / bull probabilities 25/50/25. */
export const SCENARIOS_SAMPLE = {
  scenarios: [
    { name: "bear", probability: 25, wacc: 11, terminal_growth: 2, projections: REFERENCE_PROJECTIONS },
    { name: "base", probability: 50, wacc: 9, terminal_growth: 3, projections: REFERENCE_PROJECTIONS },
    { name: "bull", probability: 25, wacc: 8.5, terminal_growth: 3.5, projections: REFERENCE_PROJECTIONS },
  ],
  ...BALANCE_SHEET_SAMPLE,
  market_price: 150.0,
};

export const SENSITIVITY_SAMPLE = {
  wacc: 9,
  terminal_growth: 3,
  wacc_step: 1,
  growth_step: 0.5,
  wacc_points: 5,
  growth_points: 5,
  ...BALANCE_SHEET_SAMPLE,
  projections: REFERENCE_PROJECTIONS,
};

export const REVERSE_SAMPLE = {
  wacc: 9,
  terminal_growth: 3, // analyst's own estimate (gap only)
  market_price: 150.0,
  ...BALANCE_SHEET_SAMPLE,
  projections: REFERENCE_PROJECTIONS,
};

export const MULTIPLES_SAMPLE = {
  kind: "ev_ebitda" as const,
  metric: 500.0,
  shares_outstanding: 10.0,
  peers: [
    { name: "الف", value: 10.0 },
    { name: "ب", value: 20.0 },
    { name: "ج", value: 30.0 },
    { name: "د", value: 40.0 },
  ],
  cash: 100.0,
  debt: 300.0,
  minority_interest: 50.0,
  preferred_equity: 50.0,
};

export const FOOTBALL_SAMPLE = {
  market_price: 150.0,
  ranges: [
    { method: "DCF", low: 100.0, mid: 150.0, high: 200.0 },
    { method: "Multiples", low: 120.0, mid: 140.0, high: 180.0 },
    { method: "Scenarios", low: 90.0, mid: 160.0, high: 210.0 },
  ],
};

export const PORTFOLIO_STATISTICS_SAMPLE = {
  assets: [
    { name: "الف", prices: [8.0, 12.0, 6.0, 6.0] },
    { name: "ب", prices: [8.0, 8.0, 12.0, 6.0] },
  ],
  periods_per_year: 1,
};

/** Optimizer sample: mean returns are UI percent; covariance stays raw. */
export const PORTFOLIO_OPTIMIZE_SAMPLE = {
  asset_names: ["الف", "ب"],
  mean_returns: [10, 20], // percent (wire 0.10 / 0.20)
  covariance: [
    [0.04, 0.0],
    [0.0, 0.16],
  ],
  risk_free_rate: 3, // percent
  risk_aversion: 3.0,
  allow_short: false,
  max_leverage: 1.0,
  frontier_points: 5,
};
