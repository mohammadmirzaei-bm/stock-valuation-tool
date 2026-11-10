/**
 * The request fragment shared by the DCF page and the three step-4 analyses
 * (scenarios, sensitivity, reverse). All four send the same company-level
 * inputs — forecast rows, WACC and the balance sheet — in wire units, so
 * building them here is what keeps the four call sites from drifting apart.
 *
 * Each caller adds only its own parameters on top (terminal growth, scenario
 * list, market price, grid steps). Readiness (rows present, WACC > 0, shares
 * outstanding > 0) is the caller's gate: the analyses only build a body once
 * their own `ready` check passed.
 */

import type { CashFlowProjectionInput } from "@/api/types";
import type { BalanceSheet } from "@/store/workflow";
import { F } from "@/config/fields";
import { toWire } from "@/lib/units";

/** The workflow-store fields {@link buildDcfBase} reads. */
export interface DcfBaseInput {
  projections: CashFlowProjectionInput[] | null;
  waccPercent: number | null;
  balanceSheet: BalanceSheet;
}

/** Wire-form DCF inputs (rates as decimals). */
export interface DcfBase {
  projections: CashFlowProjectionInput[];
  wacc: number;
  shares_outstanding: number;
  tax_rate: number;
  cash: number;
  debt: number;
  minority_interest: number;
  preferred_equity: number;
}

/** Build the shared DCF inputs from the workflow store (percent → decimal). */
export function buildDcfBase(wf: DcfBaseInput): DcfBase {
  const bs = wf.balanceSheet;
  return {
    projections: (wf.projections ?? []).map((r) => ({ ...r })),
    wacc: toWire(F.wacc.unit, wf.waccPercent ?? 0),
    shares_outstanding: bs.sharesOutstanding,
    tax_rate: toWire(F.tax_rate.unit, bs.taxRate),
    cash: bs.cash,
    debt: bs.debt,
    minority_interest: bs.minorityInterest,
    preferred_equity: bs.preferredEquity,
  };
}
