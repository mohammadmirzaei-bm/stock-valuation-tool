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
| نسبت PEG | `PEG = (P/E) / g` | `peg_ratio` |

برای هر مدل، توابع تجزیه (`single_period_decomposition`، `gordon_breakdown`،
`expected_return_breakdown`، `capm_breakdown`، `growth_opportunities_breakdown`،
`supernormal_schedule`) اجزای ارزش و بازده را برمی‌گردانند تا لایه نمایش
هیچ محاسبه‌ای انجام ندهد.

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
│   │   ├── routes.py             # ۱۲ endpoint زیر /api/valuation
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
| POST | `/api/valuation/peg` | `peg_ratio` + `interpret_peg` |
| GET | `/health` | بررسی دسترس‌پذیری سرویس |

### قرارداد داده

- همه نقاط پایانی محاسباتی `POST` با بدنه JSON هستند و همیشه یک شیء JSON
  برمی‌گردانند؛ حتی برای توابعی که در دامنه یک عدد یا فهرست ساده برمی‌گردانند
  (مثل `dividend-projection` و `risk-premium`).
- نرخ‌ها **اعشاری** وارد می‌شوند: ۱۲٪ برابر `0.12` است. دو استثنای خودتوضیح:
  نرخ رشد در `peg` (`growth_rate_percent`) و نرخ اوراق قرضه در `risk-premium`
  (`bond_rate_percent`) که هر دو درصدی‌اند.
- فیلدهای `*_percent` در پاسخ آماده نمایش‌اند تا فرانت‌اند محاسبه‌ای تکرار نکند.

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

مجموعه تست شامل ۵۷ تست است: مقادیر مرجع مدل‌ها، سازگاری ارزش فعلی اجزا با
قیمت کل، حداقل اختلاف نرخ بازده و رشد، ورودی‌های خالی یا ناهم‌خوان، آستانه‌های
تفسیر PEG، قطعی‌بودن خروجی‌ها و بررسی نبود وابستگی لایه محاسباتی به Streamlit.

در خود برنامه نیز دکمه «اجرای تست‌های سیستم» در نوار کناری، تست‌های دودی
(`self_tests.run_self_tests`) را اجرا و نتیجه را نمایش می‌دهد.

لایه API در حال حاضر تست خودکار ندارد؛ صحت هر ۱۲ endpoint، قرارداد خطا و
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

> لایه دامنه هنوز تنها جایی است که فرمول‌ها در آن قرار دارند. هرگونه مدلی که
> در آینده اضافه شود باید یک تابع خالص، یک آینه طرحواره و یک مسیر سه خطی
> باشد — این الگو همان چیزی است که نقاط پایانی را در هر چهار مرحله از
> ریاضیات تکراری دور نگه می‌دارد.
