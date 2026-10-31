"""لایه دامنه — منطق محاسباتی خالص، بدون وابستگی به لایه نمایش.

ماژول‌ها:
    errors: قرارداد خطا (`ValidationError` و `CalculationError`)
    validators: اعتبارسنجی ورودی‌ها، `MIN_SPREAD` و `require_finite_number`
    equity: ارزش‌گذاری سهام عادی (DDM، CAPM، NPVGO، رشد پایدار، PEG)
    cost_of_capital: میانگین موزون هزینه سرمایه (WACC)
    dcf: ارزش‌گذاری جریان نقدی تنزیل‌شده بر پایه FCFF
    dcf_analysis: سناریوها، ماتریس حساسیت و DCF معکوس (وابسته به dcf)
    valuation_models: نمای سازگاری عقب‌رو که نام‌های عمومی چهار ماژول بالا را
        دوباره صادر می‌کند
    self_tests: تست‌های دودی قابل اجرا از داخل برنامه
"""
