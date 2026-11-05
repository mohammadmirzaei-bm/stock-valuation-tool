/**
 * Per-page form value persistence (spec: "Persist each page's form values in
 * localStorage so navigating away does not clear them"). Kept separate from the
 * shared workflow store — these are the raw form inputs for a single page.
 */

import type { FormValues } from "./request";

const key = (pageKey: string) => `sv-form:${pageKey}`;

export function loadStoredForm(pageKey: string): FormValues | null {
  try {
    const raw = localStorage.getItem(key(pageKey));
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Record<string, unknown>;
    const out: FormValues = {};
    for (const [k, value] of Object.entries(parsed)) {
      out[k] = typeof value === "number" && Number.isFinite(value) ? value : undefined;
    }
    return out;
  } catch {
    return null;
  }
}

export function saveStoredForm(pageKey: string, values: FormValues): void {
  try {
    localStorage.setItem(key(pageKey), JSON.stringify(values));
  } catch {
    /* ignore quota errors */
  }
}

export function clearStoredForm(pageKey: string): void {
  try {
    localStorage.removeItem(key(pageKey));
  } catch {
    /* ignore */
  }
}
