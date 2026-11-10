# Stock Valuation Frontend — Design Specification

Nov 1, 2026 · 

## Overview

Build a Persian, right-to-left, dark-theme web app that wraps the existing FastAPI valuation backend in a guided workflow for university students. The backend is finished and is the single source of truth for every calculation; the frontend never re-implements a formula.

**Audience:** university students learning equity valuation, not professional analysts. Every screen explains what the model does and when to use it.

**Scope:** 13 equity models, WACC, a six-step DCF workflow, relative valuation, a football-field summary, and portfolio optimization. Auth, saved projects and live market data are out of scope for v1.

**What the backend already provides**

| Group | Base path | Endpoints |
| --- | --- | --- |
| Common equity | `/api/valuation` | `single-period`, `zero-growth`, `annual-dividend-yield`, `gordon`, `supernormal-growth`, `dividend-projection`, `expected-return`, `capm`, `preferred-stock`, `risk-premium`, `growth-opportunities`, `sustainable-growth`, `peg` |
| Cost of capital | `/api/valuation` | `wacc` |
| DCF | `/api/valuation` | `forecast`, `dcf`, `dcf-scenarios`, `dcf-sensitivity`, `reverse-dcf` |
| Relative valuation | `/api/valuation` | `multiples`, `football-field` |
| Portfolio | `/api/portfolio` | `statistics`, `optimize` |
| Health | root | `GET /health` |

All calculation endpoints are `POST` with JSON bodies. Interactive API docs are served at `/docs` and the machine-readable schema at `/openapi.json`.

## Design principles and visual language

The look is a calm, serious financial-analysis tool: dense enough to be useful, quiet enough to study with. No gradients, glassmorphism or stock photos.

**Principles**

1. Explain before you compute: every model page says what it does, when to use it, and shows its formula.
2. Results update live as the student types; there is no "Calculate" button.
3. Show the parts, not only the answer: every result page breaks the number into its components.
4. Never rely on color alone: pair color with an icon or a text label.
5. One page template for every model, so a screen is built once and reused.

**Language and direction**

- Persian, RTL by default. Numbers, formulas and variable names (WACC, EV, NPVGO, D₀) stay LTR inside RTL text.
- Numbers use a tabular monospace font so columns align. Display Latin digits in numeric cells; offer a Persian-digit toggle in settings.
- Text font: Vazirmatn. Numbers and formulas: JetBrains Mono.

**Theme**

Dark is the default; a light theme is a later option. Define every color as a CSS variable from day one so a second theme is a variable swap, not a rewrite.

**Color tokens (dark theme)**

| Token | Hex | Use |
| --- | --- | --- |
| `--bg` | `#0F1420` | App background |
| `--surface` | `#171E2E` | Cards, panels |
| `--border` | `#263047` | 1px card borders |
| `--text` | `#E6EAF2` | Primary text |
| `--text-muted` | `#8C96AB` | Labels, hints |
| `--primary` | `#4C8DC9` | Buttons, links, main chart series |
| `--positive` | `#4CAF7A` | Undervalued, upside, success |
| `--negative` | `#E5645F` | Overvalued, downside, error |
| `--warning` | `#E0A33A` | Cautions, out-of-range states |

**Shape and spacing:** 12px card radius, 8px spacing grid, 24px gap between the input and results columns. Body text 15px minimum, table numbers 14px.

**Semantic mapping to the backend.** The PEG interpretation returns a `level` of `success`, `info`, `warning` or `error`. Map these one-to-one to positive, primary, warning and negative, each with an icon. The football-field `market_position` values `below`, `inside` and `above` map to negative, neutral and positive colors, with a text label on each bar.

## Information architecture

The app has two modes: a guided six-step workflow for company valuation, and standalone tools that need no workflow. A right-hand sidebar (RTL) holds both, and a stepper across the top of the main area shows workflow progress.

**Guided workflow (default path)**

Each step passes its output to the next with one button, so the student never retypes numbers. Steps 2 and 4 are optional shortcuts that can be skipped.

1. **Forecast** (`/forecast`): revenue and margin drivers produce yearly cash-flow rows. Button: "Send to DCF".
2. **WACC** (`/wacc`): capital structure and costs produce the discount rate. Optional CAPM helper for the cost of equity. Button: "Use in DCF".
3. **DCF** (`/dcf`): consumes the forecast rows and the WACC; produces enterprise value and value per share.
4. **Analyses** on the same inputs, as three tabs:
   - Scenarios (`/dcf-scenarios`): probability-weighted bear, base and bull cases.
   - Sensitivity (`/dcf-sensitivity`): WACC by terminal-growth heatmap.
   - Reverse DCF (`/reverse-dcf`): the terminal growth the market price implies.
5. **Peer multiples** (`/multiples`): P/E, P/B, P/S, EV/EBITDA, EV/Sales.
6. **Football field** (`/football-field`): collects the ranges from steps 4 and 5 and compares them with the market price.

**Standalone tools (sidebar groups)**

| Group | Pages |
| --- | --- |
| Common equity | Single-period, Zero growth, Gordon, Supernormal growth, Dividend projection, Expected return, CAPM, Preferred stock, Risk premium, Growth opportunities, Sustainable growth, PEG, Annual dividend yield |
| Portfolio | Statistics from prices, Optimizer |

**Shared workflow state.** Keep one client-side workflow store holding the forecast rows, WACC, balance-sheet fields (cash, debt, minority interest, preferred equity, shares, tax rate) and market price. Every workflow page reads from it and writes back to it. Persist it in `localStorage` so a refresh does not lose a student's work, and provide a "Reset workflow" action.

**Home screen.** A flow diagram of the six steps with a status chip on each ("Not started" or "Complete"), two cards for the standalone groups, and a "Start with a sample" button that fills the workflow with the reference numbers used in the backend tests.

## Page template

Every model page uses the same two-column layout at 1440px wide: an input column on the right (about 35%) and a results column on the left (about 65%). Build this once as a layout component.

**Input column**

- A short title and a one-sentence "When is this model suitable?" box.
- Form fields with a Persian label, a unit beside the field (%, ریال, number of shares) and a small ⓘ button that opens a tooltip with the field's meaning and its valid range.
- A "Sample values" button that fills the form with the reference numbers from the backend tests. This doubles as a manual test for the developer.

**Results column, top to bottom**

1. The formula in LTR, for example `P = D₀(1+g) / (r − g)`.
2. One hero number, large, with its label (the price, the value per share, the WACC).
3. A row of small component cards (for Gordon: dividend yield and capital-gains yield).
4. The chart or table specific to the page.
5. Copy-result and CSV-export actions.

**Behavior**

- Calculate automatically 400 ms after the last keystroke (debounce) once the form is valid. Cancel any in-flight request when a newer one starts.
- Keep the previous result visible at 50% opacity while a new one loads, then swap. Use skeletons only for the first load.
- Persist each page's form values in `localStorage` so navigating away does not clear them.
- Fields that come from the workflow store show a chip such as "From step 1 ✓" and can be overridden; overriding detaches that field from the store.

## API contract rules

The most likely source of frontend bugs is unit handling, so this section is the one to read twice.

**Rule 1: students type percent, the API wants decimals**

Every rate field is a decimal in the request (12% is `0.12`). Forms show and accept percent; a single conversion layer divides by 100 before sending. Responses carry both forms (`required_return` and `required_return_percent`), so display the `_percent` field and never multiply on the client.

Two fields are percent already and must NOT be divided:

| Endpoint | Field | Unit sent |
| --- | --- | --- |
| `/risk-premium` | `bond_rate_percent` | Percent (8 means 8%); note that `required_return` in the same request is a decimal |
| `/peg` | `growth_rate_percent` | Percent (10 means 10%); must be greater than 0 and at most 100 |

Put the conversion in the generated field config (each field declares `unit: "rate"` or `unit: "percent-raw"`) so it is impossible to forget on a new page.

**Rule 2: two different error shapes**

| Status | Meaning | Body | UI treatment |
| --- | --- | --- | --- |
| 400 | The domain rejected the inputs or the math failed | `{ error_code, message, details }`; `error_code` is `VALIDATION_ERROR` or `CALCULATION_ERROR`; `message` is Persian; `details` is currently always null | Show `message` verbatim in a red banner above the results. Never replace it with a generic message. |
| 422 | The request shape is wrong (missing field, wrong type, unknown field) | FastAPI's standard `detail` array with `loc` and `msg` | Treat as a form bug: mark the field named in `loc`. It should be rare, because the client validates first. |

Request bodies reject unknown fields, so the client must send exactly the documented fields and nothing extra.

**Rule 3: validate on the client first, mirror only the simple rules**

The backend is the authority; the client only avoids pointless round trips. Mirror these and let everything else come back as a 400.

| Rule | Where it applies |
| --- | --- |
| Required return exceeds growth by at least 0.5 percentage points | Gordon, supernormal growth, sustainable growth |
| WACC exceeds terminal growth by at least 0.5 percentage points | DCF, scenarios, sensitivity base case |
| Growth rate between 0% and 200% (negative growth is rejected by the equity models) | Gordon, dividend projection, expected return, supernormal growth |
| Tax rate from 0% up to but excluding 100% | All FCFF and WACC pages |
| Terminal-year free cash flow must be positive | DCF family |
| Market return must exceed the risk-free rate | CAPM |
| 1 to 50 forecast years | Forecast, DCF |
| 2 to 5 scenarios, unique names, probabilities summing to 1 (tolerance 0.000001) | Scenarios |
| Odd number of grid points, 3 to 11 per axis | Sensitivity |
| At least 3 peers with a positive multiple; non-positive multiples are excluded, not errors | Peer multiples |
| 1 to 12 ranges, unique names, low ≤ mid ≤ high (negatives allowed) | Football field |
| 2 to 30 assets; at most 8 when short selling is off; at least 3 prices per asset, all positive, equal length | Portfolio |
| Periods per year is an integer from 1 to 366; frontier points 5 to 200; max leverage 0 to 3 | Portfolio |

**Rule 4: null means invalid, not zero.** Several responses return `null` on purpose: sensitivity cells that break a rule, retention-curve points, and reverse-DCF fields when the market price is outside the search range. Render `null` as a distinct empty state (hatched cell, chart gap), never as 0.

**Environment.** Read the API base URL from an environment variable (for example `VITE_API_BASE_URL`). In development the backend already allows `localhost` and `127.0.0.1` on ports 5173 and 3000; production origins are set with the backend's `ALLOWED_ORIGINS` variable.

## Screen specifications

Each screen below follows the page template. Only what is specific to the screen is listed. Field names are the backend's JSON names.

### Step 1: Forecast (`POST /forecast`)

- **Inputs:** `base_revenue`, `years` (1 to 50, slider), and five drivers: `revenue_growth`, `ebitda_margin`, `da_pct_revenue`, `capex_pct_revenue`, `nwc_pct_incremental_revenue`. Each driver has a segmented toggle, "Same for all years" or "Year by year". The first sends one number; the second shows one small input per year and sends a list whose length equals `years`.
- **Terminal-year normalization:** a checkbox that sets `normalize_terminal_year`. It requires `terminal_growth`, so enabling it reveals that field. Add a tooltip: the terminal value is built from the last explicit year, so that year should be sustainable (capex equal to depreciation).
- **Results:** a yearly table (year, revenue, growth %, EBITDA, EBITDA margin %, EBIT, depreciation, capex, ΔNWC), and a combo chart of revenue bars with an EBITDA-margin line.
- **Sign convention to explain in a tooltip:** capex is a positive outflow; ΔNWC is positive when working capital grows and turns negative when revenue shrinks.
- **Hand-off:** "Send to DCF" stores the response's `projections` array in the workflow store. It already has the exact shape `/dcf` expects.

### Step 2: WACC (`POST /wacc`)

- **Inputs:** `equity` (must be positive), `debt` (zero allowed), `cost_of_equity`, `cost_of_debt`, `tax_rate`.
- **CAPM helper:** a button beside cost of equity opens a small popover with risk-free rate, beta and market return, calls `/capm`, and fills the field with `required_return`.
- **Results:** hero `wacc_percent`; a donut chart of `equity_weight_percent` and `debt_weight_percent`; cards for after-tax cost of debt and total capital; formula `WACC = (E/V)·rₑ + (D/V)·r_d·(1 − t)`.
- **Hand-off:** "Use in DCF" writes WACC to the workflow store.

### Step 3: DCF (`POST /dcf`)

- **Inputs:** `wacc`, `terminal_growth`, `tax_rate`, `shares_outstanding`, `cash`, `debt`, `minority_interest`, `preferred_equity`. The projections come from the store and show a chip "Forecast from step 1 ✓" with an "Edit rows" link to a plain editable table.
- **Results:** hero `value_per_share`, with `enterprise_value` and `equity_value` beside it.
- **Waterfall chart** from enterprise value through plus cash, minus debt, minus minority interest and minus preferred equity to equity value. Positive steps use the positive color, negative steps the negative color.
- **Terminal-value share bar** from `terminal_value_share_percent`. Switch to the warning color with a caution icon above 80%, with the note that most of the value depends on the terminal assumption.
- **Yearly table** (EBIT, NOPAT, depreciation, capex, ΔNWC, FCFF, discount factor, present value) with horizontal scroll, and a formula strip for FCFF and terminal value.
- **Negative equity value is valid** (debt can exceed enterprise value). Show it in the negative color with an explanation, not as an error.

### Step 4a: Scenarios (`POST /dcf-scenarios`)

- **Inputs:** two to five scenario cards, each with `name`, `probability`, `wacc`, `terminal_growth` and its own projections ("Copy from forecast" button). Shared fields: `shares_outstanding`, `tax_rate`, balance sheet, optional `market_price`.
- **Live probability total** beside the scenario list: "Total: 100% ✓" in the positive color, otherwise the total in the negative color. The backend accepts a total within 0.000001 of 1 and does not normalize.
- **Results:** a table per scenario (value per share, probability, weighted value, upside %); stat cards for `expected_value_per_share`, `std_dev_value_per_share`, best and worst scenario names, and with a market price, `expected_upside_percent` and `probability_of_upside_percent`.
- **Chart:** bars of value per share per scenario, bar width or label showing probability, with a dashed vertical or horizontal line at the market price.
- A zero-probability scenario is still valued and must still be valid.

### Step 4b: Sensitivity (`POST /dcf-sensitivity`)

- **Inputs:** the DCF fields plus `wacc_step` (default 1%), `growth_step` (default 0.5%), `wacc_points` and `growth_points` (3, 5, 7, 9 or 11; default 5). Steps are decimals on the wire.
- **Heatmap:** rows are `wacc_values_percent`, columns are `growth_values_percent`, cells are `value_per_share`. Outline the cell at `base_row`, `base_col` and tag it "Base case". Color cells green above the base value and red below it.
- **`null` cells** (WACC and growth too close, or WACC not positive) are grey with diagonal hatching and a tooltip "Invalid combination". Never color them as zero.
- **Toggle** between value per share and `enterprise_value` matrices. Footer: "`valid_cells` of `total_cells` cells valid".
- **Hand-off:** "Send range to football field" computes low as the minimum non-null cell, mid as `base_value_per_share`, high as the maximum non-null cell.

### Step 4c: Reverse DCF (`POST /reverse-dcf`)

- **Inputs:** projections, `wacc`, `shares_outstanding`, `tax_rate`, `market_price`, balance sheet, and an optional `terminal_growth` (the student's own estimate, used only for the gap).
- **When `status` is `solved`:** a large sentence from `message` (for example, the market assumes about 2.1% terminal growth). Below it, a horizontal range bar from `search_min_growth` to `search_max_growth` with a marker at `implied_growth_percent` and a second marker at the student's own estimate, the gap labeled with `growth_gap_percent`. Side cards: `enterprise_value`, `equity_value`, `terminal_value_share_percent`.
- **When `status` is `market_price_below_range` or `market_price_above_range`:** this is a normal result, not an error. Show an amber card with `message`, and the values per share at the two search bounds so the student sees why the price falls outside.

### Step 5: Peer multiples (`POST /multiples`)

- **Inputs:** tabs for `kind` (`pe`, `pb`, `ps`, `ev_ebitda`, `ev_sales`). The `metric` label changes with the tab: net income, book equity, revenue, EBITDA, sales. Show cash, debt, minority interest and preferred equity only for the two EV tabs; the backend ignores them otherwise.
- **Peers table:** editable rows of `name` and `value`, an "Add peer" button, unique names. A peer with a non-positive multiple is allowed; after the response, grey out the names in `excluded_names` with the tag "Excluded". At least three valid peers are needed.
- **Results:** a box plot of the peer multiples marking `q1`, `median`, `q3`, `mean`, `min` and `max`; four cards (low = Q1, mid = median, high = Q3, mean) each showing the multiple used, the implied enterprise value for EV kinds, equity value, and value per share.
- **Hand-off:** "Send range to football field" uses `low`, `mid`, `high` value per share.

### Step 6: Football field (`POST /football-field`)

- **Inputs:** an optional `market_price` and a list of ranges, each with `method`, `low`, `mid`, `high`. Ranges arrive from earlier steps as chips ("From sensitivity", "From scenarios", "From multiples") and can also be added or edited by hand. Scenarios supply `min_value_per_share`, `expected_value_per_share`, `max_value_per_share`. One to twelve ranges, unique names.
- **Chart:** one horizontal bar per method from low to high with a diamond at mid, a dashed vertical line at the market price, and a translucent band for the overlap region from `overlap_low` to `overlap_high` when `has_overlap` is true. Tint each bar and add a text label by `market_position` (`below`, `inside`, `above`).
- **Summary cards:** `overall_low` to `overall_high`, `median_of_mids`, `mean_of_mids`, and "Market price inside the overlap" from `market_price_in_overlap`.
- **Actions:** export the chart as PNG and copy a text summary.

### Portfolio statistics (`POST /api/portfolio/statistics`)

- **Inputs:** a paste area for a price table (first row asset names, one column per asset, rows in time order), or CSV upload. The client parses it into one price list per asset. The frontend is responsible for aligning dates across assets; the backend assumes equal-length aligned series. Periods per year is a preset selector (daily 252, weekly 52, monthly 12, yearly 1) with a custom integer from 1 to 366.
- **Results:** annual mean return, volatility, covariance table and a correlation heatmap. `observations` is the number of returns, one fewer than the number of prices.
- **Hand-off:** "Use in optimizer" fills asset names, mean returns and covariance.

### Portfolio optimizer (`POST /api/portfolio/optimize`)

- **Inputs:** asset names, mean returns, covariance matrix (from statistics or entered by hand), `risk_free_rate`, `risk_aversion` (A, above 0), `allow_short` toggle, `max_leverage` slider from 0 to 3, `frontier_points` from 5 to 200. With short selling off, show a notice that at most 8 assets are supported.
- **Scatter chart:** x is volatility, y is expected return. Plot each asset as a labeled dot, the efficient frontier as a smooth curve, the minimum-variance, tangency and equal-weight portfolios as distinct markers, and the capital allocation line through its two points.
- **Complete portfolio card:** `tangency_weight_percent`, `risk_free_weight_percent`, risky weights per asset, expected return and volatility. Show a badge when `leverage_capped` is true. `clipped_to_zero` should rarely occur; if it does, show an informational note.
- **Weights:** stacked horizontal bars for each portfolio's weights. Negative weights (short positions) extend left of zero.
- A 400 here is common (for example, a risk-free rate above every return makes the tangency portfolio undefined). Show the Persian message as is.

### Standalone equity models

All use the page template with a formula, a hero number and component cards.

| Page (endpoint) | Inputs | Hero | Extra elements |
| --- | --- | --- | --- |
| Single period (`/single-period`) | `d1`, `p1`, `r` | `p0` | Split bar of `pv_dividend` and `pv_terminal_price` |
| Zero growth (`/zero-growth`) | `d`, `r` | `price` | Dividend yield percent |
| Annual dividend yield (`/annual-dividend-yield`) | `dividend`, `price` | Yield percent | None |
| Gordon (`/gordon`) | `d0`, `g`, `r` | `price` | Dividend yield and capital-gains yield cards; 10-year dividend line from `/dividend-projection` |
| Supernormal growth (`/supernormal-growth`) | `d0`, `growth_rates` (one input per year; count must equal `years`), `years`, `g_constant`, `r` | `p0` | `schedule` table with a terminal row; bar of PV of dividends vs PV of terminal price |
| Dividend projection (`/dividend-projection`) | `d0`, `g`, `periods` | Last dividend | Line chart of `dividends` |
| Expected return (`/expected-return`) | `d1`, `p0`, `g` | `total_percent` | Stacked bar of dividend yield and capital-gains yield |
| CAPM (`/capm`) | `risk_free_rate`, `beta`, `market_return` | `required_return_percent` | Market and stock risk-premium cards; security market line chart |
| Preferred stock (`/preferred-stock`) | `d`, `r` | `price` | Dividend yield percent |
| Risk premium (`/risk-premium`) | `required_return` (decimal), `bond_rate_percent` (raw percent) | `risk_premium_percent` | Bar comparing stock return with bond rate |
| Growth opportunities (`/growth-opportunities`) | `eps`, `r`, `npvgo` (may be negative) | `total_value` | Stacked bar of `no_growth_value` and `npvgo`; `growth_share_percent` |
| Sustainable growth (`/sustainable-growth`) | `eps`, `r`, `roe`, `retention_ratio` (0 up to but excluding 1) | `price` | Payout, growth, NPVGO, justified P/E; badge from `growth_creates_value`; retention-curve line over `retention_curve`, with `null` price points drawn as gaps |
| PEG (`/peg`) | `pe_ratio`, `growth_rate_percent` (raw percent, up to 100) | `peg` | Interpretation banner colored by `interpretation.level`, text from `interpretation.message` |

## UX details

**States every page needs**

| State | Behavior |
| --- | --- |
| Empty (nothing entered) | Show the formula and explanation with a "Try sample values" button; no empty chart frames |
| Incomplete form | Results area shows "Fill in the highlighted fields"; no request is sent |
| Loading | Skeleton on first load; dimmed previous result on updates |
| 400 domain error | Red banner with the Persian `message` verbatim; keep the form and previous inputs |
| 422 shape error | Mark the field from `loc`; log to the console in development |
| Network or server failure | Banner "Cannot reach the server" with a Retry button; check `/health` |
| `null` values | Hatched cell or chart gap, never zero |

**Teaching aids (the audience is students)**

- Every field has an ⓘ tooltip with meaning, typical range and an example.
- Each result page has a collapsible "How to read this result" panel of two or three plain sentences.
- Warnings are explained, not only flagged: terminal value above 80% of enterprise value, negative equity value, ROE below required return (growth destroys value).

**Export:** copy the hero result as text, download any table as CSV, export the football-field and portfolio charts as PNG.

**Responsive behavior**

- Desktop (1200px and wider): two columns as specified.
- Tablet (768 to 1199px): sidebar collapses to icons; columns stay side by side.
- Mobile (under 768px): input column stacks above results; sidebar becomes a drawer; wide tables and the heatmap scroll horizontally inside their card.

**Accessibility**

- Text contrast at WCAG AA on the dark theme (check muted text against the surface color).
- Full keyboard navigation and visible focus rings.
- Every chart has a text summary or data table for screen readers.
- Status never depends on color alone (icon or label with every red or green).
- Respect `prefers-reduced-motion`; keep animations under 200 ms.

## Tech stack, build order and acceptance

**Recommended stack**

| Concern | Choice | Reason |
| --- | --- | --- |
| Framework | React, Vite, TypeScript | Matches the backend's stated React target |
| UI components | shadcn/ui or Mantine | Both support RTL and dark themes |
| Charts | Apache ECharts | Native heatmap, box plot, scatter and custom series for the waterfall and football field |
| Forms | `react-hook-form` with `zod` | Typed validation that mirrors the backend rules |
| Server state | TanStack Query | Debounced mutations, cancellation, retries |
| Workflow store | Zustand with persistence | Small, supports `localStorage` |
| Fonts | Vazirmatn and JetBrains Mono, self-hosted | No third-party font requests |

**Types from the backend.** Generate TypeScript types from `/openapi.json` (for example with `openapi-typescript`) so request and response types never drift from the Pydantic models. Do not hand-write response types.

**Suggested build order**

1. Project setup: RTL, dark tokens as CSS variables, fonts, API client with the 400 and 422 handling from the contract section, percent-to-decimal field config.
2. The page template component, then one simple page end to end (Gordon) to prove the template, the conversion layer and the error states.
3. The remaining standalone equity pages, which are mostly configuration.
4. Workflow store, then Forecast, WACC and DCF with the waterfall.
5. Scenarios, Sensitivity heatmap and Reverse DCF.
6. Peer multiples and the Football field.
7. Portfolio statistics and optimizer.
8. Home screen, sample-data buttons, export, responsive and accessibility pass.

The Football field and the DCF waterfall carry the most custom chart work, so prototype them early.

**Acceptance checklist**

- [ ] Typing 12 in a rate field sends `0.12`, except `bond_rate_percent` and `growth_rate_percent`, which send the raw number.
- [ ] Every page's "Sample values" button reproduces the reference numbers from the backend tests (for example Gordon with 1.5, 5%, 12% gives 22.50; WACC with 600, 400, 12%, 6%, 25% gives 9.00%).
- [ ] A 400 shows the Persian message verbatim; a 422 marks the offending field.
- [ ] `null` sensitivity cells render hatched, not as zero.
- [ ] Reverse DCF with an out-of-range price shows the amber state, not an error.
- [ ] The workflow survives a page refresh and "Send to DCF" and "Use in DCF" fill the DCF page.
- [ ] Layout is correct in RTL with LTR numbers and formulas at 1440, 1024 and 390 px widths.
- [ ] All text and chart colors pass AA contrast.
