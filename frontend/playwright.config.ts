import { defineConfig, devices } from "@playwright/test";

/**
 * End-to-end smoke tests for the guided workflow.
 *
 * Two servers are started (reusing any already running one): the FastAPI
 * backend on :8000 and the Vite dev server on :5173. Specs live in `e2e/` and
 * use the `*.e2e.ts` suffix so vitest's default `*.test.ts`/`*.spec.ts` glob
 * never picks them up.
 *
 * Run with `npm run test:e2e`. If Chromium cannot find libnspr4/libnss3 on a
 * bare host, point LD_LIBRARY_PATH at a directory that has them (e.g. the
 * miniconda env's `lib/`) before running.
 */
const APP = "http://127.0.0.1:5173";
const API = "http://127.0.0.1:8000";

export default defineConfig({
  testDir: "./e2e",
  testMatch: "**/*.e2e.ts",
  timeout: 60_000,
  expect: { timeout: 15_000 },
  // The workflow shares one backend and one seeded localStorage state per test.
  fullyParallel: false,
  workers: 1,
  reporter: [["list"]],
  use: {
    baseURL: APP,
    locale: "fa-IR",
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: "python3 -m uvicorn stock_valuation.api.main:app --host 127.0.0.1 --port 8000",
      cwd: "..",
      url: `${API}/health`,
      reuseExistingServer: true,
      timeout: 120_000,
    },
    {
      command: "npm run dev -- --host 127.0.0.1 --port 5173 --strictPort",
      url: APP,
      reuseExistingServer: true,
      timeout: 120_000,
    },
  ],
});
