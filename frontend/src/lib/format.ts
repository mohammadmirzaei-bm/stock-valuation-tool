/**
 * Number / percent / currency formatting.
 *
 * Rules from the spec ("Language and direction"):
 *  - Numbers are Latin digits by default with a Persian-digit toggle in settings.
 *  - Numeric content is an LTR island; the caller wraps it in `.num`.
 *  - Percentages always come from the response's `_percent` fields — never
 *    multiply a decimal here.
 */

export type DigitMode = "latin" | "persian";

const PERSIAN_DIGITS = ["۰", "۱", "۲", "۳", "۴", "۵", "۶", "۷", "۸", "۹"];

/** Convert ASCII digits in a string to Persian digits (keeps , . % − etc). */
export function toPersianDigits(input: string): string {
  return input.replace(/[0-9]/g, (d) => PERSIAN_DIGITS[Number(d)]);
}

export function applyDigits(input: string, mode: DigitMode): string {
  return mode === "persian" ? toPersianDigits(input) : input;
}

export interface NumOptions {
  digits?: DigitMode;
  minFractionDigits?: number;
  maxFractionDigits?: number;
}

/** Grouped decimal formatting with a fixed digit mode. Null-safe. */
export function formatNumber(value: number | null | undefined, opts: NumOptions = {}): string {
  const { digits = "latin", minFractionDigits = 0, maxFractionDigits = 2 } = opts;
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "—";
  }
  const formatted = new Intl.NumberFormat("en-US", {
    minimumFractionDigits: minFractionDigits,
    maximumFractionDigits: maxFractionDigits,
  }).format(value);
  return applyDigits(formatted, digits);
}

/**
 * Format a percent value that is ALREADY in percent units (e.g. 12.5 -> "12.5%").
 * Pass the response's `*_percent` field directly.
 */
export function formatPercent(
  percentValue: number | null | undefined,
  opts: NumOptions = {},
): string {
  if (percentValue === null || percentValue === undefined || !Number.isFinite(percentValue)) {
    return "—";
  }
  const { digits = "latin", maxFractionDigits = 2 } = opts;
  return `${formatNumber(percentValue, { digits, maxFractionDigits })}%`;
}

/** Format a currency amount with the ریال unit suffix (spec unit label). */
export function formatCurrency(value: number | null | undefined, opts: NumOptions = {}): string {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "—";
  }
  return `${formatNumber(value, opts)} ریال`;
}

/** A signed number, used for upside/downside columns. */
export function formatSigned(value: number | null | undefined, opts: NumOptions = {}): string {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "—";
  }
  const sign = value > 0 ? "+" : "";
  return `${sign}${formatNumber(value, opts)}`;
}

export function formatSignedPercent(
  percentValue: number | null | undefined,
  opts: NumOptions = {},
): string {
  if (percentValue === null || percentValue === undefined || !Number.isFinite(percentValue)) {
    return "—";
  }
  const sign = percentValue > 0 ? "+" : "";
  return `${sign}${formatPercent(percentValue, opts)}`;
}
