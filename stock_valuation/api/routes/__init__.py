"""نقاط پایانی REST سرویس ارزیابی سهام.

هر endpoint دقیقاً یک تابع خالص لایه دامنه را صدا می‌زند و خروجی آن را به
مدل پاسخ Pydantic نگاشت می‌کند؛ هیچ فرمولی در این لایه دوباره پیاده‌سازی
نمی‌شود. فیلدهایی که دامنه در اختیار نمی‌گذارد (نمایش مجدد ورودی یا مقدار
برگشتی ساده) همان‌جا پر می‌شوند.

خطاهای دامنه (`ValidationError` و `CalculationError`) توسط exception handlerهای
سراسری در `api.errors` به پاسخ 400 با بدنه `ErrorResponse` تبدیل می‌شوند.

ماژول‌ها:
    equity: مدل‌های سهام عادی و سود تقسیمی
    capital: میانگین موزون هزینه سرمایه (WACC)
    dcf: ارزش‌گذاری جریان نقدی تنزیل‌شده
    dcf_analysis: سناریوها، ماتریس حساسیت و DCF معکوس
    forecast: پیش‌بینی مبتنی بر محرک‌ها
    multiples: ارزش‌گذاری نسبی با ضریب همتایان
    football_field: خلاصه زمین فوتبال
    portfolio: آماره و بهینه‌سازی سبد؛ در این روتر نیست و با پیشوند
        `/api/portfolio` از `api.main` سوار می‌شود
    _common: تبدیل سطرهای پیش‌بینی درخواست به نمونه‌های دامنه
"""

from fastapi import APIRouter

from . import (
    capital,
    dcf,
    dcf_analysis,
    equity,
    football_field,
    forecast,
    multiples,
)

# پیشوند و برچسب مشترک همه مسیرها؛ زیرروترها فقط endpointها را تعریف می‌کنند.
router = APIRouter(prefix="/api/valuation", tags=["valuation"])
router.include_router(equity.router)
router.include_router(capital.router)
router.include_router(dcf.router)
router.include_router(dcf_analysis.router)
router.include_router(forecast.router)
router.include_router(multiples.router)
router.include_router(football_field.router)
