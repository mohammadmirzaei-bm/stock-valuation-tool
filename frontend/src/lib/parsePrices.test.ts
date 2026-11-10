import { describe, it, expect } from "vitest";
import { parsePriceGrid } from "./parsePrices";

describe("parsePriceGrid (paste / CSV → aligned per-asset prices)", () => {
  it("transposes a tab grid: header = names, columns = assets, rows = time", () => {
    const grid = ["الف\tب", "8\t8", "12\t8", "6\t12", "6\t6"].join("\n");
    const { series, error } = parsePriceGrid(grid);
    expect(error).toBeUndefined();
    expect(series.map((s) => s.name)).toEqual(["الف", "ب"]);
    expect(series[0].prices).toEqual([8, 12, 6, 6]);
    expect(series[1].prices).toEqual([8, 8, 12, 6]);
  });

  it("parses comma-separated CSV", () => {
    const { series } = parsePriceGrid("A,B\n10,20\n11,21\n12,22");
    expect(series[0].prices).toEqual([10, 11, 12]);
    expect(series[1].prices).toEqual([20, 21, 22]);
  });

  it("drops ragged / non-numeric rows so every series stays equal length", () => {
    const grid = "A,B\n1,2\n3\n4,x\n5,6";
    const { series, droppedRows } = parsePriceGrid(grid);
    expect(series[0].prices).toEqual([1, 5]);
    expect(series[1].prices).toEqual([2, 6]);
    expect(droppedRows).toBe(2);
  });

  it("reports zero dropped rows for a clean grid", () => {
    expect(parsePriceGrid("A,B\n1,2\n3,4\n5,6").droppedRows).toBe(0);
  });

  it("still reports how many rows it dropped when it errors", () => {
    // three data rows, none aligned → the parse fails but the count is known
    expect(parsePriceGrid("A,B\n1\nx\n3,4,5").droppedRows).toBe(3);
  });

  it("tolerates Persian digits", () => {
    const { series } = parsePriceGrid("A\tB\n۱۰\t۲۰\n۱۱\t۲۱\n۱۲\t۲۲");
    expect(series[0].prices).toEqual([10, 11, 12]);
  });

  it("rejects non-positive prices and duplicate names", () => {
    expect(parsePriceGrid("A,B\n1,2\n-3,4\n4,5").error).toBeTruthy();
    expect(parsePriceGrid("A,A\n1,2\n3,4\n5,6").error).toBeTruthy();
  });

  it("needs a header plus at least two data rows", () => {
    expect(parsePriceGrid("A,B").error).toBeTruthy();
    expect(parsePriceGrid("A,B\n1,2").error).toBeTruthy();
  });
});
