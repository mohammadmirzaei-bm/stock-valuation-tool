import * as React from "react";
import { Check, Copy, Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { copyText } from "@/lib/clipboard";
import { downloadCsv, type CsvValue } from "@/lib/csv";

/** Copy a text result to the clipboard with transient success feedback. */
export function CopyButton({ getText, label = "کپی نتیجه" }: { getText: () => string; label?: string }) {
  const [copied, setCopied] = React.useState(false);
  return (
    <Button
      type="button"
      variant="outline"
      size="sm"
      onClick={async () => {
        const ok = await copyText(getText());
        if (ok) {
          setCopied(true);
          window.setTimeout(() => setCopied(false), 1200);
        }
      }}
    >
      {copied ? <Check className="h-4 w-4 text-positive" /> : <Copy className="h-4 w-4" />}
      {copied ? "کپی شد" : label}
    </Button>
  );
}

/** Download a table as CSV. */
export function CsvButton({
  filename,
  getRows,
  label = "خروجی CSV",
}: {
  filename: string;
  getRows: () => CsvValue[][];
  label?: string;
}) {
  return (
    <Button type="button" variant="outline" size="sm" onClick={() => downloadCsv(filename, getRows())}>
      <Download className="h-4 w-4" />
      {label}
    </Button>
  );
}
