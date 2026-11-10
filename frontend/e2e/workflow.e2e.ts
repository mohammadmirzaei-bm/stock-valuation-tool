import { test, expect, type Page } from "@playwright/test";
import { REFERENCE_PROJECTIONS, BALANCE_SHEET_SAMPLE } from "../src/lib/samples";

/**
 * One smoke test per guided-workflow step: load the reference sample values and
 * assert the page's hero number. The three pinned references are the backend
 * fixtures — Gordon 22.50, WACC 9.00%, DCF 124.02 per share.
 */

/**
 * The shared store as steps 1–2 leave it. Cash/debt/shares/tax come from the
 * shared sample; minority interest and preferred equity are 0 because that is
 * the backend README fixture (EV 13,402.20 → 124.02 per share — the 50/25 the
 * app sample carries yields 123.27).
 */
const WORKFLOW_SAMPLE = {
  projections: REFERENCE_PROJECTIONS,
  projectionsDetached: false,
  waccPercent: 9,
  waccDetached: false,
  balanceSheet: {
    cash: BALANCE_SHEET_SAMPLE.cash,
    debt: BALANCE_SHEET_SAMPLE.debt,
    minorityInterest: 0,
    preferredEquity: 0,
    sharesOutstanding: BALANCE_SHEET_SAMPLE.shares_outstanding,
    taxRate: BALANCE_SHEET_SAMPLE.tax_rate,
  },
  marketPrice: 150,
};

/** Seed the persisted workflow store before the app boots. */
async function seedWorkflow(page: Page) {
  await page.addInitScript((state) => {
    window.localStorage.setItem("sv-workflow", JSON.stringify({ state, version: 0 }));
  }, WORKFLOW_SAMPLE);
}

/** The hero answer as a number (the UI appends `%` / thousands separators). */
async function heroNumber(page: Page): Promise<number> {
  const hero = page.getByTestId("hero-value");
  await expect(hero).toBeVisible();
  const text = (await hero.textContent()) ?? "";
  const digits = text.replace(/[^\d.-]/g, "");
  expect(digits, `hero text was "${text}"`).not.toBe("");
  return Number(digits);
}

test("step 1 — forecast sample builds the FCFF rows and sends them on", async ({ page }) => {
  await page.goto("/forecast");
  await expect(page.getByRole("table")).toBeVisible();
  await page.getByRole("button", { name: "ارسال به DCF" }).click();
  await expect(page.getByText("سطرها به گام ۳ ارسال شد")).toBeVisible();
});

test("step 2 — WACC sample is 9.00%", async ({ page }) => {
  await page.goto("/wacc");
  await page.getByRole("button", { name: "مقادیر نمونه", exact: true }).click();
  expect(await heroNumber(page)).toBeCloseTo(9, 2);
});

test("step 3 — DCF value per share is 124.02", async ({ page }) => {
  await seedWorkflow(page);
  await page.goto("/dcf");
  expect(await heroNumber(page)).toBeCloseTo(124.02, 2);
});

test("step 4 — analyses honours ?tab= and switches tabs", async ({ page }) => {
  await seedWorkflow(page);
  await page.goto("/analyses?tab=scenarios");
  await expect(page.getByTestId("hero-value")).toBeVisible();

  await page.getByRole("tab", { name: "حساسیت" }).click();
  await expect(page).toHaveURL(/tab=sensitivity/);
  await expect(page.getByText("رشد پایانی پایه")).toBeVisible();
});

test("step 5 — multiples sample produces a value per share", async ({ page }) => {
  await page.goto("/multiples");
  await page.getByRole("button", { name: "استفاده از مقادیر نمونه" }).click();
  expect(await heroNumber(page)).toBeGreaterThan(0);
});

test("step 6 — football field sample renders the overall range", async ({ page }) => {
  await page.goto("/football-field");
  await page.getByRole("button", { name: "استفاده از مقادیر نمونه" }).click();
  // The hero is a range ("low – high"), not a single number.
  await expect(page.getByTestId("hero-value")).toHaveText(/[–-]/);
});

test("reference — Gordon sample prices the share at 22.50", async ({ page }) => {
  await page.goto("/equity/gordon");
  await page.getByRole("button", { name: "مقادیر نمونه", exact: true }).click();
  expect(await heroNumber(page)).toBeCloseTo(22.5, 2);
});
