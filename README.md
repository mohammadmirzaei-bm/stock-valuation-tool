# stock-valuation-tool

ابزار ارزیابی سهام بر اساس کتاب مدیریت مالی استفان راس.

منطق محاسباتی در لایه دامنه خالص (`stock_valuation/domain/`) زندگی می‌کند و
تنها از یک مسیر در دسترس است:

- **سرویس FastAPI** (`stock_valuation/api/`) — قرارداد JSON برای فرانت‌اند React

رابط Streamlit نسخه اول (`stock_cla_developed.py` و `stock_valuation/ui/`) از
مخزن حذف شده و دارایی‌های ظاهری آن در `frontend/` برای پروژه React نگه داشته
می‌شوند.

سرویس API همان توابع خالص لایه دامنه را صدا می‌زند و هیچ فرمولی در لایه HTTP
دوباره پیاده‌سازی نمی‌شود.

## مدل‌های پشتیبانی‌شده

| مدل | فرمول | تابع | ماژول دامنه |
|---|---|---|---|
| تک‌دوره‌ای | `P₀ = (D₁ + P₁) / (1 + r)` | `single_period_model` | `equity` |
| رشد صفر | `P = D / r` | `zero_growth_model` | `equity` |
| رشد ثابت (گوردون) | `P = D₀(1+g) / (r - g)` | `constant_growth_model` | `equity` |
| رشد غیرعادی | `P₀ = Σ Dₜ/(1+r)ᵗ + Pₙ/(1+r)ⁿ` | `supernormal_growth_model` | `equity` |
| بازده مورد انتظار | `r = D₁/P₀ + g` | `expected_return` | `equity` |
| بازده مورد انتظار (CAPM) | `r = rf + β(rm − rf)` | `capm_required_return` | `equity` |
| سهام ممتاز | `P = D / r` | `preferred_stock_valuation` | `equity` |
| فرصت‌های رشد | `P = EPS/r + NPVGO` | `growth_opportunities_valuation` | `equity` |
| رشد پایدار و NPVGO | `g = b × ROE`، `P = EPS₁(1−b)/(r−g)` | `sustainable_growth_valuation` | `equity` |
| نسبت PEG | `PEG = (P/E) / g` | `peg_ratio` | `equity` |
| WACC | `WACC = (E/V)rₑ + (D/V)r_d(1−t)` | `wacc` | `cost_of_capital` |
| DCF (FCFF) | `EV = Σ FCFFₜ/(1+WACC)ᵗ + TV/(1+WACC)ⁿ` | `dcf_valuation` | `dcf` |
| حساسیت DCF | ماتریس ارزش هر سهم و EV برای شبکه WACC × رشد پایانی | `dcf_sensitivity` | `dcf_analysis` |
| DCF معکوس | رشد پایانی تلویحی قیمت بازار (نصف‌سازی بازه) | `reverse_dcf_implied_growth` | `dcf_analysis` |
| سناریوهای وزنی DCF | `E[V] = Σ pᵢVᵢ` و انحراف معیار وزنی | `dcf_scenario_valuation` | `dcf_analysis` |

توابع کمکی مثل `calculate_fcff` هم در همان ماژول موضوعی قرار دارند.

برای هر مدل، توابع تجزیه (`single_period_decomposition`، `gordon_breakdown`،
`expected_return_breakdown`، `capm_breakdown`، `growth_opportunities_breakdown`،
`supernormal_schedule` در `equity` و `wacc_breakdown` در `cost_of_capital`)
اجزای ارزش و بازده را برمی‌گردانند تا فرانت‌اند React هیچ محاسبه‌ای انجام ندهد.

> مدل‌های WACC، DCF، حساسیت DCF، DCF معکوس، سناریوهای وزنی DCF و رشد پایدار
> فقط در لایه دامنه و endpointهای FastAPI در دسترس‌اند؛ رابط گرافیکی برای
> آن‌ها در این مخزن پیاده‌سازی نشده است.

## ساختار پروژه

```
stock-env/
├── stock_valuation/
│   ├── domain/                   # لایه دامنه — منطق خالص، بدون import وب
│   │   ├── errors.py             # ValidationError و CalculationError
│   │   ├── validators.py         # اعتبارسنجی ورودی‌ها، MIN_SPREAD، require_finite_number
│   │   ├── equity.py             # سهام عادی: DDM، CAPM، NPVGO، رشد پایدار، PEG
│   │   ├── cost_of_capital.py    # WACC و تجزیه آن
│   │   ├── dcf.py                # FCFF و ارزش‌گذاری DCF بر پایه آن
│   │   ├── dcf_analysis.py       # سناریوها، ماتریس حساسیت، DCF معکوس (وابسته به dcf)
│   │   ├── valuation_models.py   # نمای سازگاری عقب‌رو؛ منطق ندارد، فقط دوباره‌صادر می‌کند
│   │   └── self_tests.py         # تست‌های دودی قابل اجرا از پوسته
│   └── api/                      # سرویس FastAPI
│       ├── main.py               # اپ، CORS، GET /health، ثبت exception handler
│       ├── errors.py             # ترجمه خطاهای دامنه به HTTP 400
│       ├── routes/               # نقاط پایانی، بر اساس موضوع
│       │   ├── __init__.py       # router مشترک با پیشوند /api/valuation
│       │   ├── equity.py         # ۱۳ endpoint مدل‌های سهام عادی
│       │   ├── capital.py        # /wacc
│       │   ├── dcf.py            # /dcf
│       │   ├── dcf_analysis.py   # /dcf-scenarios، /dcf-sensitivity، /reverse-dcf
│       │   └── _common.py        # تبدیل سطرهای پیش‌بینی درخواست به نمونه‌های دامنه
│       └── schemas/              # مدل‌های Pydantic درخواست و پاسخ
│           ├── __init__.py       # دوباره‌صادر کردن همه نام‌ها برای `schemas as s`
│           ├── common.py         # _Base، _RequestBase و بدنه خطا
│           ├── equity.py
│           ├── capital.py
│           ├── dcf.py
│           └── dcf_analysis.py
├── tests/
│   └── domain/                   # تست‌های لایه دامنه (بدون فریم‌ورک وب)
│       ├── _fixtures.py          # پیش‌بینی پنج‌ساله مرجع DCF
│       ├── test_equity.py
│       ├── test_cost_of_capital.py
│       ├── test_dcf.py
│       ├── test_dcf_analysis.py
│       ├── test_layering.py      # نگهبان مرز لایه دامنه
│       └── test_self_tests.py
├── docs/
│   └── dcf_design.md             # قرارداد طراحی DCF/WACC
├── frontend/                     # دارایی‌های ظاهری برای فرانت‌اند React
│   ├── tailwind.config.js        # رنگ‌ها، فونت، شعاع و پالت نمودارها
│   └── src/index.css             # RTL، فونت وزیرمتن و متغیرهای CSS
├── requirements-api.txt          # وابستگی‌های اجرای سرویس (fastapi، pydantic، uvicorn)
├── requirements.txt              # fastapi و pydantic برای ابزارهای محلی
├── Dockerfile
└── README.md
```

## نصب و اجرا

پیش‌نیاز: پایتون ۳.۱۰ یا جدیدتر (تصویر داکر این مخزن `python:3.11-slim` است).

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### اجرای سرویس API

`requirements-api.txt` سه بسته لازم برای اجرای سرویس را فهرست می‌کند
(`fastapi`، `pydantic`، `uvicorn`):

```bash
pip install -r requirements-api.txt
uvicorn stock_valuation.api.main:app --reload
```

سرویس روی `http://127.0.0.1:8000` بالا می‌آید و مستندات تعاملی OpenAPI در
`/docs` در دسترس است.

`requirements.txt` فقط `fastapi` و `pydantic` را دارد و برای ابزارهای محلی
(مثلاً import کردن اسکیموها بدون اجرای سرویس) نگه داشته شده است؛ برای بالا
آوردن سرویس همان `requirements-api.txt` را نصب کنید.

برای اجرای سرویس روی پورت یا میزبان دیگر:

```bash
uvicorn stock_valuation.api.main:app --host 0.0.0.0 --port 8000
```

مبداهای مجاز CORS با متغیر محیطی `ALLOWED_ORIGINS` تنظیم می‌شود (بخش CORS را
ببینید). تست‌ها را می‌توان بدون نصب هیچ بسته‌ای اجرا کرد (بخش «اجرای تست‌ها»).

## سرویس API

### نقاط پایانی

۱۸ endpoint محاسباتی در چهار ماژول روت و یک endpoint سلامت در `api/main.py`:

| متد | مسیر | ماژول روت | تابع دامنه |
|---|---|---|---|
| POST | `/api/valuation/single-period` | `routes/equity.py` | `equity.single_period_decomposition` |
| POST | `/api/valuation/zero-growth` | `routes/equity.py` | `equity.zero_growth_model` |
| POST | `/api/valuation/annual-dividend-yield` | `routes/equity.py` | `equity.annual_dividend_yield_percent` |
| POST | `/api/valuation/gordon` | `routes/equity.py` | `equity.gordon_breakdown` |
| POST | `/api/valuation/supernormal-growth` | `routes/equity.py` | `equity.supernormal_growth_model` + `equity.supernormal_schedule` |
| POST | `/api/valuation/dividend-projection` | `routes/equity.py` | `equity.project_dividends` |
| POST | `/api/valuation/expected-return` | `routes/equity.py` | `equity.expected_return_breakdown` |
| POST | `/api/valuation/capm` | `routes/equity.py` | `equity.capm_breakdown` |
| POST | `/api/valuation/preferred-stock` | `routes/equity.py` | `equity.preferred_stock_valuation` |
| POST | `/api/valuation/risk-premium` | `routes/equity.py` | `equity.risk_premium_percent` |
| POST | `/api/valuation/growth-opportunities` | `routes/equity.py` | `equity.growth_opportunities_breakdown` |
| POST | `/api/valuation/sustainable-growth` | `routes/equity.py` | `equity.sustainable_growth_valuation` |
| POST | `/api/valuation/peg` | `routes/equity.py` | `equity.peg_ratio` + `equity.interpret_peg` |
| POST | `/api/valuation/wacc` | `routes/capital.py` | `cost_of_capital.wacc_breakdown` |
| POST | `/api/valuation/dcf` | `routes/dcf.py` | `dcf.dcf_valuation` |
| POST | `/api/valuation/dcf-scenarios` | `routes/dcf_analysis.py` | `dcf_analysis.dcf_scenario_valuation` |
| POST | `/api/valuation/dcf-sensitivity` | `routes/dcf_analysis.py` | `dcf_analysis.dcf_sensitivity` |
| POST | `/api/valuation/reverse-dcf` | `routes/dcf_analysis.py` | `dcf_analysis.reverse_dcf_implied_growth` |
| GET | `/health` | `api/main.py` | بررسی دسترس‌پذیری سرویس |

هر ماژول روت یک `APIRouter` بدون پیشوند دارد و `routes/__init__.py` همه را
زیر یک `router` مشترک با `prefix="/api/valuation"` و برچسب `valuation` قرار
می‌دهد؛ پس افزودن ماژول روت جدید فقط یک `include_router` در آن فایل می‌خواهد.
اسکیمای هر endpoint در ماژول هم‌نام `schemas/` است و `schemas/__init__.py` همه
نام‌ها را دوباره صادر می‌کند تا `from .. import schemas as s` ثابت بماند.

### قرارداد داده

- همه نقاط پایانی محاسباتی `POST` با بدنه JSON هستند و همیشه یک شیء JSON
  برمی‌گردانند؛ حتی برای توابعی که در دامنه یک عدد یا فهرست ساده برمی‌گردانند
  (مثل `dividend-projection` و `risk-premium`).
- نرخ‌ها **اعشاری** وارد می‌شوند: ۱۲٪ برابر `0.12` است. دو استثنای خودتوضیح:
  نرخ رشد در `peg` (`growth_rate_percent`) و نرخ اوراق قرضه در `risk-premium`
  (`bond_rate_percent`) که هر دو درصدی‌اند.
- فیلدهای `*_percent` در پاسخ آماده نمایش‌اند تا فرانت‌اند محاسبه‌ای تکرار نکند.

### ماتریس حساسیت DCF (WACC × رشد پایانی)

ارزش هر سهم و ارزش بنگاه را برای شبکه‌ای از ترکیب‌های WACC و رشد پایانی
برمی‌گرداند. هر سلول با همان `dcf_valuation` محاسبه می‌شود؛ محورها صعودی و
مرکزچین روی حالت پایه‌اند، پس حالت پایه دقیقاً سلول (`base_row`, `base_col`) است.
گام‌ها و تعداد نقاط (فرد، بین ۳ تا ۱۱) در دامنه اعتبارسنجی می‌شوند.

```bash
curl -s -X POST http://127.0.0.1:8000/api/valuation/dcf-sensitivity \
  -H "Content-Type: application/json" -d @sensitivity.json
```

```json
{
  "projections": [
    {"ebit": 1000, "depreciation": 200, "capex": 250, "delta_nwc": 50},
    {"ebit": 1100, "depreciation": 210, "capex": 260, "delta_nwc": 55},
    {"ebit": 1200, "depreciation": 220, "capex": 270, "delta_nwc": 60},
    {"ebit": 1300, "depreciation": 230, "capex": 280, "delta_nwc": 65},
    {"ebit": 1400, "depreciation": 240, "capex": 290, "delta_nwc": 70}
  ],
  "wacc": 0.09,
  "terminal_growth": 0.03,
  "shares_outstanding": 100,
  "tax_rate": 0.25,
  "cash": 500,
  "debt": 1500,
  "wacc_step": 0.01,
  "growth_step": 0.005,
  "wacc_points": 5,
  "growth_points": 5
}
```

پاسخ (مختصر؛ مقادیر گرد شده‌اند):

```json
{
  "wacc_values": [0.07, 0.08, 0.09, 0.1, 0.11],
  "growth_values": [0.02, 0.025, 0.03, 0.035, 0.04],
  "wacc_values_percent": [7.0, 8.0, 9.0, 10.0, 11.0],
  "growth_values_percent": [2.0, 2.5, 3.0, 3.5, 4.0],
  "value_per_share": [
    [157.27, 173.04, 192.75, 218.09, 251.87],
    [128.71, 139.07, 151.5, 166.69, 185.68],
    [108.34, 115.58, 124.02, 134.0, 145.98],
    [93.07, 98.36, 104.41, 111.39, 119.54],
    [81.21, 85.21, 89.72, 94.82, 100.66]
  ],
  "enterprise_value": [["...همین شکل..."]],
  "base_wacc": 0.09,
  "base_terminal_growth": 0.03,
  "base_row": 2,
  "base_col": 2,
  "base_value_per_share": 124.02201272656133,
  "base_enterprise_value": 13402.201272656133,
  "valid_cells": 25,
  "total_cells": 25
}
```

نکته‌ها برای فرانت‌اند:

- `matrix[i][j]` متعلق به `wacc_values[i]` (سطر) و `growth_values[j]` (ستون) است؛
  همین قاعده برای `enterprise_value` هم برقرار است.
- `null` یعنی آن ترکیب نامعتبر است (مثلاً WACC ≤ 0 یا اختلاف WACC و رشد کمتر از
  `MIN_SPREAD`)؛ چنین سلولی را خالی/خاکستری رندر کنید، نه صفر.
- `valid_cells` و `total_cells` برای نمایش نسبت پوشش ماتریس آماده‌اند.

### DCF معکوس (رشد پایانی تلویحی بازار)

به ازای قیمت بازار، نرخ رشد پایانی‌ای را پیدا می‌کند که ارزش هر سهم را برابر
قیمت بازار کند. جستجو در بازه `[−20%، WACC − 0.5%]` با نصف‌سازی انجام
می‌شود؛ اگر قیمت بیرون بازه باشد، خطا برنمی‌گردد و وضعیت
`market_price_below_range` یا `market_price_above_range` گزارش می‌شود.

```json
{
  "projections": ["...همان پنج سال بالا..."],
  "wacc": 0.09,
  "shares_outstanding": 100,
  "tax_rate": 0.25,
  "market_price": 120.0,
  "cash": 500,
  "debt": 1500,
  "terminal_growth": 0.03
}
```

پاسخ واقعی برای همین ورودی (مقادیر گرد شده):

```json
{
  "status": "solved",
  "market_price": 120.0,
  "implied_growth": 0.027718738173134614,
  "implied_growth_percent": 2.77,
  "wacc": 0.09,
  "wacc_percent": 9.0,
  "search_min_growth": -0.2,
  "search_max_growth": 0.085,
  "value_per_share_at_min_growth": 36.93,
  "value_per_share_at_max_growth": 1331.89,
  "enterprise_value": 13000.0,
  "equity_value": 12000.0,
  "terminal_value_share_percent": 76.72,
  "reference_terminal_growth": 0.03,
  "growth_gap": -0.0023,
  "growth_gap_percent": -0.23,
  "message": "بازار با این قیمت، رشد پایانی حدود 2.77% را فرض کرده است"
}
```

نکته‌ها برای فرانت‌اند:

- `terminal_growth` در درخواست اختیاری است؛ نرخ رشد پایانی خود تحلیل‌گر است و
  فقط برای محاسبه `growth_gap` (تلویحی منهای مرجع) استفاده می‌شود.
- `status` سه مقدار دارد: `solved` یعنی `implied_growth` مقدار دارد؛ در
  `market_price_below_range` و `market_price_above_range` مقدار
  `implied_growth` و همچنین `implied_growth_percent`، `enterprise_value`،
  `equity_value` و `terminal_value_share_percent` برابر `null` است.
- `message` فارسی و آماده نمایش است و در حالت‌های خارج از بازه، کرانه‌های جستجو
  را هم ذکر می‌کند.

### سناریوهای وزنی DCF

دو تا پنج سناریوی مستقل با `dcf_valuation` ارزش‌گذاری می‌شوند؛ ورودی‌های
ترازنامه و تعداد سهام مشترک‌اند. شکست حتی یک سناریو کل درخواست را با همان
نوع خطا و نام سناریو رد می‌کند؛ سناریوی با احتمال صفر نیز بررسی می‌شود.

```bash
curl -s -X POST http://127.0.0.1:8000/api/valuation/dcf-scenarios \
  -H "Content-Type: application/json" -d @scenarios.json
```

بدنهٔ `scenarios.json`:

```json
{
  "scenarios": [
    {"name": "bear", "probability": 0.5, "wacc": 0.1, "terminal_growth": 0.0,
     "projections": [{"ebit": 100, "depreciation": 0, "capex": 0, "delta_nwc": 0}]},
    {"name": "bull", "probability": 0.5, "wacc": 0.1, "terminal_growth": 0.0,
     "projections": [{"ebit": 200, "depreciation": 0, "capex": 0, "delta_nwc": 0}]}
  ],
  "shares_outstanding": 10,
  "tax_rate": 0.0
}
```

پاسخ مختصر واقعی (مقادیر گرد شده‌اند):

```json
{
  "scenarios": [
    {"name": "bear", "probability": 0.5, "probability_percent": 50.0,
     "value_per_share": 100.0, "weighted_value_per_share": 50.0,
     "upside": null, "upside_percent": null},
    {"name": "bull", "probability": 0.5, "probability_percent": 50.0,
     "value_per_share": 200.0, "weighted_value_per_share": 100.0,
     "upside": null, "upside_percent": null}
  ],
  "expected_value_per_share": 150.0,
  "expected_enterprise_value": 1500.0,
  "expected_equity_value": 1500.0,
  "std_dev_value_per_share": 50.0,
  "min_value_per_share": 100.0,
  "max_value_per_share": 200.0,
  "worst_scenario": "bear",
  "best_scenario": "bull",
  "market_price": null,
  "expected_upside": null,
  "expected_upside_percent": null,
  "probability_of_upside": null,
  "probability_of_upside_percent": null
}
```

نکته‌ها برای فرانت‌اند:

- سطرهای `scenarios` ترتیب ورودی را حفظ می‌کنند؛ در تساوی بهترین/بدترین،
  نخستین سناریو برنده است.
- `probability` باید در بازهٔ صفر تا یک و مجموع آن‌ها برابر یک با تلورانس
  `1e-6` باشد؛ هیچ نرمال‌سازی خودکاری انجام نمی‌شود.
- بدون `market_price` همهٔ `upside`، `upside_percent`، `expected_upside*` و
  `probability_of_upside*` برابر `null` هستند. با قیمت بازار، احتمال رشد فقط
  سناریوهای با `value_per_share > market_price` را جمع می‌کند.
- `min_value_per_share`، `max_value_per_share` و `expected_value_per_share`
  ورودی نمودار بازهٔ ارزش به سبک football-field هستند.

### رشد پایدار و NPVGO

این مدل از `EPS₁`، بازده مورد انتظار، `ROE` و نسبت نگهداری سود، رشد پایدار
و NPVGO را استخراج می‌کند. اگر `ROE == r` باشد NPVGO تقریباً صفر است؛
سرمایه‌گذاری با `ROE < r` ارزش را کاهش می‌دهد. نسبت نگهداری باید کمتر از یک
و اختلاف `r − g` مطابق همان اعتبارسنج و `MIN_SPREAD` موجود باشد.

```bash
curl -s -X POST http://127.0.0.1:8000/api/valuation/sustainable-growth \
  -H "Content-Type: application/json" \
  -d '{"eps":5.0,"r":0.12,"roe":0.15,"retention_ratio":0.4}'
```

پاسخ مختصر واقعی (مقادیر گرد شده‌اند؛ هر ده نقطهٔ منحنی نمایش داده شده‌اند):

```json
{
  "sustainable_growth": 0.06,
  "sustainable_growth_percent": 6.0,
  "payout_ratio": 0.6,
  "next_dividend": 3.0,
  "price": 50.0,
  "no_growth_value": 41.6667,
  "npvgo": 8.3333,
  "growth_share_percent": 16.6667,
  "justified_pe": 10.0,
  "growth_creates_value": true,
  "retention_curve": [
    {"retention_ratio": 0.0, "sustainable_growth": 0.0, "price": 41.6667, "npvgo": 0.0},
    {"retention_ratio": 0.1, "sustainable_growth": 0.015, "price": 42.8571, "npvgo": 1.1905},
    {"retention_ratio": 0.2, "sustainable_growth": 0.03, "price": 44.4444, "npvgo": 2.7778},
    {"retention_ratio": 0.3, "sustainable_growth": 0.045, "price": 46.6667, "npvgo": 5.0},
    {"retention_ratio": 0.4, "sustainable_growth": 0.06, "price": 50.0, "npvgo": 8.3333},
    {"retention_ratio": 0.5, "sustainable_growth": 0.075, "price": 55.5556, "npvgo": 13.8889},
    {"retention_ratio": 0.6, "sustainable_growth": 0.09, "price": 66.6667, "npvgo": 25.0},
    {"retention_ratio": 0.7, "sustainable_growth": 0.105, "price": 100.0, "npvgo": 58.3333},
    {"retention_ratio": 0.8, "sustainable_growth": 0.12, "price": null, "npvgo": null},
    {"retention_ratio": 0.9, "sustainable_growth": 0.135, "price": null, "npvgo": null}
  ]
}
```

نکته‌ها برای فرانت‌اند:

- نقاط `retention_curve` با `price: null` ترکیب نامعتبر رشد و بازده هستند؛
  آن‌ها را به شکل شکاف در نمودار خطی رندر کنید، نه قیمت صفر.
- درصدهای رشد پایدار و نگهداری سود برای هر نقطه در پاسخ کامل آماده‌اند.
- مسیر موجود `/growth-opportunities` با NPVGO دستی دست‌نخورده است؛ مسیر جدید
  NPVGO را از ROE و نسبت نگهداری سود به دست می‌آورد.

### قرارداد خطا

| کد وضعیت | معنا |
|---|---|
| 200 | محاسبه موفق |
| 400 | خطای دامنه (`ValidationError` یا `CalculationError`) |
| 422 | خطای اسکیمای Pydantic (بدنه ناقص، نوع نامعتبر، فیلد ناشناخته) |

بدنه پاسخ 400 برای هر دو استثنای دامنه یکسان است:

```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "❌ نرخ بازده (12.0%) باید بیشتر از نرخ رشد (12.0%) باشد!",
  "details": null
}
```

`error_code` یکی از `VALIDATION_ERROR` یا `CALCULATION_ERROR` است و `message`
متن فارسی همان استثنای دامنه. پاسخ‌های 422 ساختار بومی FastAPI
(`{"detail": [...]}`) را حفظ می‌کنند و عمداً تغییر نکرده‌اند.

### CORS

مبداهای مجاز پیش‌فرض برای فرانت‌اند در حال توسعه: Vite روی پورت `5173` و
Create React App روی پورت `3000` (هم `localhost` و هم `127.0.0.1`). برای محیط
دیگر، متغیر محیطی `ALLOWED_ORIGINS` را با فهرست جداشده با کاما تنظیم کنید.

## داکر

```bash
docker build -t stock-valuation-api .
docker run --rm -p 8000:8000 stock-valuation-api
```

سرویس روی `http://127.0.0.1:8000` در دسترس است:

```bash
curl -s http://127.0.0.1:8000/health          # {"status":"ok"}
docker ps                                     # ستون STATUS: healthy
docker logs -f <container>                    # لاگ uvicorn بدون بافر
```

### آنچه در تصویر می‌نشیند

- پایه تصویر `python:3.11-slim` است و فقط `requirements-api.txt`
  (`fastapi`، `pydantic`، `uvicorn`) نصب می‌شود؛ هیچ وابستگی رابط گرافیکی
  (Streamlit، pandas، Plotly) در تصویر نیست.
- `Dockerfile` تنها `requirements-api.txt` و پوشه `stock_valuation/` را `COPY`
  می‌کند، پس کد دامنه و API کل محتوای اجرایی تصویرند.
- `.dockerignore` محیط‌های مجازی، کش پایتون، `.git/`، `frontend/`، `tests/`،
  آرتیفکت‌های بیلد و مستندات (`README.md`، `Achievements.md`) را از بستر بیلد
  حذف می‌کند تا تغییر آن‌ها کش لایه‌ها را باطل نکند.
- وابستگی‌ها پیش از کد کپی می‌شوند تا تغییر سورس، لایه `pip install` را
  بازسازی نکند.

### اجرا و پیکربندی

- سرویس با `uvicorn stock_valuation.api.main:app --host 0.0.0.0 --port 8000`
  بالا می‌آید و `EXPOSE 8000` است.
- کانتینر با کاربر غیر ریشه `appuser` (uid `10001`) اجرا می‌شود؛ این کاربر پیش
  از `COPY` ساخته می‌شود تا فایل‌ها با مالکیت درست و بدون لایه `chown` اضافه
  وارد تصویر شوند.
- `PYTHONUNBUFFERED=1` لاگ‌ها را بی‌درنگ در `docker logs` می‌رساند و
  `PYTHONDONTWRITEBYTECODE=1` نوشتن بایت‌کد در تصویر را متوقف می‌کند.
- `HEALTHCHECK` هر ۳۰ ثانیه (با `start-period=10s` و سه تلاش) `GET /health` را
  با `urllib` استاندارد صدا می‌زند، چون تصویر `slim` ابزار `curl` ندارد؛ هر کد
  غیر ۲۰۰ باعث شکست healthcheck می‌شود.
- برای فرانت‌اندی روی میزبان دیگر، `ALLOWED_ORIGINS` را با فهرست جداشده با
  کاما بگذرید:

```bash
docker run --rm -p 8000:8000 \
  -e ALLOWED_ORIGINS="https://app.example.com" \
  stock-valuation-api
```

## فرانت‌اند React

پوشه `frontend/` فقط دارایی ظاهری است و `package.json` ندارد؛ محتوای آن در
یک پروژه Vite + React + Tailwind 3 کپی می‌شود:

- `frontend/tailwind.config.js` — رنگ‌های پایه و معنایی، فونت `Vazirmatn`، شعاع گوشه
  ۸ پیکسل، رنگ‌های نمودار و آرایه‌های `chartCategorical` / `chartSequential`
  برای کتابخانه‌های چارت.
- `frontend/src/index.css` — بارگذاری وزیرمتن، متغیرهای `:root`، `direction: rtl`،
  تراز راست، مقیاس سرصفحه‌ها و کلاس‌های کمکی `.ltr` / `.rtl`.

رنگ میله‌های نمودار در `--chart-bar` فایل `frontend/src/index.css` آبی پیش‌فرض
Plotly (`rgba(55, 128, 191, …)`) است و با رنگ اصلی تم (`#1D4ED8`) یکسان نیست؛
هر دو در دسترس‌اند تا انتخاب آگاهانه انجام شود. در Tailwind 4 به‌جای
پیکربندی JS باید `@config` یا بلوک `@theme` استفاده شود.

> کامنت‌های بالایی `frontend/tailwind.config.js` و `frontend/src/index.css` به
> `.streamlit/config.toml` و `stock_valuation/ui/theme.py` ارجاع می‌دهند؛ آن
> فایل‌ها با حذف رابط Streamlit از مخزن رفته‌اند و این ارجاع‌ها فقط منشأ تاریخ
> رنگ‌ها و تایپوگرافی را توضیح می‌دهند — دنبالشان نگردید.

## لایه‌بندی

### لایه دامنه (`stock_valuation/domain/`)

توابع خالص و قطعی؛ ورودی را صریح می‌گیرند و خروجی را برمی‌گردانند، بدون
خواندن یا نوشتن وضعیت سراسری و بدون import هیچ فریم‌ورک وبی. هر ماژول یک
موضوع است:

| ماژول | نقش | به چه تکیه می‌کند |
|---|---|---|
| `errors.py` | `ValidationError` و `CalculationError` | وابستگی ندارد |
| `validators.py` | اعتبارسنج‌های مشترک، `MIN_SPREAD`، `require_finite_number` | `errors` |
| `equity.py` | مدل‌های سود تقسیمی، CAPM، NPVGO، رشد پایدار، PEG | `errors`، `validators` |
| `cost_of_capital.py` | `wacc` و `wacc_breakdown` | `errors`، `validators` |
| `dcf.py` | `calculate_fcff`، `CashFlowProjection`، `dcf_valuation` | `errors`، `validators` |
| `dcf_analysis.py` | سناریوها، ماتریس حساسیت، DCF معکوس | `dcf`، `errors`، `validators` |
| `valuation_models.py` | نمای سازگاری عقب‌رو (بدون منطق) | چهار ماژول موضوعی |
| `self_tests.py` | تست‌های دودی مرجع | `valuation_models` |

جهت import فقط از ماژول موضوعی به `errors`/`validators` و از `dcf_analysis` به
`dcf` است؛ ماژول‌های `equity`، `cost_of_capital` و `dcf` مستقل‌اند و هیچ‌کدام
لایه API را import نمی‌کنند.

### لایه API (`stock_valuation/api/`)

- `main.py`: ساخت اپ، CORS، `GET /health` و ثبت exception handlerهای سراسری.
- `errors.py`: ترجمه `ValidationError` / `CalculationError` به پاسخ 400 با بدنه
  `ErrorResponse`.
- `routes/`: یک ماژول به هر موضوع (`equity`، `capital`، `dcf`، `dcf_analysis`)
  و `_common.py` برای تبدیل سطرهای پیش‌بینی درخواست به نمونه دامنه. هر endpoint
  دقیقاً یک تابع دامنه را صدا می‌زند و خروجی را با `model_validate` به مدل پاسخ
  نگاشت می‌کند؛ فیلدهایی که دامنه نمی‌دهد (نمایش مجدد ورودی) همان‌جا پر می‌شوند.
- `schemas/`: همان تقسیم موضوعی برای مدل‌های Pydantic؛ `common.py` پایه‌های
  `_Base` / `_RequestBase` و بدنه خطا را دارد و `__init__.py` همه نام‌ها را
  دوباره صادر می‌کند تا `from .. import schemas as s` کار کند.

### نمای سازگاری عقب‌رو

`stock_valuation/domain/valuation_models.py` دیگر هیچ منطقی ندارد و فقط نام‌های
عمومی چهار ماژول موضوعی را دوباره صادر می‌کند، تا importهای قدیمی بدون تغییر
کار کنند. کد جدید باید مستقیماً از ماژول موضوعی خود import کند:

```python
from stock_valuation.domain.dcf import dcf_valuation          # ✅
from stock_valuation.domain.valuation_models import dcf_valuation  # فقط سازگاری کد قبلی
```

### مرزهایی که تست نگه می‌دارد

`tests/domain/test_layering.py` همه ماژول‌های بسته دامنه را با `pkgutil` کشف
می‌کند، پس ماژول جدید بدون تغییر آن فایل بررسی می‌شود. این تست چهار قرارداد را
بررسی می‌کند: نبود import `streamlit` / `fastapi` / `pydantic` در لایه دامنه،
نبود ارجاع به `st.`، نبود رشته `session_state`، و اینکه همه ماژول‌ها (و نمای
سازگاری) همان کلاس‌های خطای `domain/errors.py` را به اشتراک دارند.

### خطاهای لایه دامنه

- `ValidationError` — ورودی نامعتبر یا ترکیب نامعتبر پارامترها
  (مثلاً نرخ رشد بزرگ‌تر از نرخ بازده، یا اختلاف کمتر از `MIN_SPREAD`)
- `CalculationError` — نتیجه غیرعددی یا خطای عددی در محاسبه

هر دو استثنا در `stock_valuation/domain/errors.py` تعریف شده‌اند و لایه دامنه
منبع حقیقت اعتبارسنجی است؛ کرانه‌های `Field` در Pydantic فقط آینه همان
اعتبارسنج‌ها هستند و قانون جدیدی اضافه نمی‌کنند. سرویس API همین دو استثنا را به
پاسخ 400 با بدنه ثابت تبدیل می‌کند و پیام فارسی دامنه را عیناً در `message`
می‌گذارد تا فرانت‌اند چیزی را بازترجمی نکند.

## اجرای تست‌ها

همه تست‌ها در `tests/domain/` هستند، از `unittest.TestCase` استفاده می‌کنند و
جز کتابخانه استاندارد و خود لایه دامنه چیزی import نمی‌کنند؛ پس بدون نصب
`fastapi` / `pydantic` / `pytest` هم اجرا می‌شوند. همه فرمان‌ها از ریشه پروژه
اجرا می‌شوند:

```bash
# کل مجموعه (unittest — پیش‌فرض مخزن)
python3 -m unittest discover -s tests -t . -v

# یک ماژول تست
python3 -m unittest tests.domain.test_dcf_analysis -v

# یک کلاس یا یک تست
python3 -m unittest tests.domain.test_dcf.TestFcff.test_reference_r1

# در صورت نصب pytest
python3 -m pytest tests -q
python3 -m pytest tests/domain/test_layering.py -q
```

هر دو اجراکننده ۱۵۷ تست را کشف می‌کنند؛ فایل تست با ماژول دامنه‌ای که می‌سنجد
هم‌نام است:

| فایل | ماژول دامنه | تست |
|---|---|---|
| `tests/domain/test_equity.py` | `domain/equity.py` | ۶۹ |
| `tests/domain/test_dcf_analysis.py` | `domain/dcf_analysis.py` | ۴۶ |
| `tests/domain/test_dcf.py` | `domain/dcf.py` | ۲۷ |
| `tests/domain/test_cost_of_capital.py` | `domain/cost_of_capital.py` | ۱۰ |
| `tests/domain/test_layering.py` | مرز لایه دامنه | ۴ |
| `tests/domain/test_self_tests.py` | `domain/self_tests.py` | ۱ |

`tests/domain/_fixtures.py` پیش‌بینی پنج‌ساله مرجع DCF را به‌صورت مشترک در اختیار
آزمون‌های DCF، حساسیت و DCF معکوس می‌گذارد.

محتوای مجموعه: مقادیر مرجع مدل‌ها (شامل WACC و DCF)، سازگاری
ارزش فعلی اجزا با قیمت کل، حداقل اختلاف نرخ بازده/WACC و رشد، ورودی‌های خالی
یا ناهم‌خوان، آستانه‌های تفسیر PEG، ماتریس حساسیت DCF (سلول مرکزی، محورها،
سلول‌های نامعتبر و پارامترهای شبکه)، رفت‌وبرگشت و حالت‌های خارج از بازه DCF
معکوس، احتمال‌ها و آمار ریسک سناریوهای وزنی، هویت‌های NPVGO و منحنی رشد
پایدار، قطعی‌بودن خروجی‌ها و نبود وابستگی لایه محاسباتی به فریم‌ورک‌های وب.

### تست‌های دودی

`domain/self_tests.py` هشت بررسی سریع (smoke) روی مدل‌های مرجع انجام می‌دهد و
فهرست پیام‌های ✅/❌ برمی‌گرداند؛ چون رابط گرافیکی در مخزن نیست، از پوسته اجرا
می‌شود:

```bash
python3 -c "from stock_valuation.domain.self_tests import run_self_tests; [print(m) for m in run_self_tests()]"
```

مرجع کامل و قطعی همان مجموعه `tests/domain/` است و `test_self_tests.py` فقط
بررسی می‌کند فهرست ۸ سطری باشد و همه با ✅ شروع شوند.

لایه API در حال حاضر تست خودکار ندارد؛ صحت هر ۱۸ endpoint، قرارداد خطا و
پاسخ 422 با فراخوانی واقعی HTTP بررسی شده است.

## افزودن مدل جدید

1. تابع محاسباتی و در صورت نیاز نوع نتیجه (dataclass منجمد یا NamedTuple) را
   در ماژول موضوعی لایه دامنه اضافه کنید: `equity.py`، `cost_of_capital.py`،
   `dcf.py` یا `dcf_analysis.py`. اگر موضوع تازه‌ای است، ماژول جدید بسازید؛
   `test_layering.py` آن را خودکار کشف می‌کند. docstring بنویسید و از
   `ValidationError` / `CalculationError` و اعتبارسنج‌های `validators.py`
   استفاده کنید.
2. `domain/valuation_models.py` را با نام‌های جدید به‌روز کنید تا نمای
   سازگاری عقب‌رو کامل بماند (این فایل فقط `import`/`__all__` دارد و نباید
   منطق جدیدی در آن نوشته شود).
3. مدل درخواست و پاسخ Pydantic را در ماژول هم‌نام `api/schemas/` اضافه کنید و
   نام‌ها را در `api/schemas/__init__.py` (همراه `__all__`) دوباره صادر کنید؛
   نام فیلدهای پاسخ را با خروجی دامنه یکی بگیرید تا
   `model_validate(..., from_attributes=True)` بدون نگاشت دستی کار کند.
4. یک endpoint در ماژول هم‌نام `api/routes/` اضافه کنید که فقط تابع دامنه را
   صدا بزند؛ برای ماژول روت تازه، یک `include_router` در
   `api/routes/__init__.py` کافی است. هیچ فرمول یا اعتبارسنجی عددی را در این
   لایه تکرار نکنید.
5. تست‌ها را در `tests/domain/test_<ماژول>.py` بنویسید (مقادیر مرجع، خطاهای
   اعتبارسنجی، قطعی‌بودن خروجی) و در صورت نیاز فیکسچر مشترک را در
   `tests/domain/_fixtures.py` اضافه کنید.
6. جدول مدل‌ها و جدول endpointهای همین README را به‌روز کنید.

>توسعه مدل‌های جدید: فرمول‌ها صرفاً در لایه دامنه و در ماژول موضوعی خود
>نگهداری می‌شوند. برای اضافه کردن هر مدل جدید، تنها به نوشتن یک تابع محاسباتی
>کاملاً ایزوله، یک طرحواره Pydantic و یک روت هدایت‌کننده نیاز دارید. این
>ساختار تضمین می‌کند که قرارداد JSON و مسیرهای API هیچ‌گاه درگیر منطق ریاضی
>تکراری نشوند.
