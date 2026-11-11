# Portfolio Sample Data — Statistics → Efficient Frontier

Deterministic, self-consistent sample data for the portfolio flow:
`POST /api/portfolio/statistics` → `POST /api/portfolio/optimize`
(UI: **آماره سبد از قیمت‌ها** → **بهینه‌ساز سبد**).

| File | Purpose |
|---|---|
| `portfolio_prices.csv` | Price grid for the statistics page (tab-separated despite the `.csv` extension — the UI accepts both). |
| `portfolio_optimizer.csv` | Optimizer inputs: asset block + covariance block + parameter block. |

No random numbers are involved: prices come from a fixed closed-form construction
(drift + empirically orthonormalized sinusoid factors mixed by the Cholesky factor
of a target correlation matrix). The files are static, so every run, paste, and
test sees exactly the same data.

---

## 1. `portfolio_prices.csv` — statistics input

Format expected by `parsePriceGrid` (frontend) and `PortfolioStatisticsRequest` (API):

- **Row 1 (header):** asset names, one per column: `TECH  HLTH  BANK  OIL  GOLD  BOND`.
- **Rows 2–37:** one row per period, **oldest → newest**, 36 aligned monthly prices
  per asset (→ 35 returns). All prices are positive and finite, 4 decimals.
- Columns are separated by **tabs**; the parser also accepts commas.

**Use it:** paste the file into the statistics textarea or upload it via
«بارگذاری CSV», then set **دوره در سال (m) = 12** (monthly data).

### Asset design (annualized targets, arithmetic scaling)

| Asset | Role | Mean | Vol | Notable correlations |
|---|---|---|---|---|
| TECH | growth engine | 20% | 35% | +0.60 BANK, **−0.35 GOLD** |
| HLTH | defensive growth | 12% | 18% | +0.55 TECH, **+0.05 OIL (≈0)** |
| BANK | cyclical value | 10% | 24% | +0.60 TECH, −0.25 GOLD |
| OIL | commodity | 8% | 30% | +0.10 TECH (≈0), +0.25 BANK |
| GOLD | crisis hedge | 6.5% | 16% | −0.35 TECH, +0.30 BOND |
| BOND | low-vol anchor | 6% | 10% | −0.20 TECH, +0.30 GOLD |

The strongly negative equity–gold pairs and near-zero equity–oil pairs give the
frontier a pronounced leftward bend (diversification visibly pays). Realized
statistics match these targets to ~1e-6; the annualized covariance is symmetric
positive definite (eigenvalues ≈ 0.0077 … 0.169, condition number ≈ 22).

**About `m`:** the data is designed for `periods_per_year = 12`. Annualization in
this app is arithmetic (`mean × m`, `cov × m`), so `m = 252` also works and stays
well-conditioned (correlations and eigenvectors are unchanged, eigenvalues scale
by 21) — but the means then read 420%, 252%, … which is only a unit artifact.
Use 12 for a presentable demo.

## 2. `portfolio_optimizer.csv` — optimizer input

Three comma-separated blocks, separated by blank lines. The optimizer page has
no CSV importer: copy the values into its fields, use the statistics page's
«استفاده در بهینه‌ساز» handoff button, or POST the JSON directly (mapping below).

**Block 1 — assets** (`asset,expected_return_pct,volatility_pct`):
one row per asset; expected annual return and annual volatility **in percent**
(e.g. `20.00` = 20%). The API/UI convert to decimals by dividing by 100.

**Block 2 — covariance** (`covariance,TECH,HLTH,…` header, then one row per asset):
annual covariance in **decimals** (e.g. `0.122500` = 35%²). Symmetric to the
digit, positive definite, and consistent with block 1: each diagonal entry equals
`(volatility_pct / 100)²` at the displayed precision (max deviation < 1e-16).
Off-diagonal = `ρᵢⱼ · σᵢ · σⱼ`, e.g. TECH–GOLD = −0.35 × 0.35 × 0.16 = −0.0196.

**Block 3 — parameters** (`parameter,value`):

| Parameter | Value | Meaning / domain limit |
|---|---|---|
| `risk_free_rate_pct` | 3 | annual risk-free rate in percent (API: 0.03, must be ≥ 0) |
| `risk_aversion` | 3.0 | A in `y* = (μ_T − rf) / (A · σ_T²)` (must be > 0) |
| `max_leverage` | 1.0 | cap on y* (0–3) |
| `frontier_points` | 50 | number of frontier points (5–200) |
| `allow_short` | false | long-only; max 8 assets (6 here ✓; 2–30 with shorts) |

**Wire mapping:** `mean_returns = expected_return_pct / 100`,
`risk_free_rate = risk_free_rate_pct / 100`; covariance and the remaining
parameters pass through unchanged. Example request body:

```json
{
  "asset_names": ["TECH", "HLTH", "BANK", "OIL", "GOLD", "BOND"],
  "mean_returns": [0.20, 0.12, 0.10, 0.08, 0.065, 0.06],
  "covariance": [
    [0.122500, 0.034650, 0.050400, 0.010500, -0.019600, -0.007000],
    [0.034650, 0.032400, 0.017280, 0.002700, -0.004320, 0.001800],
    [0.050400, 0.017280, 0.057600, 0.018000, -0.009600, -0.002400],
    [0.010500, 0.002700, 0.018000, 0.090000, 0.007200, -0.001500],
    [-0.019600, -0.004320, -0.009600, 0.007200, 0.025600, 0.004800],
    [-0.007000, 0.001800, -0.002400, -0.001500, 0.004800, 0.010000]
  ],
  "risk_free_rate": 0.03, "risk_aversion": 3.0,
  "allow_short": false, "max_leverage": 1.0, "frontier_points": 50
}
```

## 3. Expected reference outputs (verified against the live endpoints)

Statistics (`m = 12`): **35 observations**, means/vols as in the table above,
correlation matrix as designed (diagonal exactly 1).

Optimizer (long-only, parameters above):

- **Min-variance (GMV):** return **7.73%**, volatility **7.73%** — the leftmost
  frontier point. Weights ≈ BOND 54.8%, GOLD 20.6%, BANK 7.8%, HLTH 7.7%,
  TECH 5.6%, OIL 3.5%: the negative-correlation hedge pair dominates.
- **Tangency (max Sharpe):** return **9.80%**, volatility **9.23%**,
  **Sharpe ≈ 0.737**. Weights ≈ BOND 35.5%, GOLD 26.9%, TECH 19.0%, HLTH 15.9%,
  OIL 2.7%, **BANK 0%** — BANK is dominated and drops out of the long-only
  support (with `allow_short = true` it goes to ≈ −1.8% instead).
- **Complete portfolio:** uncapped `y* = (0.0980 − 0.03) / (3 × 0.0923²) ≈ 2.66`,
  so **y\* is capped at max_leverage = 1.0** (`leverage_capped = true`, the UI
  shows the «به سقف اهرم رسید» badge). Risk-free weight 0%; the complete
  portfolio coincides with the tangency: **9.80% return / 9.23% volatility**.
- **Efficient frontier:** 50 points arcing from the GMV (7.73%, 7.73%) up to
  pure TECH (20.00%, 35.00%) — a visibly curved, non-flat frontier.
- **Capital allocation line:** dashed line from (0%, 3%) through the tangency
  with slope 0.737, drawn out to 2× the tangency volatility (≈18.5%).
- **Equal-weight benchmark:** 10.42% return / 12.29% volatility, Sharpe 0.603 —
  sits below the CAL, so the optimization visibly beats the naive benchmark.

## 4. Internal consistency (verified)

- The optimizer CSV's return/volatility/covariance blocks were generated from
  `statistics_from_prices` run on the **exact rounded prices** in
  `portfolio_prices.csv` — not from idealized targets.
- Feeding the statistics response straight into `/optimize` (the UI handoff)
  reproduces the CSV-driven result: max difference on returns, volatilities and
  y* ≈ **1.1e-7** (display rounding only).
- Both endpoints return HTTP 200 for `m = 12` and `m = 252`, and for
  `allow_short` both false and true; the frontend `parsePriceGrid` accepts the
  price file with 0 dropped rows (6 series × 36 prices).