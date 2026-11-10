import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MoneyUnitToggle } from "./MoneyUnitToggle";
import { useSettings } from "@/store/settings";

describe("MoneyUnitToggle — cycles the money unit stored in settings", () => {
  beforeEach(() => useSettings.setState({ moneyUnit: "none" }));

  it("cycles none → ریال → تومان → none and persists to the store", () => {
    render(<MoneyUnitToggle />);
    const btn = screen.getByTitle("واحد پول");
    expect(screen.getByText("بدون واحد")).toBeInTheDocument();

    fireEvent.click(btn);
    expect(useSettings.getState().moneyUnit).toBe("rial");
    expect(screen.getByText("ریال")).toBeInTheDocument();

    fireEvent.click(btn);
    expect(useSettings.getState().moneyUnit).toBe("toman");
    expect(screen.getByText("تومان")).toBeInTheDocument();

    fireEvent.click(btn);
    expect(useSettings.getState().moneyUnit).toBe("none");
  });
});
