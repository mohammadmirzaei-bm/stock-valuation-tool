"""پایه‌های مشترک مدل‌های Pydantic و بدنه ثابت پاسخ خطا."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class _Base(BaseModel):
    """پایه مشترک همه مدل‌های این ماژول."""

    model_config = ConfigDict(
        # ساخت از نمونه‌های دامنه (NamedTuple / dataclass منجمد) بدون نگاشت دستی
        from_attributes=True,
        # ثبت نام فیلدها به‌صورت keyword؛ برای خواندن ساده از نمونه دامنه
        populate_by_name=True,
    )


class _RequestBase(_Base):
    """پایه بدنه درخواست‌ها؛ فیلد ناشناخته مجاز نیست."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        extra="forbid",
    )


class ErrorResponse(_Base):
    """بدنه ثابت پاسخ 400 برای خطاهای دامنه.

    ساختار سه‌فیلدی برای همه خطاهای `ValidationError` و `CalculationError`
    یکسان است تا فرانت‌اند بتواند با یک شروط واحد خطا را نمایش دهد.

    Attributes:
        error_code: کد نوع خطا (VALIDATION_ERROR یا CALCULATION_ERROR)
        message: متن خطای دامنه (فارسی)
        details: جزئیات تکمیلی؛ فعلاً همیشه null است
    """

    error_code: str = Field(description="کد نوع خطا")
    message: str = Field(description="متن خطای دامنه")
    details: Optional[dict] = Field(default=None, description="جزئیات تکمیلی؛ فعلاً null")
