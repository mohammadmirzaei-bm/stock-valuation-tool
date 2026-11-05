/**
 * Shared workflow store (spec "Shared workflow state").
 *
 * One client-side store holds the forecast rows, WACC, balance-sheet fields,
 * market price and the collected football-field ranges. Every workflow page
 * reads from and writes back to it. It is persisted to localStorage so a
 * refresh never loses a student's work, and a "Reset workflow" action clears it.
 *
 * Fields that flow from an earlier step carry a source chip ("From step 1 ✓").
 * Overriding such a field keeps the value but detaches it from the store, so
 * the chip disappears and later upstream updates no longer overwrite the
 * student's manual edit.
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { CashFlowProjectionInput } from "@/api/types";
import {
  BALANCE_SHEET_SAMPLE,
  FORECAST_SAMPLE,
  FOOTBALL_SAMPLE,
  REFERENCE_PROJECTIONS,
  type ForecastSample,
} from "@/lib/samples";

/** WACC sample output is 9.00% (600 / 400 / 12% / 6% / 25%). */
const SAMPLE_WACC_PERCENT = 9;

/** Balance-sheet + share fields, all in UI units (tax as percent). */
export interface BalanceSheet {
  cash: number;
  debt: number;
  minorityInterest: number;
  preferredEquity: number;
  sharesOutstanding: number;
  taxRate: number; // percent
}

/** A football-field range plus where it came from (for the source chips). */
export interface FootballRange {
  method: string;
  low: number;
  mid: number;
  high: number;
  source?: string;
}

export type StepId =
  | "forecast"
  | "wacc"
  | "dcf"
  | "scenarios"
  | "sensitivity"
  | "reverse"
  | "multiples"
  | "football";

interface WorkflowState {
  // Step 1 — forecast
  forecastInputs: ForecastSample | null;
  projections: CashFlowProjectionInput[] | null;
  projectionsDetached: boolean; // true once edited by hand after "Send to DCF"

  // Step 2 — WACC
  waccPercent: number | null;
  waccDetached: boolean;

  // Shared company data
  balanceSheet: BalanceSheet;
  marketPrice: number | null;

  // Step 6 — collected ranges
  ranges: FootballRange[];

  completed: Record<StepId, boolean>;

  // actions
  setForecastInputs: (inputs: ForecastSample) => void;
  sendToDcf: (rows: CashFlowProjectionInput[]) => void;
  overrideProjections: (rows: CashFlowProjectionInput[]) => void;

  useInDcf: (waccPercent: number) => void;
  overrideWacc: (waccPercent: number) => void;

  setBalanceSheet: (patch: Partial<BalanceSheet>) => void;
  setMarketPrice: (value: number | null) => void;

  upsertRange: (range: FootballRange) => void;
  removeRange: (method: string) => void;

  completeStep: (step: StepId) => void;
  loadSample: () => void;
  reset: () => void;
}

const EMPTY_BALANCE: BalanceSheet = {
  cash: 0,
  debt: 0,
  minorityInterest: 0,
  preferredEquity: 0,
  sharesOutstanding: 0,
  taxRate: 25,
};

const emptyCompleted = (): Record<StepId, boolean> => ({
  forecast: false,
  wacc: false,
  dcf: false,
  scenarios: false,
  sensitivity: false,
  reverse: false,
  multiples: false,
  football: false,
});

export const useWorkflow = create<WorkflowState>()(
  persist(
    (set, get) => ({
      forecastInputs: null,
      projections: null,
      projectionsDetached: false,
      waccPercent: null,
      waccDetached: false,
      balanceSheet: EMPTY_BALANCE,
      marketPrice: null,
      ranges: [],
      completed: emptyCompleted(),

      setForecastInputs: (inputs) => set({ forecastInputs: inputs }),

      sendToDcf: (rows) =>
        set({ projections: rows, projectionsDetached: false, completed: { ...get().completed, forecast: true } }),

      overrideProjections: (rows) => set({ projections: rows, projectionsDetached: true }),

      useInDcf: (waccPercent) =>
        set({ waccPercent, waccDetached: false, completed: { ...get().completed, wacc: true } }),

      overrideWacc: (waccPercent) => set({ waccPercent, waccDetached: true }),

      setBalanceSheet: (patch) => set({ balanceSheet: { ...get().balanceSheet, ...patch } }),
      setMarketPrice: (value) => set({ marketPrice: value }),

      upsertRange: (range) => {
        const others = get().ranges.filter((r) => r.method !== range.method);
        set({ ranges: [...others, range] });
      },
      removeRange: (method) => set({ ranges: get().ranges.filter((r) => r.method !== method) }),

      completeStep: (step) => set({ completed: { ...get().completed, [step]: true } }),

      loadSample: () =>
        set({
          forecastInputs: FORECAST_SAMPLE,
          projections: REFERENCE_PROJECTIONS,
          projectionsDetached: false,
          waccPercent: SAMPLE_WACC_PERCENT,
          waccDetached: false,
          balanceSheet: {
            cash: BALANCE_SHEET_SAMPLE.cash,
            debt: BALANCE_SHEET_SAMPLE.debt,
            minorityInterest: BALANCE_SHEET_SAMPLE.minority_interest,
            preferredEquity: BALANCE_SHEET_SAMPLE.preferred_equity,
            sharesOutstanding: BALANCE_SHEET_SAMPLE.shares_outstanding,
            taxRate: BALANCE_SHEET_SAMPLE.tax_rate,
          },
          marketPrice: FOOTBALL_SAMPLE.market_price,
          ranges: FOOTBALL_SAMPLE.ranges.map((r) => ({ ...r, source: "نمونه" })),
          completed: { ...emptyCompleted(), forecast: true, wacc: true, dcf: true },
        }),

      reset: () =>
        set({
          forecastInputs: null,
          projections: null,
          projectionsDetached: false,
          waccPercent: null,
          waccDetached: false,
          balanceSheet: EMPTY_BALANCE,
          marketPrice: null,
          ranges: [],
          completed: emptyCompleted(),
        }),
    }),
    { name: "sv-workflow" },
  ),
);
