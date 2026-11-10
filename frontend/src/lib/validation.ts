/**
 * Client-side mirror validation (spec "Rule 3"): the backend stays the
 * authority; these checks only avoid pointless round trips. Bounds come from
 * each field's config; the few cross-field rules (required return must exceed
 * growth by ≥ 0.5pp, market return must exceed risk-free, etc.) are listed per
 * model. Anything not mirrored here is left to the backend's 400.
 *
 * Values passed in are in UI units (rates as percent), so a spread of "half a
 * percentage point" is a plain `>= 0.5` comparison here.
 */

import type { FieldDef } from "@/config/fields";

/** Minimum required return / WACC minus growth, in percentage points. */
export const MIN_SPREAD_PP = 0.5;

export interface ValidationOptions {
  /** Each pair: values[higher] must exceed values[lower] by MIN_SPREAD_PP. */
  spread?: { higher: string; lower: string }[];
  /** values[greater] must be strictly greater than values[smaller]. */
  greaterThan?: { greater: string; smaller: string }[];
  /** Extra named fields not in `fields` to require as present (e.g. lists). */
  required?: string[];
}

export type FieldErrors = Record<string, string>;

const REQUIRED_MSG = "این فیلد لازم است";

/**
 * Validate a model's percent-form values. Returns per-field messages; an empty
 * object means the form is complete and passes the mirrored rules.
 */
export function validateModel(
  values: Record<string, number | undefined>,
  fields: FieldDef[],
  options: ValidationOptions = {},
): FieldErrors {
  const errors: FieldErrors = {};

  const present = (key: string) => {
    const v = values[key];
    return v !== undefined && v !== null && Number.isFinite(v);
  };

  // Required + bounds from the field config.
  for (const field of fields) {
    if (!present(field.key)) {
      errors[field.key] = REQUIRED_MSG;
      continue;
    }
    const v = values[field.key] as number;
    if (field.unit === "count" && !Number.isInteger(v)) {
      errors[field.key] = "باید عدد صحیح باشد";
      continue;
    }
    if (field.min !== undefined) {
      const bad = field.exclusiveMin ? v <= field.min : v < field.min;
      if (bad) {
        errors[field.key] = field.exclusiveMin ? `باید بیشتر از ${field.min} باشد` : `حداقل ${field.min}`;
        continue;
      }
    }
    if (field.max !== undefined) {
      const bad = field.exclusiveMax ? v >= field.max : v > field.max;
      if (bad) {
        errors[field.key] = field.exclusiveMax ? `باید کمتر از ${field.max} باشد` : `حداکثر ${field.max}`;
      }
    }
  }

  // Spread rules (only when both sides are present and not already errored).
  for (const pair of options.spread ?? []) {
    if (present(pair.higher) && present(pair.lower) && !errors[pair.higher] && !errors[pair.lower]) {
      const diff = (values[pair.higher] as number) - (values[pair.lower] as number);
      if (diff < MIN_SPREAD_PP) {
        errors[pair.higher] = `باید حداقل ${MIN_SPREAD_PP} واحد درصد بیشتر از ${pair.lower} باشد`;
      }
    }
  }

  for (const pair of options.greaterThan ?? []) {
    if (present(pair.greater) && present(pair.smaller) && !errors[pair.greater] && !errors[pair.smaller]) {
      if ((values[pair.greater] as number) <= (values[pair.smaller] as number)) {
        errors[pair.greater] = "باید بیشتر از مقدار دیگر باشد";
      }
    }
  }

  for (const key of options.required ?? []) {
    if (!present(key)) errors[key] = REQUIRED_MSG;
  }

  return errors;
}

export function isValid(errors: FieldErrors): boolean {
  return Object.keys(errors).length === 0;
}
