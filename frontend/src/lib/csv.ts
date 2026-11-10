/** CSV export for any table on a results page (spec "Export"). */

export type CsvValue = string | number | null | undefined;

function escapeCell(value: CsvValue): string {
  if (value === null || value === undefined) return "";
  const s = String(value);
  // Quote when the cell contains a delimiter, quote, or newline.
  if (/[",\n]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
  return s;
}

export function toCsv(rows: CsvValue[][]): string {
  return rows.map((row) => row.map(escapeCell).join(",")).join("\r\n");
}

/** Prepend a UTF-8 BOM so Excel renders Persian text correctly. */
export function csvBlob(csv: string): Blob {
  return new Blob(["\uFEFF" + csv], { type: "text/csv;charset=utf-8;" });
}

export function triggerDownload(data: Blob | string, filename: string): void {
  const url = typeof data === "string" ? data : URL.createObjectURL(data);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  if (typeof data !== "string") URL.revokeObjectURL(url);
}

export function downloadCsv(filename: string, rows: CsvValue[][]): void {
  triggerDownload(csvBlob(toCsv(rows)), filename);
}
