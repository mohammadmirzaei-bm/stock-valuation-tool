/**
 * Build a wire request body from form values using each field's declared unit.
 *
 * Values in the form are in the units the student types (rates are percent);
 * this maps every field through the conversion layer so a `rate` becomes a
 * decimal and a `percent-raw` stays raw. Because conversion is driven by the
 * field config it is impossible to forget the ÷100 on a new page.
 */

import type { FieldDef } from "@/config/fields";
import { toWire } from "./units";

export type FormValues = Record<string, number | undefined>;

/** Convert the listed fields from form values into a wire body object. */
export function buildWire(
  fields: FieldDef[],
  values: FormValues,
): Record<string, number | undefined> {
  const body: Record<string, number | undefined> = {};
  for (const field of fields) {
    const raw = values[field.key];
    if (raw === undefined || raw === null || Number.isNaN(raw)) continue;
    body[field.key] = toWire(field.unit, raw);
  }
  return body;
}

/** Convert a single percent-form value using one field's unit. */
export function wireValue(field: FieldDef, value: number): number {
  return toWire(field.unit, value);
}
