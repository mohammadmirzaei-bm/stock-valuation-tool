import { describe, it, expect, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { HomeDiagram } from "./HomeDiagram";
import { useWorkflow } from "@/store/workflow";
import { WORKFLOW_STEPS } from "@/config/models";

const renderDiagram = () =>
  render(
    <MemoryRouter>
      <HomeDiagram />
    </MemoryRouter>,
  );

describe("HomeDiagram — connected six-step flow", () => {
  beforeEach(() => useWorkflow.getState().reset());

  it("renders a node per step, each with an icon+text status chip", () => {
    renderDiagram();
    expect(screen.getAllByText("شروع نشده")).toHaveLength(WORKFLOW_STEPS.length);
    expect(screen.getByText("پیش‌بینی")).toBeInTheDocument();
    expect(screen.getByText("زمین فوتبال")).toBeInTheDocument();
  });

  it("connects the six nodes with five arrows between them", () => {
    const { container } = renderDiagram();
    expect(container.querySelectorAll('li[aria-hidden="true"]')).toHaveLength(WORKFLOW_STEPS.length - 1);
  });

  it("fans step 4 out into its three sub-analysis branches", () => {
    renderDiagram();
    expect(screen.getByText("سناریوها")).toBeInTheDocument();
    expect(screen.getByText("حساسیت")).toBeInTheDocument();
    expect(screen.getByText("DCF معکوس")).toBeInTheDocument();
  });

  it("marks a completed step with «کامل» (icon + text, never color alone)", () => {
    useWorkflow.getState().completeStep("dcf");
    renderDiagram();
    expect(screen.getAllByText("کامل")).toHaveLength(1);
    expect(screen.getAllByText("شروع نشده")).toHaveLength(WORKFLOW_STEPS.length - 1);
  });
});
