import * as React from "react";
import { useController, type Control } from "react-hook-form";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { InfoTip } from "./InfoTip";
import { resolveField, type FieldDef } from "@/config/fields";
import { useSettings } from "@/store/settings";
import { moneySuffix } from "@/lib/format";
import type { FormValues } from "@/lib/request";
import { cn } from "@/lib/utils";

interface FieldInputProps {
  control: Control<FormValues>;
  field: FieldDef;
  error?: string;
  disabled?: boolean;
  /** Optional element rendered next to the label (e.g. a "From step 1 ✓" chip). */
  badge?: React.ReactNode;
  labelFor?: string;
}

/** A labeled numeric input with unit suffix, ⓘ tooltip and inline error. */
export function FieldInput({ control, field, error, disabled, badge }: FieldInputProps) {
  const meta = resolveField(field);
  const moneyUnit = useSettings((s) => s.moneyUnit);
  const { field: rhf } = useController({ control, name: field.key });

  // Money fields take their suffix from the settings unit (never hardcoded);
  // an explicit per-field suffix still wins.
  const suffix = meta.suffix ?? (field.unit === "money" ? moneySuffix(moneyUnit) : undefined);

  const display = rhf.value === undefined || rhf.value === null || Number.isNaN(rhf.value) ? "" : String(rhf.value);

  return (
    <div className="grid gap-1.5">
      <div className="flex items-center gap-1.5">
        <Label htmlFor={rhf.name} className="text-foreground">
          {meta.label}
        </Label>
        <InfoTip text={field.tooltip} />
        {badge}
      </div>
      <div className="flex items-center gap-2">
        <Input
          id={rhf.name}
          name={rhf.name}
          type="number"
          inputMode="decimal"
          step={meta.step}
          min={field.min}
          max={field.max}
          disabled={disabled}
          value={display}
          onChange={(e) => {
            const raw = e.target.value;
            rhf.onChange(raw === "" ? undefined : Number(raw));
          }}
          aria-invalid={!!error}
          aria-describedby={error ? `${rhf.name}-error` : undefined}
          className={cn(error && "border-negative focus-visible:ring-negative")}
        />
        {suffix && <span className="shrink-0 text-sm text-muted-foreground">{suffix}</span>}
      </div>
      {error && (
        <p id={`${rhf.name}-error`} className="text-xs text-negative">
          {error}
        </p>
      )}
    </div>
  );
}
