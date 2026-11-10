import * as React from "react";

/** Only plain objects get a shallow merge with defaults; primitives/arrays
 * are used verbatim so their value survives a reload. */
function isPlainObject(v: unknown): v is Record<string, unknown> {
  return typeof v === "object" && v !== null && !Array.isArray(v);
}

/** A stored value is trusted only when its runtime type matches the initial
 * value's — this rejects legacy `{}` entries left by an older build. */
function isCompatible(initial: unknown, parsed: unknown): boolean {
  if (Array.isArray(initial)) return Array.isArray(parsed);
  if (typeof initial === "number") return typeof parsed === "number" && Number.isFinite(parsed);
  return typeof initial === typeof parsed;
}

/**
 * useState synced to localStorage under `sv-form:<key>` so a workflow page keeps
 * its inputs across navigation and refresh (spec: per-page form persistence).
 */
export function usePersistentState<T>(key: string, initial: T) {
  const storageKey = `sv-form:${key}`;
  const [state, setState] = React.useState<T>(() => {
    try {
      const raw = localStorage.getItem(storageKey);
      if (raw == null) return initial;
      const parsed = JSON.parse(raw) as unknown;
      if (isPlainObject(initial) && isPlainObject(parsed)) {
        return { ...initial, ...parsed } as T;
      }
      return isCompatible(initial, parsed) ? (parsed as T) : initial;
    } catch {
      return initial;
    }
  });

  React.useEffect(() => {
    const id = window.setTimeout(() => {
      try {
        localStorage.setItem(storageKey, JSON.stringify(state));
      } catch {
        /* ignore */
      }
    }, 250);
    return () => window.clearTimeout(id);
  }, [storageKey, state]);

  // Flush the latest value on unmount: navigating away inside the debounce
  // window must not lose the last edit.
  const latest = React.useRef({ storageKey, state });
  latest.current = { storageKey, state };
  React.useEffect(
    () => () => {
      try {
        localStorage.setItem(latest.current.storageKey, JSON.stringify(latest.current.state));
      } catch {
        /* ignore */
      }
    },
    [],
  );

  return [state, setState] as const;
}
