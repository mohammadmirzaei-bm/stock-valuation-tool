import { describe, it, expect } from "vitest";
import { marketPositionView } from "./semantics";

describe("marketPositionView — market price vs the valuation range", () => {
  it("below the range => cheaper than value => positive tone", () => {
    expect(marketPositionView("below")).toEqual({
      tone: "positive",
      label: "قیمت بازار زیر بازه (ارزان‌تر)",
    });
  });

  it("inside the range => neutral tone", () => {
    expect(marketPositionView("inside")).toEqual({
      tone: "neutral",
      label: "قیمت بازار داخل بازه",
    });
  });

  it("above the range => expensive => negative tone", () => {
    expect(marketPositionView("above")).toEqual({
      tone: "negative",
      label: "قیمت بازار بالای بازه (گران‌تر)",
    });
  });

  it("returns null when there is no market price", () => {
    expect(marketPositionView(null)).toBeNull();
    expect(marketPositionView(undefined)).toBeNull();
    expect(marketPositionView("")).toBeNull();
  });

  it("falls back to a neutral view for an unknown position", () => {
    expect(marketPositionView("sideways")).toEqual({ tone: "neutral", label: "sideways" });
  });
});
