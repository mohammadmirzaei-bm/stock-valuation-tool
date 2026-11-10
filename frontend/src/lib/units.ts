/**
 * Centralized percent-to-decimal conversion.
 *
 * Spec (API contract, "read this section twice"): students type percent in the
 * UI, the API wants decimals (12% -> 0.12) for every rate field, EXCEPT two
 * fields that are already percent on the wire and must NOT be divided:
 *   - /risk-premium  -> bond_rate_percent
 *   - /peg           -> growth_rate_percent
 *
 * The distinction lives in the field's `unit`, so a new page cannot forget it:
 * a rate field declares `unit: "rate"` and is divided by 100 on send; the two
 * raw exceptions declare `unit: "percent-raw"` and pass through untouched.
 * Responses already carry `_percent` fields for display — the client never
 * multiplies on the way back.
 */

export type FieldUnit =
  | "rate" // UI shows percent; wire is decimal (divide by 100)
  | "percent-raw" // UI shows percent; wire is the raw number (no divide)
  | "number" // plain numeric (beta, P/E, prices)
  | "money" // currency amount (ریال)
  | "count"; // integer count (shares, years, grid points)

/** Convert a single UI value into the value sent on the wire. */
export function toWire(unit: FieldUnit, value: number): number {
  switch (unit) {
    case "rate":
      return value / 100;
    case "percent-raw":
    case "number":
    case "money":
    case "count":
      return value;
  }
}

/** Inverse of {@link toWire}: map a wire value back to its UI (percent) form. */
export function fromWire(unit: FieldUnit, value: number): number {
  switch (unit) {
    case "rate":
      return value * 100;
    case "percent-raw":
    case "number":
    case "money":
    case "count":
      return value;
  }
}

/** Whether a field is shown with a percent sign in the form. */
export function isPercentDisplay(unit: FieldUnit): boolean {
  return unit === "rate" || unit === "percent-raw";
}
