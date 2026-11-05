import { describe, it, expect, beforeEach } from "vitest";
import { useWorkflow } from "./workflow";

// The store persists to localStorage under "sv-workflow"; actions are synchronous.
beforeEach(() => {
  localStorage.clear();
  useWorkflow.getState().reset();
});

describe("workflow store — hand-off + detach", () => {
  const rows = [
    { ebit: 1000, depreciation: 200, capex: 250, delta_nwc: 50 },
    { ebit: 1100, depreciation: 210, capex: 260, delta_nwc: 55 },
  ];

  it("starts attached when forecast is sent, and detaches on manual edit", () => {
    useWorkflow.getState().sendToDcf(rows);
    expect(useWorkflow.getState().projectionsDetached).toBe(false);
    expect(useWorkflow.getState().projections?.length).toBe(2);

    useWorkflow.getState().overrideProjections(rows.map((r) => ({ ...r, ebit: r.ebit + 1 })));
    const s = useWorkflow.getState();
    expect(s.projectionsDetached).toBe(true);
    expect(s.projections?.[0].ebit).toBe(1001); // value kept, chip dropped
  });

  it("tracks WACC origin the same way", () => {
    useWorkflow.getState().useInDcf(9);
    expect(useWorkflow.getState().waccDetached).toBe(false);
    useWorkflow.getState().overrideWacc(10);
    expect(useWorkflow.getState().waccDetached).toBe(true);
    expect(useWorkflow.getState().waccPercent).toBe(10);
  });
});

describe("workflow store — ranges, sample, reset", () => {
  it("upserts by method (unique) and removes", () => {
    const wf = useWorkflow.getState();
    wf.upsertRange({ method: "DCF", low: 100, mid: 150, high: 200 });
    wf.upsertRange({ method: "Multiples", low: 120, mid: 140, high: 180 });
    wf.upsertRange({ method: "DCF", low: 90, mid: 140, high: 210 }); // replace
    expect(useWorkflow.getState().ranges.length).toBe(2);
    expect(useWorkflow.getState().ranges.find((r) => r.method === "DCF")?.low).toBe(90);
    useWorkflow.getState().removeRange("Multiples");
    expect(useWorkflow.getState().ranges.map((r) => r.method)).toEqual(["DCF"]);
  });

  it("loadSample seeds the reference numbers (WACC 9, 5 FCFF rows, 100 shares)", () => {
    useWorkflow.getState().loadSample();
    const s = useWorkflow.getState();
    expect(s.waccPercent).toBe(9);
    expect(s.projections?.length).toBe(5);
    expect(s.balanceSheet.sharesOutstanding).toBe(100);
    expect(s.balanceSheet.taxRate).toBe(25);
    expect(s.marketPrice).toBe(150);
    expect(s.completed.dcf).toBe(true);
  });

  it("reset clears everything", () => {
    useWorkflow.getState().loadSample();
    useWorkflow.getState().reset();
    const s = useWorkflow.getState();
    expect(s.projections).toBeNull();
    expect(s.waccPercent).toBeNull();
    expect(s.ranges).toEqual([]);
    expect(s.completed.dcf).toBe(false);
  });

  it("persists to localStorage", () => {
    useWorkflow.getState().useInDcf(9);
    const raw = localStorage.getItem("sv-workflow");
    expect(raw).toBeTruthy();
    expect(JSON.parse(raw!).state.waccPercent).toBe(9);
  });
});
