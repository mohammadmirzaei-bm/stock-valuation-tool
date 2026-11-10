import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { SidebarNav } from "./Sidebar";

const renderAt = (url: string) =>
  render(
    <MemoryRouter initialEntries={[url]}>
      <SidebarNav />
    </MemoryRouter>,
  );

describe("SidebarNav — step 4 lists its three analysis tabs", () => {
  it("renders one link per analysis tab under the workflow", () => {
    renderAt("/");
    expect(screen.getByRole("link", { name: "سناریوها" })).toHaveAttribute("href", "/analyses?tab=scenarios");
    expect(screen.getByRole("link", { name: "حساسیت" })).toHaveAttribute("href", "/analyses?tab=sensitivity");
    expect(screen.getByRole("link", { name: "DCF معکوس" })).toHaveAttribute("href", "/analyses?tab=reverse");
  });

  it("marks only the tab named in ?tab= as active", () => {
    renderAt("/analyses?tab=sensitivity");
    expect(screen.getByRole("link", { name: "حساسیت" }).className).toContain("sidebar-active");
    expect(screen.getByRole("link", { name: "سناریوها" }).className).not.toContain("sidebar-active");
  });

  it("defaults to scenarios when the query string is missing, like the page", () => {
    renderAt("/analyses");
    expect(screen.getByRole("link", { name: "سناریوها" }).className).toContain("sidebar-active");
    expect(screen.getByRole("link", { name: "حساسیت" }).className).not.toContain("sidebar-active");
  });
});
