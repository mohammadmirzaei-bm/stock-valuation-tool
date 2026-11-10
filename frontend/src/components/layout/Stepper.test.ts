import { describe, it, expect } from "vitest";
import { stepComplete } from "./Stepper";
import type { StepId } from "@/store/workflow";

const completed = (over: Partial<Record<StepId, boolean>> = {}): Record<StepId, boolean> => ({
  forecast: false,
  wacc: false,
  dcf: false,
  scenarios: false,
  sensitivity: false,
  reverse: false,
  multiples: false,
  football: false,
  ...over,
});

describe("stepComplete", () => {
  it("treats football complete only from its own flag, never from multiples", () => {
    expect(stepComplete(completed({ multiples: true }), "football")).toBe(false);
    expect(stepComplete(completed({ football: true }), "football")).toBe(true);
  });

  it("reads a plain step from its own flag", () => {
    expect(stepComplete(completed({ dcf: true }), "dcf")).toBe(true);
    expect(stepComplete(completed(), "dcf")).toBe(false);
  });

  it("treats analyses complete when any of its three tabs is done", () => {
    expect(stepComplete(completed(), "analyses")).toBe(false);
    expect(stepComplete(completed({ scenarios: true }), "analyses")).toBe(true);
    expect(stepComplete(completed({ sensitivity: true }), "analyses")).toBe(true);
    expect(stepComplete(completed({ reverse: true }), "analyses")).toBe(true);
  });
});
