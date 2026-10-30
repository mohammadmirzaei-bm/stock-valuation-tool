"""ترجمه خطاهای دامنه به پاسخ‌های HTTP.

`ValidationError` و `CalculationError` لایه دامنه هر دو به HTTP 400 با بدنه
یکسان `{"error_code", "message", "details"}` تبدیل می‌شوند.

پاسخ‌های 422 مربوط به اعتبارسنجی اسکیمای Pydantic دست‌نخورده می‌مانند: این
handlerها با شیء کلاس استثنا (نه با نام آن) ثبت می‌شوند، بنابراین با
`pydantic.ValidationError` هم‌نام که FastAPI خودش مدیریت می‌کند اشتباه
گرفته نمی‌شوند.
"""

from fastapi import Request
from fastapi.responses import JSONResponse

from ..domain.errors import CalculationError, ValidationError
from .schemas import ErrorResponse

VALIDATION_ERROR_CODE = "VALIDATION_ERROR"
CALCULATION_ERROR_CODE = "CALCULATION_ERROR"


def domain_error_response(error_code: str, message: str) -> JSONResponse:
    """ساخت پاسخ HTTP 400 با ساختار ثابت خطاهای دامنه."""
    body = ErrorResponse(error_code=error_code, message=message)
    return JSONResponse(status_code=400, content=body.model_dump())


async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """خطای اعتبارسنجی دامنه ← HTTP 400 با کد `VALIDATION_ERROR`."""
    return domain_error_response(VALIDATION_ERROR_CODE, str(exc))


async def calculation_error_handler(request: Request, exc: CalculationError) -> JSONResponse:
    """خطای محاسباتی دامنه ← HTTP 400 با کد `CALCULATION_ERROR`."""
    return domain_error_response(CALCULATION_ERROR_CODE, str(exc))
