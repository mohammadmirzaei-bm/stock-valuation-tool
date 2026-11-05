/**
 * Portfolio hand-off store (spec Portfolio: "Use in optimizer").
 *
 * Keeps the asset names, mean returns (UI percent) and annual covariance the
 * Statistics page computed, so the Optimizer page can seed from them. A store
 * (not the valuation workflow store) is used because the portfolio tools are
 * standalone and share no valuation state. Persisted so a refresh keeps it.
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface PortfolioHandoff {
  assetNames: string[];
  meanReturnsPercent: number[]; // UI percent; the optimizer divides by 100 on send
  covariance: number[][]; // annual, raw covariance (no unit conversion)
}

interface PortfolioState {
  handoff: PortfolioHandoff | null;
  setHandoff: (h: PortfolioHandoff) => void;
  clear: () => void;
}

export const usePortfolio = create<PortfolioState>()(
  persist(
    (set) => ({
      handoff: null,
      setHandoff: (h) => set({ handoff: h }),
      clear: () => set({ handoff: null }),
    }),
    { name: "sv-portfolio" },
  ),
);
