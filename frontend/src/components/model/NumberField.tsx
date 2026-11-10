import * as React from "react";
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
  /** Optional input id, so a prerequisite checklist can scroll to and focus it. */
  id?: string;
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
  id,
}: NumberFieldProps) {
  // Every input gets a stable id so its label is always associated (clicking
  // the label focuses the field; screen readers announce it). Callers that need
  // a known id (prerequisite focus targets) can still override it.
  const autoId = React.useId();
  const inputId = id ?? autoId;
  return (
    <div className={cn("grid gap-1.5", compact && "gap-1")}>
      <div className="flex items-center gap-1.5">
        <Label className="text-foreground" htmlFor={inputId}>{label}</Label>
        {info && <InfoTip text={info} />}
      </div>
      <div className="flex items-center gap-2">
        <Input
          id={inputId}
          type="number"
          inputMode="decimal"
          min={min}
          max={max}
          step={step}
          disabled={disabled}
          value={value === undefined || Number.isNaN(value) ? "" : String(value)}
          onChange={(e) => onChange(e.target.value === "" ? undefined : Number(e.target.value))}
          aria-invalid={!!error}
          aria-describedby={error ? `${inputId}-error` : undefined}
          className={cn(error && "border-negative", compact && "h-8 text-table-num")}
        />
        {suffix && <span className="shrink-0 text-sm text-muted-foreground">{suffix}</span>}
      </div>
      {error && <p id={`${inputId}-error`} className="text-xs text-negative">{error}</p>}
    </div>
  );
}