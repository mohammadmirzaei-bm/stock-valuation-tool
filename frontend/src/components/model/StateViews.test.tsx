import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ResultSkeleton } from "./StateViews";

describe("ResultSkeleton — shaped like the real result layout", () => {
  it("announces a loading status for assistive tech", () => {
    render(<ResultSkeleton />);
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("mirrors hero + a four-card component row + a chart block", () => {
    const { container } = render(<ResultSkeleton />);
    // the component-cards grid holds four placeholders, like ComponentCards
    expect(container.querySelectorAll(".grid > div")).toHaveLength(4);
    // hero (3 bars) + 4 cards × 2 bars + 1 chart bar = 12 pulsing blocks
    expect(container.querySelectorAll(".animate-pulse")).toHaveLength(12);
  });
});
