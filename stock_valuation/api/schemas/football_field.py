"""قراردادهای Pydantic خلاصه زمین فوتبال."""

from typing import List, Optional

from pydantic import Field

from ...domain.validators import MAX_FOOTBALL_RANGES, MIN_FOOTBALL_RANGES
from .common import _Base, _RequestBase


class ValuationRangeInput(_RequestBase):
    """بازه ارزش یک روش ارزیابی؛ ترتیب و کرانه‌ها در دامنه بررسی می‌شوند."""

    method: str = Field(min_length=1, description="نام یکتای روش ارزیابی")
    low: float = Field(description="کرانه پایین بازه؛ می‌تواند منفی باشد")
    mid: float = Field(description="مقدار میانی (ارزش پایه یا میانه)")
    high: float = Field(description="کرانه بالا؛ باید low ≤ mid ≤ high باشد")


class FootballFieldRequest(_RequestBase):
    """ورودی خلاصه زمین فوتبال از بازه‌های ارزش روش‌های مختلف."""

    ranges: List[ValuationRangeInput] = Field(
        min_length=MIN_FOOTBALL_RANGES,
        max_length=MAX_FOOTBALL_RANGES,
        description="بازه‌های ارزش روش‌ها؛ نام‌ها یکتا و low ≤ mid ≤ high",
    )
    market_price: Optional[float] = Field(
        default=None, description="قیمت بازار اختیاری (متناهی و مثبت)"
    )


class FootballFieldRowResult(_Base):
    """یک ردیف خلاصه زمین فوتبال؛ معادل `FootballFieldRow` دامنه."""

    method: str = Field(description="نام روش ارزیابی")
    low: float = Field(description="کرانه پایین بازه")
    mid: float = Field(description="مقدار میانی")
    high: float = Field(description="کرانه بالا")
    upside_of_mid: Optional[float] = Field(
        description="بازده قیمت میانی نسبت به بازار (اعشاری)؛ بدون قیمت بازار null"
    )
    upside_of_mid_percent: Optional[float] = Field(
        description="بازده قیمت میانی نسبت به بازار (درصد)؛ بدون قیمت بازار null"
    )
    market_position: Optional[str] = Field(
        description="موقعیت قیمت بازار: below، inside یا above؛ بدون قیمت بازار null"
    )


class FootballFieldResult(_Base):
    """پاسخ خلاصه زمین فوتبال؛ معادل `FootballFieldResult` دامنه."""

    rows: List[FootballFieldRowResult] = Field(description="ردیف‌ها به ترتیب ورودی")
    overall_low: float = Field(description="کمترین کرانه پایین")
    overall_high: float = Field(description="بیشترین کرانه بالا")
    median_of_mids: float = Field(description="میانه مقادیر میانی")
    mean_of_mids: float = Field(description="میانگین مقادیر میانی")
    overlap_low: float = Field(description="بیشترین کرانه پایین (شروع همپوشانی)")
    overlap_high: float = Field(description="کمترین کرانه بالا (پایان همپوشانی)")
    has_overlap: bool = Field(description="آیا همه بازه‌ها ناحیه مشترک دارند؟")
    market_price: Optional[float] = Field(description="قیمت بازار اختیاری")
    market_price_in_overlap: Optional[bool] = Field(
        description="آیا قیمت بازار داخل ناحیه همپوشانی است؟ بدون قیمت بازار null"
    )
