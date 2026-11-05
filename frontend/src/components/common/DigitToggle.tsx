import { Hash } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useSettings } from "@/store/settings";
import { formatNumber } from "@/lib/format";

/** Settings control: switch between Latin and Persian digits everywhere. */
export function DigitToggle() {
  const digits = useSettings((s) => s.digits);
  const toggle = useSettings((s) => s.toggleDigits);
  const sample = formatNumber(12345.6, { digits, maxFractionDigits: 1 });
  return (
    <Button type="button" variant="ghost" size="sm" onClick={toggle} title="ارقام فارسی / لاتین">
      <Hash className="h-4 w-4" />
      <span className="num hidden sm:inline">{sample}</span>
      <span className="text-xs text-muted-foreground">{digits === "latin" ? "لاتین" : "فارسی"}</span>
    </Button>
  );
}
