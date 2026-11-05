/**
 * Formatting bound to the active digit mode (Latin / Persian). Pages use these
 * instead of calling lib/format directly, so the settings toggle is honored
 * everywhere at once.
 */

import { useSettings } from "@/store/settings";
import {
  formatNumber,
  formatPercent,
  formatCurrency,
  formatSigned,
  formatSignedPercent,
  type NumOptions,
} from "@/lib/format";

export function useFormat() {
  const digits = useSettings((s) => s.digits);
  const withDigits = (o: NumOptions = {}): NumOptions => ({ digits, ...o });
  return {
    digits,
    number: (v: number | null | undefined, o?: NumOptions) => formatNumber(v, withDigits(o)),
    percent: (v: number | null | undefined, o?: NumOptions) => formatPercent(v, withDigits(o)),
    currency: (v: number | null | undefined, o?: NumOptions) => formatCurrency(v, withDigits(o)),
    signed: (v: number | null | undefined, o?: NumOptions) => formatSigned(v, withDigits(o)),
    signedPercent: (v: number | null | undefined, o?: NumOptions) => formatSignedPercent(v, withDigits(o)),
  };
}

export type FormatApi = ReturnType<typeof useFormat>;
