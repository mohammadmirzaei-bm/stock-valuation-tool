"""نقطه ورود سرویس FastAPI برای فرانت‌اند React.

اجرا:
    uvicorn stock_valuation.api.main:app --reload

مستندات تعاملی: http://127.0.0.1:8000/docs
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..domain.errors import CalculationError, ValidationError
from .errors import calculation_error_handler, validation_error_handler
from .routes import router
from .routes.portfolio import router as portfolio_router
from .schemas import ErrorResponse

# میزبان‌های پیش‌فرض React در حالت توسعه: Vite و Create React App
_DEV_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]


def allowed_origins() -> list[str]:
    """مبداهای مجاز CORS؛ با متغیر محیطی `ALLOWED_ORIGINS` (جدا شده با کاما) بازنویسی می‌شود."""
    raw = os.getenv("ALLOWED_ORIGINS")
    if raw:
        return [origin.strip() for origin in raw.split(",") if origin.strip()]
    return _DEV_ORIGINS


app = FastAPI(
    title="Stock Valuation API",
    description="سرویس ارزیابی سهام — نگاشت REST توابع خالص لایه دامنه",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# خطاهای دامنه ← HTTP 400 با بدنه ثابت؛ پاسخ‌های 422 اسکیمای Pydantic
# دست‌نخورده می‌مانند چون برای کلاس‌های متفاوتی ثبت شده‌اند.
app.add_exception_handler(ValidationError, validation_error_handler)
app.add_exception_handler(CalculationError, calculation_error_handler)

_DOMAIN_ERROR = {
    400: {"model": ErrorResponse, "description": "خطای دامنه (اعتبارسنجی یا محاسبه)"},
}

app.include_router(router, responses=_DOMAIN_ERROR)
app.include_router(portfolio_router, responses=_DOMAIN_ERROR)


@app.get("/health", summary="بررسی سلامت سرویس")
def health() -> dict[str, str]:
    """پاسخ ساده برای بررسی دسترس‌پذیری API از فرانت‌اند React."""
    return {"status": "ok"}
