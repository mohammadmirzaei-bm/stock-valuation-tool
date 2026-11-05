import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { InfoTip } from "./InfoTip";
import { cn } from "@/lib/utils";

interface NumberFieldProps {
  label: string;
  value: number | undefined;
  onChange: (v: number | undefined) => void;
  suffix?: string;
  info?: string;
  error?: string;
  min?: number;
  max?: number;
  step?: number;
  disabled?: boolean;
  compact?: boolean;
}

/** A controlled numeric input (used outside react-hook-form pages: forecast, peers). */
export function NumberField({
  label,
  value,
  onChange,
  suffix,
  info,
  error,
  min,
  max,
  step,
  disabled,
  compact,
}: NumberFieldProps) {
  return (
    <div className={cn("grid gap-1.5", compact && "gap-1")}>
      <div className="flex items-center gap-1.5">
        <Label className="text-foreground">{label}</Label>
        {info && <InfoTip text={info} />}
      </div>
      <div className="flex items-center gap-2">
        <Input
          type="number"
          inputMode="decimal"
          min={min}
          max={max}
          step={step}
          disabled={disabled}
          value={value === undefined || Number.isNaN(value) ? "" : String(value)}
          onChange={(e) => onChange(e.target.value === "" ? undefined : Number(e.target.value))}
          aria-invalid={!!error}
          className={cn(error && "border-negative", compact && "h-8 text-table-num")}
        />
        {suffix && <span className="shrink-0 text-sm text-muted-foreground">{suffix}</span>}
      </div>
      {error && <p className="text-xs text-negative">{error}</p>}
    </div>
  );
}
