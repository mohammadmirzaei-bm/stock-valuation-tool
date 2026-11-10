import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { InsightCallout } from "./InsightCallout";

describe("InsightCallout — one-line title + explanation, tinted by tone", () => {
  it("renders the title and the explanation", () => {
    render(<InsightCallout tone="warning" title="سهم ارزش انتهایی بالاست" explanation="بیش از ۸۰٪ ارزش از دورهٔ پایانی می‌آید." />);
    expect(screen.getByText("سهم ارزش انتهایی بالاست")).toBeInTheDocument();
    expect(screen.getByText("بیش از ۸۰٪ ارزش از دورهٔ پایانی می‌آید.")).toBeInTheDocument();
  });

  it("tints the container by tone (negative)", () => {
    const { container } = render(<InsightCallout tone="negative" title="ارزش سهام منفی است" />);
    const box = container.firstElementChild as HTMLElement;
    expect(box.className).toContain("border-negative/40");
    expect(box.className).toContain("bg-negative/10");
  });

  it("omits the explanation line when none is given", () => {
    const { container } = render(<InsightCallout tone="positive" title="خوب است" />);
    const box = container.firstElementChild as HTMLElement;
    // children are [icon, textBlock]; the text block holds only the title
    expect(box.children[1].childElementCount).toBe(1);
  });
});
