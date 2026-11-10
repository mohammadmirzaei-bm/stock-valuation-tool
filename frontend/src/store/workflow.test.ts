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
  it("upserts by method (unique) and removes by id", () => {
    const wf = useWorkflow.getState();
    wf.upsertRange({ method: "DCF", low: 100, mid: 150, high: 200 });
    wf.upsertRange({ method: "Multiples", low: 120, mid: 140, high: 180 });
    wf.upsertRange({ method: "DCF", low: 90, mid: 140, high: 210 }); // replace in place
    expect(useWorkflow.getState().ranges.length).toBe(2);
    expect(useWorkflow.getState().ranges.find((r) => r.method === "DCF")?.low).toBe(90);
    const multiplesId = useWorkflow.getState().ranges.find((r) => r.method === "Multiples")!.id;
    useWorkflow.getState().removeRange(multiplesId);
    expect(useWorkflow.getState().ranges.map((r) => r.method)).toEqual(["DCF"]);
  });

  it("assigns a stable id and re-upsert keeps order + id (no reorder on edit)", () => {
    const wf = useWorkflow.getState();
    wf.upsertRange({ method: "DCF", low: 100, mid: 150, high: 200 });
    wf.upsertRange({ method: "Multiples", low: 120, mid: 140, high: 180 });
    const [dcfId, multId] = useWorkflow.getState().ranges.map((r) => r.id);
    expect(dcfId).toBeTruthy();
    expect(multId).not.toBe(dcfId);

    // Re-sending DCF must update in place, not move it after Multiples.
    wf.upsertRange({ method: "DCF", low: 110, mid: 160, high: 210 });
    const after = useWorkflow.getState().ranges;
    expect(after.map((r) => r.method)).toEqual(["DCF", "Multiples"]);
    expect(after[0].id).toBe(dcfId);
    expect(after[0].low).toBe(110);
  });

  it("updateRange(id, patch) edits fields in place, preserving order and id", () => {
    const wf = useWorkflow.getState();
    wf.upsertRange({ method: "DCF", low: 100, mid: 150, high: 200 });
    wf.upsertRange({ method: "Multiples", low: 120, mid: 140, high: 180 });
    const dcfId = useWorkflow.getState().ranges[0].id;

    wf.updateRange(dcfId, { method: "DCF ارزش" });
    wf.updateRange(dcfId, { low: 90 });
    const after = useWorkflow.getState().ranges;
    expect(after.map((r) => r.method)).toEqual(["DCF ارزش", "Multiples"]);
    expect(after[0].id).toBe(dcfId);
    expect(after[0].low).toBe(90);
    expect(after[0].mid).toBe(150); // untouched fields preserved
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

describe("workflow store — completion flags", () => {
  it("completeStep sets only its own flag (dcf and football stay independent)", () => {
    useWorkflow.getState().completeStep("dcf");
    expect(useWorkflow.getState().completed.dcf).toBe(true);
    expect(useWorkflow.getState().completed.football).toBe(false);
    expect(useWorkflow.getState().completed.multiples).toBe(false);

    useWorkflow.getState().completeStep("football");
    expect(useWorkflow.getState().completed.football).toBe(true);
    expect(useWorkflow.getState().completed.dcf).toBe(true);
  });
});
