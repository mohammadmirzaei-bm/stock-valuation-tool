"""قراردادهای Pydantic ارزش‌گذاری نسبی با ضریب همتایان."""

from typing import List, Optional

from pydantic import Field

from ...domain.multiples import MultipleKind
from ...domain.validators import MIN_PEERS
from .common import _Base, _RequestBase


class PeerMultipleInput(_RequestBase):
    """ضریب یک شرکت همتا؛ نام باید یکتا و ضریب عددی باشد."""

    name: str = Field(min_length=1, description="نام یکتای همتا")
    value: float = Field(description="ضریب همتا (مثلاً P/E)")


class MultiplesRequest(_RequestBase):
    """ورودی ارزش‌گذاری نسبی هدف با ضریب همتایان.

    شاخص هدف و تعداد سهام باید مثبت باشند و ضریب‌های غیرمثبت همتایان
    در دامنه از آماره‌ها حذف می‌شوند.
    """

    kind: MultipleKind = Field(
        description="نوع ضریب: pe، pb، ps، ev_ebitda یا ev_sales"
    )
    metric: float = Field(
        description="شاخص کل هدف (سود خالص، حقوق صاحبان سهام، درآمد، EBITDA یا فروش)؛ مثبت"
    )
    shares_outstanding: float = Field(description="تعداد سهام هدف؛ مثبت")
    peers: List[PeerMultipleInput] = Field(
        min_length=MIN_PEERS,
        description="همتایان با نام یکتا؛ پس از حذف ضریب غیرمثبت حداقل MIN_PEERS معتبر لازم است",
    )
    cash: float = Field(default=0.0, description="موجودی نقد هدف (فقط ضرایب بنگاهی)")
    debt: float = Field(default=0.0, description="بدهی بهره‌دار هدف (فقط ضرایب بنگاهی)")
    minority_interest: float = Field(
        default=0.0, description="منافع اقلیت هدف (فقط ضرایب بنگاهی)"
    )
    preferred_equity: float = Field(
        default=0.0, description="سهام ممتاز هدف (فقط ضرایب بنگاهی)"
    )


class PeerStatisticsResult(_Base):
    """آماره‌های همتایان معتبر؛ معادل `PeerStatistics` دامنه."""

    used_count: int = Field(description="تعداد همتایان معتبر استفاده‌شده")
    excluded_count: int = Field(description="تعداد همتایان کنارگذاشته‌شده (ضریب غیرمثبت)")
    excluded_names: List[str] = Field(
        description="نام همتایان کنارگذاشته‌شده به ترتیب ورودی"
    )
    mean: float = Field(description="میانگین ضریب همتایان معتبر")
    median: float = Field(description="میانه ضریب همتایان معتبر")
    q1: float = Field(description="چارک اول با درون‌یابی خطی")
    q3: float = Field(description="چارک سوم با درون‌یابی خطی")
    min: float = Field(description="کمترین ضریب معتبر")
    max: float = Field(description="بیشترین ضریب معتبر")


class ImpliedCaseResult(_Base):
    """ارزش تلویحی بر پایه یک ضریب؛ معادل `ImpliedCase` دامنه."""

    multiple: float = Field(description="ضریب به‌کاررفته")
    implied_enterprise_value: Optional[float] = Field(
        description="ارزش بنگاه تلویحی؛ برای ضریب‌های حقوق صاحبان سهام null"
    )
    implied_equity_value: float = Field(
        description="ارزش حقوق صاحبان سهام تلویحی (منفی کلمپ نمی‌شود)"
    )
    value_per_share: float = Field(description="ارزش هر سهم تلویحی")


class ImpliedValuationResult(_Base):
    """پاسخ ارزش‌گذاری نسبی؛ معادل `ImpliedValuation` دامنه."""

    kind: MultipleKind = Field(description="نوع ضریب")
    metric: float = Field(description="شاخص کل هدف")
    statistics: PeerStatisticsResult = Field(description="آماره‌های همتایان معتبر")
    low: ImpliedCaseResult = Field(description="حالت چارک اول (Q1)")
    mid: ImpliedCaseResult = Field(description="حالت میانه")
    high: ImpliedCaseResult = Field(description="حالت چارک سوم (Q3)")
    mean: ImpliedCaseResult = Field(description="حالت میانگین")
