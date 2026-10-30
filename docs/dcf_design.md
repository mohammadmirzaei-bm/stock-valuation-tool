# DCF / WACC — Final design

Formulas live only in `stock_valuation/domain/`. API maps JSON ↔ domain.
Streamlit UI for these models is **out of scope** for this change.

---

## 1. Decision table (final)

| ID | Decision | Status |
|---|---|---|
| D1 | Discount at end of year: year *t* uses `(1+r)^t`, *t*=1..*n* (year = list index) | Locked |
| D2 | Capex & ΔNWC positive = cash outflow; `FCFF = EBIT(1−t)+Dep−Capex−ΔNWC` | Locked |
| D3 | `TV = FCFF_n(1+g)/(WACC−g)`; `PV(TV) = TV/(1+WACC)^n` | Locked |
| D4 | `Equity = EV + cash − debt − minority_interest − preferred_equity` (last two default 0). Negative equity / per-share allowed. | Locked |
| D5 | Rates as decimals; only `*_percent` are %; no rounding in domain | Locked |
| D6 | Reuse `MIN_SPREAD` (0.005) for `WACC − g` via WACC-labelled validator | Locked |
| D7 | Reject terminal FCFF ≤ 0 | Locked |
| D8 | No Pydantic in domain; `CashFlowProjection` dataclass; route maps input | Locked |
| D9 | API results via `model_validate(..., from_attributes=True)`; field names = domain; no `model_copy` | Locked |
| D10 | `projections` length ∈ [1, 50] in **both** domain and Pydantic structure. Numeric bounds (`tax_rate`, shares, cash, …) are **domain-only** so bad numbers return Persian HTTP 400, not 422. | Locked |
| D11 | `terminal_value_share_percent = pv_terminal_value / EV × 100` (0 if EV == 0) | Locked |
| A1 | No `/fcff` endpoint; `/dcf` takes raw line items only | Locked |
| A2 | `CashFlowProjection`: `ebit`, `depreciation`, `capex`, `delta_nwc` only (no `year`, no per-row `tax_rate`) | Locked |
| A3 | Single global `tax_rate` on `dcf_valuation` | Locked |
| A5 | Zero debt valid; `debt ≥ 0`, `cost_of_debt ≥ 0`, `equity > 0`, `cost_of_equity > 0` | Locked |
| A8 | WACC spread wrapper uses `1e-12` float tolerance; Gordon validator unchanged | Locked |

---

## 2. Function signatures

```python
def calculate_fcff(
    ebit: float,
    tax_rate: float,
    depreciation: float,
    capex: float,
    delta_nwc: float,
) -> float: ...

def wacc(
    equity: float,
    debt: float,
    cost_of_equity: float,
    cost_of_debt: float,
    tax_rate: float,
) -> float: ...

def wacc_breakdown(
    equity: float,
    debt: float,
    cost_of_equity: float,
    cost_of_debt: float,
    tax_rate: float,
) -> WaccBreakdown: ...

def dcf_valuation(
    projections: list[CashFlowProjection],
    wacc_rate: float,
    terminal_growth: float,
    shares_outstanding: float,
    tax_rate: float,
    cash: float = 0.0,
    debt: float = 0.0,
    minority_interest: float = 0.0,
    preferred_equity: float = 0.0,
) -> DcfBreakdown: ...
```

**Cost of equity:** callers may use `capm_required_return` / `capm_breakdown`. CAPM is **not** inside `wacc()`.

API request field `wacc` maps to domain parameter `wacc_rate`.

---

## 3. Dataclass fields

All `@dataclass(frozen=True)`.

### `CashFlowProjection`

| Field | Type | Meaning |
|---|---|---|
| `ebit` | `float` | EBIT for the year |
| `depreciation` | `float` | Non-cash charges |
| `capex` | `float` | Capex outflow as positive |
| `delta_nwc` | `float` | NWC increase as positive (reduces FCFF) |

Year index = position in the list (1..n).

### `WaccBreakdown`

`wacc`, `equity`, `debt`, `total_capital`, `equity_weight`, `debt_weight`,
`cost_of_equity`, `cost_of_debt`, `after_tax_cost_of_debt`, `tax_rate`

**Properties:** `wacc_percent`, `cost_of_equity_percent`, `cost_of_debt_percent`,
`after_tax_cost_of_debt_percent`, `tax_rate_percent`, `equity_weight_percent`,
`debt_weight_percent`.

### `FcffYearRow`

`year`, `ebit`, `nopat`, `depreciation`, `capex`, `delta_nwc`, `fcff`,
`discount_factor`, `present_value`

### `DcfBreakdown`

`enterprise_value`, `equity_value`, `value_per_share`, `wacc`, `terminal_growth`,
`terminal_value`, `pv_terminal_value`, `pv_fcff_total`, `cash`, `debt`,
`minority_interest`, `preferred_equity`, `shares_outstanding`,
`terminal_value_share_percent`, `years`

**Properties:** `wacc_percent`, `terminal_growth_percent`.

---

## 4. Validation (Persian, domain source of truth)

| Rule | Message tone |
|---|---|
| Tax `0 ≤ t < 1` | `❌ نرخ مالیات باید بین 0 و 1 (غیرشامل) باشد!` |
| Equity > 0 | `❌ ارزش حقوق صاحبان سهام باید مثبت باشد!` |
| Debt / cash / MI / preferred ≥ 0 | `❌ … باید نامنفی باشد!` |
| Cost of equity > 0; cost of debt ≥ 0 | field-named `باید مثبت/نامنفی باشد!` |
| WACC > 0; shares > 0 | same pattern |
| `g ≥ WACC` | `❌ نرخ WACC (x%) باید بیشتر از نرخ رشد پایانی (y%) باشد!` |
| `WACC − g < MIN_SPREAD − 1e-12` | spread message naming WACC and نرخ رشد پایانی |
| Terminal FCFF ≤ 0 | `❌ جریان نقدی آزاد پایانی باید مثبت باشد؛ مدل رشد گوردون در غیر این صورت بی‌معناست!` |
| Projections length | `❌ حداقل یک سال…` / `❌ تعداد سال‌های پیش‌بینی نباید بیشتر از 50 باشد!` |
| Non-finite input | `❌ {field} باید عدد متناهی باشد!` |
| Non-finite result | `CalculationError("نتیجه محاسبه نامعتبر است")` |

**Pydantic:** `_RequestBase` + `extra="forbid"`; `projections` `min_length=1`, `max_length=50` only. **No** `gt`/`ge`/`lt` on rates, tax, shares, cash, debt.

**A8:** Existing `validate_growth_rate_vs_return` unchanged. New
`validate_terminal_growth_vs_wacc` adds `_WACC_SPREAD_TOLERANCE = 1e-12` so
intended `MIN_SPREAD` boundaries are not rejected by binary float noise
(e.g. `0.09 − 0.085`).

---

## 5. Endpoint contracts

### `POST /api/valuation/wacc`

```json
{
  "equity": 600,
  "debt": 400,
  "cost_of_equity": 0.12,
  "cost_of_debt": 0.06,
  "tax_rate": 0.25
}
```

Response mirrors `WaccBreakdown` (+ `*_percent` properties), e.g. `"wacc": 0.09`.

### `POST /api/valuation/dcf`

R4-equivalent request (tax_rate=0 and zero dep/capex/ΔNWC ⇒ FCFF = EBIT):

```json
{
  "projections": [
    {"ebit": 80, "depreciation": 0, "capex": 0, "delta_nwc": 0},
    {"ebit": 90, "depreciation": 0, "capex": 0, "delta_nwc": 0},
    {"ebit": 100, "depreciation": 0, "capex": 0, "delta_nwc": 0}
  ],
  "wacc": 0.09,
  "terminal_growth": 0.03,
  "shares_outstanding": 10,
  "tax_rate": 0,
  "cash": 50,
  "debt": 200,
  "minority_interest": 0,
  "preferred_equity": 0
}
```

Expected (unrounded): `enterprise_value ≈ 1551.9456835844344`,
`equity_value ≈ 1401.9456835844344`, `value_per_share ≈ 140.19456835844343`,
`terminal_value_share_percent ≈ 85.41417749298277`.

Route pattern:

```python
return s.WaccResult.model_validate(breakdown, from_attributes=True)
return s.DcfResult.model_validate(breakdown, from_attributes=True)
```

---

## 6. Reference values (tests)

| Case | Expected |
|---|---|
| R1 FCFF(100, 0.25, 10, 15, 5) | 65 |
| R2 WACC(600, 400, 0.12, 0.06, 0.25) | 0.09; weights 0.6/0.4; after-tax rd 0.045 |
| R3 EBIT [100,100,100], r=0.10, g=0, t=0 | ΣPV FCFF ≈ 248.6851990984222; PV(TV) ≈ 751.3148009015775; EV ≈ 1000 |
| R4 EBIT [80,90,100], r=0.09, g=0.03, cash=50, debt=200, shares=10, t=0 | see §5 |
| Hand components → FCFF [65,74,84], r=0.10, g=0.02 | TV = 1071; assert via arithmetic in test comment |

---

## 7. Implemented checklist

1. Validators: `validate_non_negative`, `validate_tax_rate`,
   `validate_terminal_growth_vs_wacc`, `validate_projections_length`
2. Domain dataclasses + `calculate_fcff`, `wacc`, `wacc_breakdown`, `dcf_valuation`
3. Schemas + routes `/wacc` and `/dcf` (no `/fcff`)
4. Unit tests `TestFcff` / `TestWacc` / `TestDcf` + self-test smoke
5. README model + endpoint tables (14 endpoints); Streamlit UI deferred
