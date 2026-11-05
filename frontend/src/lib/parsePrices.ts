/**
 * Client-side parser for the portfolio "paste prices / upload CSV" flow (spec
 * Portfolio: Statistics). The grid is: first row = asset names, each column =
 * one asset, subsequent rows = time points (oldest → newest). We transpose it
 * into one positive price list per asset and align rows — only rows that carry
 * a finite number in every kept column survive, so every series is the same
 * length (the backend assumes equal-length aligned series).
 */

export interface ParsedSeries {
  name: string;
  prices: number[];
}

export interface ParseResult {
  series: ParsedSeries[];
  error?: string;
}

function splitRow(line: string, delimiter: string): string[] {
  return line.split(delimiter).map((c) => c.trim());
}

function detectDelimiter(lines: string[]): string {
  return lines.some((l) => l.includes("\t")) ? "\t" : ",";
}

/** Persian/Arabic digits are tolerated alongside Latin digits. */
const PERSIAN = /[\u06F0-\u06F9\u0660-\u0669]/g;
function normalizeNumber(cell: string): number {
  const ascii = cell.replace(PERSIAN, (d) => {
    const code = d.charCodeAt(0);
    const base = code >= 0x06f0 ? 0x06f0 : 0x0660;
    return String(code - base);
  });
  return Number(ascii);
}

export function parsePriceGrid(text: string): ParseResult {
  const lines = text
    .replace(/\r\n/g, "\n")
    .split("\n")
    .map((l) => l.trim())
    .filter((l) => l.length > 0);

  if (lines.length < 2) return { series: [], error: "حداقل یک سطر نام و یک سطر قیمت لازم است." };

  const delimiter = detectDelimiter(lines);
  const header = splitRow(lines[0], delimiter);
  const nameCount = header.length;
  if (nameCount < 1) return { series: [], error: "سطر اول باید نام دارایی‌ها را داشته باشد." };

  const dataRows = lines.slice(1).map((l) => splitRow(l, delimiter));

  // Keep only rectangular rows where every expected column is numeric.
  const aligned = dataRows.filter((row) => {
    if (row.length !== nameCount) return false;
    return row.every((cell) => {
      const n = normalizeNumber(cell);
      return Number.isFinite(n);
    });
  });

  if (aligned.length < 2) {
    return { series: [], error: "ستون‌ها هم‌تراز نیستند یا کمترین تعداد سطر معتبر (۲) رعایت نشده است." };
  }

  const series: ParsedSeries[] = header.map((rawName, col) => {
    const name = rawName || `دارایی ${col + 1}`;
    const prices = aligned.map((row) => normalizeNumber(row[col]));
    return { name, prices };
  });

  // Prices must be positive for the backend.
  const anyNonPositive = series.some((s) => s.prices.some((p) => p <= 0));
  if (anyNonPositive) return { series: [], error: "همهٔ قیمت‌ها باید مثبت باشند." };

  const uniqueNames = new Set(series.map((s) => s.name)).size === series.length;
  if (!uniqueNames) return { series: [], error: "نام دارایی‌ها باید یکتا باشد." };

  return { series };
}
