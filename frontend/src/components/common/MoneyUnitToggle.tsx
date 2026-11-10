import { Banknote } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useSettings } from "@/store/settings";
import { MONEY_UNITS, type MoneyUnit } from "@/lib/format";

const ORDER: MoneyUnit[] = ["none", "rial", "toman"];

/**
 * Settings control: cycle the money unit (بدون واحد → ریال → تومان) applied to
 * every amount and money input. Mirrors DigitToggle's compact idiom; the label
 * is icon-only on the smallest screens so the header never overflows.
 */
export function MoneyUnitToggle() {
  const moneyUnit = useSettings((s) => s.moneyUnit);
  const setMoneyUnit = useSettings((s) => s.setMoneyUnit);
  const cycle = () => setMoneyUnit(ORDER[(ORDER.indexOf(moneyUnit) + 1) % ORDER.length]);
  return (
    <Button type="button" variant="ghost" size="sm" onClick={cycle} title="واحد پول">
      <Banknote className="h-4 w-4" />
      <span className="hidden text-xs text-muted-foreground sm:inline">{MONEY_UNITS[moneyUnit].label}</span>
    </Button>
  );
}
