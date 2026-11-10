import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Hero, ComponentCards } from "./ResultParts";

describe("Hero — result hierarchy (label above, big value, unit/hint below)", () => {
  it("renders the label, the value and the hint", () => {
    render(<Hero label="ارزش هر سهم" value="1,234" hint="بر مبنای هر سهم" />);
    expect(screen.getByText("ارزش هر سهم")).toBeInTheDocument();
    expect(screen.getByText("1,234")).toBeInTheDocument();
    expect(screen.getByText("بر مبنای هر سهم")).toBeInTheDocument();
  });

  it("omits the hint line when there is none", () => {
    const { container } = render(<Hero label="بازده" value="12%" />);
    // label + value only → two child divs, no third hint line
    expect(container.querySelector(".space-y-1")?.childElementCount).toBe(2);
  });
});

describe("ComponentCards — supporting parts, smaller and muted", () => {
  it("renders one card per item", () => {
    render(<ComponentCards items={[{ label: "EV", value: "800" }, { label: "Equity", value: "600" }]} />);
    expect(screen.getByText("EV")).toBeInTheDocument();
    expect(screen.getByText("Equity")).toBeInTheDocument();
  });

  it("renders nothing when there are no items", () => {
    const { container } = render(<ComponentCards items={[]} />);
    expect(container).toBeEmptyDOMElement();
  });
});
