# stock-valuation-tool

ابزار ارزیابی سهام بر اساس کتاب مدیریت مالی استفان راس.

منطق محاسباتی در یک لایه دامنه خالص پیاده‌سازی شده و از دو مسیر مستقل در
دسترس است:

- **سرویس FastAPI** (`stock_valuation/api/`) — قرارداد JSON برای فرانت‌اند React
- **داشبورد Streamlit** (`stock_cla_developed.py`) — رابط فارسی RTL نسخه اول

هر دو مسیر همان توابع خالص لایه دامنه را صدا می‌زنند و هیچ فرمولی در لایه‌های
نمایش تکرار نشده است.

## مدل‌های پشتیبانی‌شده

| مدل | فرمول | تابع |
|---|---|---|
| تک‌دوره‌ای | `P₀ = (D₁ + P₁) / (1 + r)` | `single_period_model` |
| رشد صفر | `P = D / r` | `zero_growth_model` |
| رشد ثابت (گوردون) | `P = D₀(1+g) / (r - g)` | `constant_growth_model` |
| رشد غیرعادی | `P₀ = Σ Dₜ/(1+r)ᵗ + Pₙ/(1+r)ⁿ` | `supernormal_growth_model` |
| بازده مورد انتظار | `r = D₁/P₀ + g` | `expected_return` |
| بازده مورد انتظار (CAPM) | `r = rf + β(rm − rf)` | `capm_required_return` |
| سهام ممتاز | `P = D / r` | `preferred_stock_valuation` |
| فرصت‌های رشد | `P = EPS/r + NPVGO` | `growth_opportunities_valuation` |
| رشد پایدار و NPVGO | `g = b × ROE`، `P = EPS₁(1−b)/(r−g)` | `sustainable_growth_valuation` |
| نسبت PEG | `PEG = (P/E) / g` | `peg_ratio` |
| WACC | `WACC = (E/V)rₑ + (D/V)r_d(1−t)` | `wacc` |
| DCF (FCFF) | `EV = Σ FCFFₜ/(1+WACC)ᵗ + TV/(1+WACC)ⁿ` | `dcf_valuation` |
| حساسیت DCF | ماتریس ارزش هر سهم و EV برای شبکه WACC × رشد پایانی | `dcf_sensitivity` |
| DCF معکوس | رشد پایانی تلویحی قیمت بازار (نصف‌سازی بازه) | `reverse_dcf_implied_growth` |
| سناریوهای وزنی DCF | `E[V] = Σ pᵢVᵢ` و انحراف معیار وزنی | `dcf_scenario_valuation` |

برای هر مدل، توابع تجزیه (`single_period_decomposition`، `gordon_breakdown`،
`expected_return_breakdown`، `capm_breakdown`، `growth_opportunities_breakdown`،
`supernormal_schedule`، `wacc_breakdown`) اجزای ارزش و بازده را برمی‌گردانند تا
لایه نمایش هیچ محاسبه‌ای انجام ندهد.

> رابط Streamlit برای مدل‌های WACC، DCF، حساسیت DCF، DCF معکوس،
> سناریوهای وزنی DCF و رشد پایدار هنوز پیاده‌سازی نشده و خارج از محدودهٔ این تغییر است؛ فقط لایه دامنه و endpointهای
> FastAPI در دسترس‌اند.

## ساختار پروژه

```
stock-env/
├── stock_cla_developed.py        # نقطه ورود Streamlit: چیدمان صفحه، منوی کناری، مسیریابی
├── stock_valuation/
│   ├── domain/                   # لایه دامنه — بدون وابستگی به Streamlit
│   │   ├── valuation_models.py   # مدل‌های ارزیابی و انواع نتیجه
│   │   ├── validators.py         # اعتبارسنجی ورودی‌ها و MIN_SPREAD
│   │   ├── errors.py             # ValidationError و CalculationError
│   │   └── self_tests.py         # تست‌های دودی قابل اجرا از داخل برنامه
│   ├── api/                      # سرویس FastAPI
│   │   ├── main.py               # اپ، CORS، GET /health، ثبت exception handler
│   │   ├── routes.py             # ۱۸ endpoint زیر /api/valuation
│   │   ├── schemas.py            # مدل‌های Pydantic درخواست و پاسخ
│   │   └── errors.py             # ترجمه خطاهای دامنه به HTTP 400
│   └── ui/                       # لایه نمایش Streamlit — فقط ویجت، رندر و نمودار
│       ├── views.py              # ویجت‌ها، رندر نتایج، تاریخچه محاسبات (session state)
│       ├── charts.py             # سازنده‌های نمودار Plotly
│       └── theme.py              # چیدمان راست‌به‌چپ (RTL) رابط فارسی
├── frontend/                     # دارایی‌های ظاهری برای فرانت‌اند React
│   ├── tailwind.config.js        # رنگ‌ها، فونت، شعاع و پالت نمودارها
│   └── src/index.css             # RTL، فونت وزیرمتن و متغیرهای CSS
├── .streamlit/
│   └── config.toml               # تم روشن مالی، فونت وزیرمتن و پالت رنگ نمودارها
├── tests/
│   └── test_valuation_models.py
├── requirements.txt              # وابستگی‌های کامل (شامل Streamlit)
├── requirements-api.txt          # فقط وابستگی‌های بک‌اند
├── Dockerfile
└── README.md
```

## نصب و اجرا

پیش‌نیاز: پایتون ۳.۱۱ یا جدیدتر. (`fastapi`، `pydantic` و `uvicorn` حداقل ۳.۱۰
و `streamlit` حداقل ۳.۱۱ می‌خواهند.)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### سرویس API

برای بک‌اند فقط `requirements-api.txt` کافی است (بدون Streamlit، pandas و Plotly):

```bash
pip install -r requirements-api.txt
uvicorn stock_valuation.api.main:app --reload
```

سرویس روی `http://127.0.0.1:8000` بالا می‌آید و مستندات تعاملی OpenAPI در
`/docs` در دسترس است.

### داشبورد Streamlit

```bash
streamlit run stock_cla_developed.py
```

برنامه روی `http://localhost:8501` در دسترس خواهد بود.

## سرویس API

### نقاط پایانی

| متد | مسیر | تابع دامنه |
|---|---|---|
| POST | `/api/valuation/single-period` | `single_period_decomposition` |
| POST | `/api/valuation/zero-growth` | `zero_growth_model` |
| POST | `/api/valuation/annual-dividend-yield` | `annual_dividend_yield_percent` |
| POST | `/api/valuation/gordon` | `gordon_breakdown` |
| POST | `/api/valuation/supernormal-growth` | `supernormal_growth_model` + `supernormal_schedule` |
| POST | `/api/valuation/dividend-projection` | `project_dividends` |
| POST | `/api/valuation/expected-return` | `expected_return_breakdown` |
| POST | `/api/valuation/capm` | `capm_breakdown` |
| POST | `/api/valuation/preferred-stock` | `preferred_stock_valuation` |
| POST | `/api/valuation/risk-premium` | `risk_premium_percent` |
| POST | `/api/valuation/growth-opportunities` | `growth_opportunities_breakdown` |
| POST | `/api/valuation/sustainable-growth` | `sustainable_growth_valuation` |
| POST | `/api/valuation/peg` | `peg_ratio` + `interpret_peg` |
| POST | `/api/valuation/wacc` | `wacc_breakdown` |
| POST | `/api/valuation/dcf` | `dcf_valuation` |
| POST | `/api/valuation/dcf-scenarios` | `dcf_scenario_valuation` |
| POST | `/api/valuation/dcf-sensitivity` | `dcf_sensitivity` |
| POST | `/api/valuation/reverse-dcf` | `reverse_dcf_implied_growth` |
| GET | `/health` | بررسی دسترس‌پذیری سرویس |

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
docker run -p 8000:8000 stock-valuation-api
```

- تصویر از `python:3.11-slim` ساخته می‌شود و فقط `requirements-api.txt` را
  نصب می‌کند؛ پشته Streamlit (نزدیک ۴۰۰ مگابایت) وارد تصویر نمی‌شود.
- `.dockerignore` محیط‌های مجازی، کش پایتون، `.git`، `.streamlit`،
  `stock_valuation/ui/`، `frontend/` و `tests/` را از بستر بیلد حذف می‌کند.
- سرویس روی `0.0.0.0:8000` گوش می‌دهد.

## فرانت‌اند React

پوشه `frontend/` فقط دارایی ظاهری است و `package.json` ندارد؛ محتوای آن در
یک پروژه Vite + React + Tailwind 3 کپی می‌شود:

- `frontend/tailwind.config.js` — رنگ‌های پایه و معنایی، فونت `Vazirmatn`، شعاع گوشه
  ۸ پیکسل، رنگ‌های نمودار و آرایه‌های `chartCategorical` / `chartSequential`
  برای کتابخانه‌های چارت.
- `frontend/src/index.css` — بارگذاری وزیرمتن، متغیرهای `:root`، `direction: rtl`،
  تراز راست، مقیاس سرصفحه‌ها و کلاس‌های کمکی `.ltr` / `.rtl`.

رنگ میله‌های نمودار در `stock_valuation/ui/charts.py` آبی پیش‌فرض Plotly
(`rgb(55, 128, 191)`) است و با رنگ اصلی تم (`#1D4ED8`) یکسان نیست؛ هر دو در دسترس‌اند تا انتخاب
آگاهانه انجام شود. در Tailwind 4 به‌جای پیکربندی JS باید `@config` یا بلوک
`@theme` استفاده شود.

## داشبورد Streamlit

### رابط کاربری

- تم رنگی، فونت فارسی وزیرمتن و پالت نمودارها از `.streamlit/config.toml`
  تأیید می‌شوند (بدون CSS سفارشی برای رنگ و فونت).
- چیدمان راست‌به‌چپ (RTL) در `stock_valuation.ui.theme.apply_rtl_layout`
  اعمال می‌شود و ویجت‌ها، کارت‌های شاخص و جدول‌ها را هماهنگ می‌کند.

### لایه‌بندی

- **لایه دامنه** (`stock_valuation/domain/`): توابع خالص و قطعی، بدون خواندن
  یا نوشتن وضعیت سراسری و session state، بدون هیچ import از Streamlit. هر
  تابع ورودی‌ها را صریح می‌گیرد و خروجی را برمی‌گرداند.
- **لایه API** (`stock_valuation/api/`): نگاشت REST همان توابع دامنه. تنها
  کار این لایه تعریف قرارداد JSON، ترجمه استثناهای دامنه به کد وضعیت HTTP و
  پیکربندی CORS است؛ هیچ فرمولی اینجا نوشته نمی‌شود.
- **لایه نمایش** (`stock_valuation/ui/` و `stock_cla_developed.py`):
  فقط دریافت ورودی از ویجت‌ها، رندر نتایج و نگهداری حداقلی وضعیت نمایش
  (تاریخچه محاسبات). هیچ فرمول یا قاعده کسب‌وکاری در این لایه وجود ندارد.

### قرارداد خطا

- `ValidationError` — ورودی نامعتبر یا ترکیب نامعتبر پارامترها
  (مثلاً نرخ رشد بزرگ‌تر از نرخ بازده، یا اختلاف کمتر از `MIN_SPREAD`)
- `CalculationError` — نتیجه غیرعددی یا خطای عددی در محاسبه

هر دو استثنا از `stock_valuation/domain/errors.py` وارد می‌شوند و لایه نمایش
فقط آن‌ها را به پیام کاربر تبدیل می‌کند. سرویس API همین دو استثنا را به
پاسخ 400 با بدنه ثابت تبدیل می‌کند.

## اجرای تست‌ها

تست‌ها فقط به کتابخانه استاندارد نیاز دارند و Streamlit را import نمی‌کنند:

```bash
# اجرای کامل مجموعه تست‌ها
python3 -m unittest discover -s tests -t . -v

# اجرای یک ماژول
python3 -m unittest tests.test_valuation_models -v

# در صورت نصب pytest
python3 -m pytest tests -v
```

مجموعه تست شامل ۱۵۷ تست است: مقادیر مرجع مدل‌ها (شامل WACC و DCF)، سازگاری
ارزش فعلی اجزا با قیمت کل، حداقل اختلاف نرخ بازده/WACC و رشد، ورودی‌های خالی
یا ناهم‌خوان، آستانه‌های تفسیر PEG، ماتریس حساسیت DCF (سلول مرکزی، محورها،
سلول‌های نامعتبر و پارامترهای شبکه)، رفت‌وبرگشت و حالت‌های خارج از بازه DCF
معکوس، احتمال‌ها و آمار ریسک سناریوهای وزنی، هویت‌های NPVGO و منحنی رشد
پایدار، قطعی‌بودن خروجی‌ها و بررسی نبود وابستگی لایه محاسباتی به Streamlit.

در خود برنامه نیز دکمه «اجرای تست‌های سیستم» در نوار کناری، تست‌های دودی
(`self_tests.run_self_tests`) را اجرا و نتیجه را نمایش می‌دهد.

لایه API در حال حاضر تست خودکار ندارد؛ صحت هر ۱۸ endpoint، قرارداد خطا و
پاسخ 422 با فراخوانی واقعی HTTP بررسی شده است.

## افزودن مدل جدید

1. تابع محاسباتی و در صورت نیاز نوع نتیجه را در
   `stock_valuation/domain/valuation_models.py` اضافه کنید (با docstring و
   استفاده از `ValidationError` / `CalculationError`).
2. مدل درخواست و پاسخ Pydantic را در `stock_valuation/api/schemas.py` اضافه
   کنید؛ نام فیلدهای پاسخ را با خروجی دامنه یکی بگیرید تا `model_validate`
   بدون نگاشت دستی کار کند.
3. یک endpoint در `stock_valuation/api/routes.py` اضافه کنید که فقط تابع دامنه
   را صدا بزند.
4. یک تابع `render_*` در `stock_valuation/ui/views.py` بنویسید که فقط
   ویجت‌ها و رندر را مدیریت کند و محاسبه را به لایه دامنه بسپارد، سپس گزینه
   جدید را به `st.radio` در `render_common_stock` و مسیریابی
   `stock_cla_developed.py` اضافه کنید.
5. برای تابع جدید تست در `tests/test_valuation_models.py` بنویسید.

>توسعه مدل‌های جدید: فرمول‌ها صرفاً در لایه دامنه نگهداری می‌شوند. برای اضافه کردن هر مدل جدید، تنها به نوشتن یک تابع محاسباتی کاملاً ایزوله، یک طرحواره Pydantic و یک روت هدایت‌کننده نیاز دارید. این ساختار تضمین می‌کند که رابط‌های کاربری و مسیرهای API هیچ‌گاه درگیر منطق ریاضی تکراری نشوند. 
>
>
>
