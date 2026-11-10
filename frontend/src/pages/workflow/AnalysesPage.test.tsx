import { describe, it, expect, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { TooltipProvider } from "@/components/ui/tooltip";
import { AnalysesPage, GrowthRangeBar, scenarioUpsideCards } from "./AnalysesPage";
import { useWorkflow } from "@/store/workflow";
import type { FormatApi } from "@/hooks/useFormat";

// Minimal formatter stub: only the two methods scenarioUpsideCards calls.
const fmt = {
  signedPercent: (v: number | null) => `sp:${v}`,
  percent: (v: number | null) => `p:${v}`,
} as unknown as FormatApi;

describe("GrowthRangeBar — LTR island so markers and min/max labels agree", () => {
  it("renders inside a dir=ltr container", () => {
    const { container } = render(
      <GrowthRangeBar min={0.02} max={0.08} implied={0.05} own={null} gap={null} />,
    );
    expect(container.querySelector('[dir="ltr"]')).not.toBeNull();
  });

  it("shows the min and max bounds as percent labels", () => {
    render(<GrowthRangeBar min={0.02} max={0.08} implied={0.05} own={null} gap={null} />);
    expect(screen.getByText("2%")).toBeInTheDocument();
    expect(screen.getByText("8%")).toBeInTheDocument();
  });
});

describe("scenarioUpsideCards — optional API fields arrive as null, not undefined", () => {
  it("hides both cards when the fields are null", () => {
    const cards = scenarioUpsideCards(
      { expected_upside_percent: null, probability_of_upside_percent: null },
      fmt,
    );
    expect(cards).toEqual([]);
  });

  it("shows both cards when the fields carry numbers", () => {
    const cards = scenarioUpsideCards(
      { expected_upside_percent: 12.5, probability_of_upside_percent: 60 },
      fmt,
    );
    expect(cards.map((c) => c.label)).toEqual(["بازده مورد انتظار", "احتمال بازده مثبت"]);
    expect(cards[0].value).toBe("sp:12.5");
  });

  it("shows only the card whose field is non-null", () => {
    const cards = scenarioUpsideCards(
      { expected_upside_percent: null, probability_of_upside_percent: 40 },
      fmt,
    );
    expect(cards).toHaveLength(1);
    expect(cards[0].label).toBe("احتمال بازده مثبت");
  });
});

describe("AnalysesPage — the active tab comes from ?tab=", () => {
  const renderAt = (url: string) =>
    render(
      <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
        <TooltipProvider>
          <MemoryRouter initialEntries={[url]}>
            <AnalysesPage />
          </MemoryRouter>
        </TooltipProvider>
      </QueryClientProvider>,
    );

  beforeEach(() => useWorkflow.getState().reset());

  it("opens the tab named in the query string (sensitivity)", () => {
    renderAt("/analyses?tab=sensitivity");
    expect(screen.getByText("رشد پایانی پایه")).toBeInTheDocument();
    expect(screen.queryByLabelText("نام سناریو")).toBeNull();
  });

  it("opens the reverse tab", () => {
    renderAt("/analyses?tab=reverse");
    expect(screen.getByText(/رشد پایانی نظر خودتان/)).toBeInTheDocument();
  });

  it("falls back to scenarios for a missing or unknown tab", () => {
    renderAt("/analyses?tab=unknown");
    expect(screen.getAllByLabelText("نام سناریو").length).toBeGreaterThan(0);
  });
});
