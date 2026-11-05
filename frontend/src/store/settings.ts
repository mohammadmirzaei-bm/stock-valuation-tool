/**
 * App-wide settings. Persisted so the Persian-digit preference survives a
 * refresh (spec: "offer a Persian-digit toggle in settings").
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { DigitMode } from "@/lib/format";

interface SettingsState {
  digits: DigitMode;
  setDigits: (mode: DigitMode) => void;
  toggleDigits: () => void;
}

export const useSettings = create<SettingsState>()(
  persist(
    (set, get) => ({
      digits: "latin",
      setDigits: (mode) => set({ digits: mode }),
      toggleDigits: () => set({ digits: get().digits === "latin" ? "persian" : "latin" }),
    }),
    { name: "sv-settings" },
  ),
);

/** Convenience accessor for the current digit mode (for non-hook call sites). */
export function getDigitMode(): DigitMode {
  return useSettings.getState().digits;
}
