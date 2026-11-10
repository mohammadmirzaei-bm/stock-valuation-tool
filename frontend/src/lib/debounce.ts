import { useEffect, useState } from "react";

/**
 * Debounced value used to trigger the 400 ms auto-calculate after the last
 * keystroke (spec "Behavior": calculate automatically 400 ms after the last
 * keystroke once the form is valid).
 */
export function useDebouncedValue<T>(value: T, delayMs = 400): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const id = window.setTimeout(() => setDebounced(value), delayMs);
    return () => window.clearTimeout(id);
  }, [value, delayMs]);
  return debounced;
}
