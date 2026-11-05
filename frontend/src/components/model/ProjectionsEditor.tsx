import { Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { CashFlowProjectionInput } from "@/api/types";
import { useFormat } from "@/hooks/useFormat";

const BLANK: CashFlowProjectionInput = { ebit: 0, depreciation: 0, capex: 0, delta_nwc: 0 };
type Col = keyof CashFlowProjectionInput;

const COLS: { key: Col; label: string }[] = [
  { key: "ebit", label: "EBIT" },
  { key: "depreciation", label: "استهلاک" },
  { key: "capex", label: "Capex" },
  { key: "delta_nwc", label: "ΔNWC" },
];

/**
 * Editable FCFF rows. Used by DCF "Edit rows" and scenario "Copy from forecast".
 * All four columns are plain money values (no percent conversion here).
 */
export function ProjectionsEditor({
  rows,
  onChange,
  readonly = false,
}: {
  rows: CashFlowProjectionInput[];
  onChange?: (rows: CashFlowProjectionInput[]) => void;
  readonly?: boolean;
}) {
  const fmt = useFormat();

  const setCell = (i: number, key: Col, value: number) => {
    if (!onChange) return;
    const next = rows.map((r, idx) => (idx === i ? { ...r, [key]: value } : r));
    onChange(next);
  };

  return (
    <div className="overflow-x-auto rounded-md border border-border">
      <table dir="ltr" className="ltr-table w-full text-table-num">
        <thead className="bg-muted text-muted-foreground">
          <tr>
            <th className="px-3 py-2 text-right">#</th>
            {COLS.map((c) => (
              <th key={c.key} className="px-3 py-2">
                {c.label}
              </th>
            ))}
            {!readonly && <th className="px-3 py-2" />}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="border-b border-border">
              <td className="num px-3 py-1 text-right text-muted-foreground">{i + 1}</td>
              {COLS.map((c) =>
                readonly ? (
                  <td key={c.key} className="num px-3 py-1">
                    {fmt.number(r[c.key])}
                  </td>
                ) : (
                  <td key={c.key} className="px-1 py-1">
                    <Input
                      type="number"
                      value={String(r[c.key])}
                      onChange={(e) => setCell(i, c.key, Number(e.target.value))}
                      className="h-7 text-table-num"
                    />
                  </td>
                ),
              )}
              {!readonly && (
                <td className="px-1">
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    aria-label="حذف سال"
                    onClick={() => onChange?.(rows.filter((_, idx) => idx !== i))}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
      {!readonly && onChange && (
        <div className="border-t border-border p-2">
          <Button type="button" variant="outline" size="sm" onClick={() => onChange([...rows, { ...BLANK }])}>
            <Plus className="h-4 w-4" />
            افزودن سال
          </Button>
        </div>
      )}
    </div>
  );
}
