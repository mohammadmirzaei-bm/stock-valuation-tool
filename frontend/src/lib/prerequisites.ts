/**
 * Prerequisite model for the guided workflow (spec "Shared workflow state").
 *
 * Five shared inputs gate a workflow result, each owned by the step that
 * provides it: forecast rows (step 1), WACC (step 2), and the balance-sheet /
 * market fields shares outstanding, tax rate and market price (step 3, the DCF
 * page). A page computes which of the prerequisites it depends on are missing
 * and hands them to <PrerequisiteChecklist>, which links to the providing step
 * — or, when that step is the page you are already on, focuses the inline field
 * instead of performing a misleading no-op navigation.
 */

export type PrereqKind = "forecast" | "wacc" | "shares" | "taxRate" | "marketPrice";

export interface PrereqMeta {
  /** Persian label shown in the checklist. */
  label: string;
  /** Step number that provides this input (for the "go to step N" button). */
  step: number;
  /** Route of the providing step. */
  path: string;
  /** id of the inline input on the providing page, focused when already there. */
  focusId: string;
}

export const PREREQ_META: Record<PrereqKind, PrereqMeta> = {
  forecast: { label: "سطرهای پیش‌بینی", step: 1, path: "/forecast", focusId: "prereq-forecast" },
  wacc: { label: "WACC (نرخ تنزیل)", step: 2, path: "/wacc", focusId: "prereq-wacc" },
  shares: { label: "تعداد سهام", step: 3, path: "/dcf", focusId: "prereq-shares" },
  taxRate: { label: "نرخ مالیات", step: 3, path: "/dcf", focusId: "prereq-tax" },
  marketPrice: { label: "قیمت بازار", step: 3, path: "/dcf", focusId: "prereq-market" },
};

/** Canonical display order: by providing step, then importance. */
const ORDER: PrereqKind[] = ["forecast", "wacc", "shares", "taxRate", "marketPrice"];

/** The current values a page checks its prerequisites against. */
export interface PrereqValues {
  forecast: readonly unknown[] | null | undefined;
  wacc: number | null | undefined;
  shares: number | null | undefined;
  taxRate: number | null | undefined;
  marketPrice: number | null | undefined;
}

const MISSING: Record<PrereqKind, (v: PrereqValues) => boolean> = {
  forecast: (v) => !v.forecast || v.forecast.length === 0,
  wacc: (v) => v.wacc == null || !(v.wacc > 0),
  shares: (v) => !(typeof v.shares === "number" && v.shares > 0),
  taxRate: (v) => !(typeof v.taxRate === "number" && v.taxRate >= 0 && v.taxRate < 100),
  marketPrice: (v) => v.marketPrice == null || !(v.marketPrice > 0),
};

/**
 * Which of the prerequisites a page `needs` are currently missing, in canonical
 * order. Pure so every page's checklist can be unit-tested in isolation.
 */
export function missingPrereqs(needs: readonly PrereqKind[], v: PrereqValues): PrereqKind[] {
  return ORDER.filter((k) => needs.includes(k) && MISSING[k](v));
}
