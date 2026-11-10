import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { PrerequisiteChecklist } from "./PrerequisiteChecklist";

describe("PrerequisiteChecklist", () => {
  it("falls back to the generic prompt when nothing is missing", () => {
    render(
      <MemoryRouter initialEntries={["/dcf"]}>
        <PrerequisiteChecklist missing={[]} />
      </MemoryRouter>,
    );
    expect(screen.getByText("برای دیدن نتیجه، فیلدهای مشخص‌شده را کامل کنید.")).toBeInTheDocument();
  });

  it("shows the prerequisite label and a step button for a cross-step gap", () => {
    render(
      <MemoryRouter initialEntries={["/analyses"]}>
        <PrerequisiteChecklist missing={["forecast"]} />
      </MemoryRouter>,
    );
    expect(screen.getByText("سطرهای پیش‌بینی")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /گام 1/ })).toBeInTheDocument();
  });

  it("navigates to the providing step when the button is clicked", () => {
    render(
      <MemoryRouter initialEntries={["/analyses"]}>
        <Routes>
          <Route path="/analyses" element={<PrerequisiteChecklist missing={["wacc"]} />} />
          <Route path="/wacc" element={<div>WACC PAGE</div>} />
        </Routes>
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByRole("button", { name: /گام 2/ }));
    expect(screen.getByText("WACC PAGE")).toBeInTheDocument();
  });

  it("focuses the inline field instead of navigating when already on the providing step", () => {
    render(
      <MemoryRouter initialEntries={["/dcf"]}>
        <Routes>
          <Route
            path="/dcf"
            element={
              <>
                <input id="prereq-shares" />
                <PrerequisiteChecklist missing={["shares"]} />
              </>
            }
          />
        </Routes>
      </MemoryRouter>,
    );
    const input = document.getElementById("prereq-shares") as HTMLInputElement;
    const focusSpy = vi.spyOn(input, "focus");
    fireEvent.click(screen.getByRole("button", { name: /رفتن به فیلد/ }));
    expect(focusSpy).toHaveBeenCalled();
  });

  it("lists local gaps as plain rows with no button", () => {
    render(
      <MemoryRouter initialEntries={["/multiples"]}>
        <PrerequisiteChecklist missing={[]} local={["دست‌کم ۳ همتا با ضریب مثبت وارد کنید."]} />
      </MemoryRouter>,
    );
    expect(screen.getByText("دست‌کم ۳ همتا با ضریب مثبت وارد کنید.")).toBeInTheDocument();
    expect(screen.queryByRole("button")).toBeNull();
  });
});
