# stock-valuation-tool

ابزار ارزیابی سهام بر اساس کتاب مدیریت مالی استفان راس.

یک داشبورد تعاملی Streamlit که مدل‌های تنزیل سود تقسیمی، سهام ممتاز، فرصت‌های
رشد و نسبت PEG را پیاده‌سازی می‌کند. منطق محاسباتی کاملاً از لایه نمایش جدا
است و بدون نصب Streamlit نیز قابل استفاده و آزمون است.

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
│   └── ui/                       # لایه نمایش — فقط ویجت، رندر و نمودار
│       ├── views.py              # ویجت‌ها، رندر نتایج، تاریخچه محاسبات (session state)
│       ├── charts.py             # سازنده‌های نمودار Plotly
│       └── theme.py              # چیدمان راست‌به‌چپ (RTL) رابط فارسی
├── .streamlit/
│   └── config.toml               # تم روشن مالی، فونت وزیرمتن و پالت رنگ نمودارها
├── tests/
│   └── test_valuation_models.py
├── requirements.txt
└── README.md
```

### رابط کاربری

- تم رنگی، فونت فارسی وزیرمتن و پالت نمودارها از `.streamlit/config.toml`
  تأیید می‌شوند (بدون CSS سفارشی برای رنگ و فونت).
- چیدمان راست‌به‌چپ (RTL) در `stock_valuation.ui.theme.apply_rtl_layout`
  اعمال می‌شود و ویجت‌ها، کارت‌های شاخص و جدول‌ها را هماهنگ می‌کند.

### لایه‌بندی

- **لایه دامنه** (`stock_valuation/domain/`): توابع خالص و قطعی، بدون خواندن
  یا نوشتن وضعیت سراسری و session state، بدون هیچ import از Streamlit. هر
  تابع ورودی‌ها را صریح می‌گیرد و خروجی را برمی‌گرداند.
- **لایه نمایش** (`stock_valuation/ui/` و `stock_cla_developed.py`):
  فقط دریافت ورودی از ویجت‌ها، رندر نتایج و نگهداری حداقلی وضعیت نمایش
  (تاریخچه محاسبات). هیچ فرمول یا قاعده کسب‌وکاری در این لایه وجود ندارد.

### قرارداد خطا

- `ValidationError` — ورودی نامعتبر یا ترکیب نامعتبر پارامترها
  (مثلاً نرخ رشد بزرگ‌تر از نرخ بازده، یا اختلاف کمتر از `MIN_SPREAD`)
- `CalculationError` — نتیجه غیرعددی یا خطای عددی در محاسبه

هر دو استثنا از `stock_valuation/domain/errors.py` وارد می‌شوند و لایه نمایش
فقط آن‌ها را به پیام کاربر تبدیل می‌کند.

## نصب و اجرا

پیش‌نیاز: پایتون ۳.۸ یا جدیدتر.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

streamlit run stock_cla_developed.py
```

برنامه روی `http://localhost:8501` در دسترس خواهد بود.

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

## افزودن مدل جدید

1. تابع محاسباتی و در صورت نیاز نوع نتیجه را در
   `stock_valuation/domain/valuation_models.py` اضافه کنید (با docstring و
   استفاده از `ValidationError` / `CalculationError`).
2. یک تابع `render_*` در `stock_valuation/ui/views.py` بنویسید که فقط
   ویجت‌ها و رندر را مدیریت کند و محاسبه را به لایه دامنه بسپارد.
3. گزینه جدید را به `st.radio` در `render_common_stock` و مسیریابی
   `stock_cla_developed.py` اضافه کنید.
4. برای تابع جدید تست در `tests/test_valuation_models.py` بنویسید.
