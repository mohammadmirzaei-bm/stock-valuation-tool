"""قراردادهای Pydantic تحلیل‌های تکمیلی DCF: سناریوها، حساسیت و DCF معکوس."""

from typing import List, Optional

from pydantic import Field

from ...domain.validators import (
    DEFAULT_GROWTH_STEP,
    DEFAULT_SENSITIVITY_POINTS,
    DEFAULT_WACC_STEP,
    MAX_SCENARIOS,
    MIN_SCENARIOS,
)
from .common import _Base, _RequestBase
from .dcf import CashFlowProjectionInput, DcfRequest


class ScenarioRowResult(_Base):
    """سطر نتیجهٔ سناریو؛ آینهٔ `ScenarioRow` دامنه."""

    name: str = Field(description="نام سناریو")
    probability: float = Field(description="احتمال سناریو (اعشاری)")
    probability_percent: float = Field(description="احتمال سناریو (درصد)")
    wacc: float = Field(description="نرخ WACC (اعشاری)")
    wacc_percent: float = Field(description="نرخ WACC (درصد)")
    terminal_growth: float = Field(description="نرخ رشد پایانی (اعشاری)")
    terminal_growth_percent: float = Field(description="نرخ رشد پایانی (درصد)")
    enterprise_value: float = Field(description="ارزش بنگاه")
    equity_value: float = Field(description="ارزش حقوق صاحبان سهام")
    value_per_share: float = Field(description="ارزش هر سهم")
    terminal_value_share_percent: float = Field(description="سهم ارزش پایانی از EV (درصد)")
    weighted_value_per_share: float = Field(description="سهم وزنی ارزش هر سهم")
    upside: Optional[float] = Field(description="بازده بالقوه (اعشاری)؛ بدون قیمت بازار null")
    upside_percent: Optional[float] = Field(description="بازده بالقوه (درصد)؛ بدون قیمت بازار null")


class DcfScenarioResult(_Base):
    """پاسخ سناریوهای وزنی DCF؛ آینهٔ `ScenarioValuationResult` دامنه."""

    scenarios: List[ScenarioRowResult] = Field(description="نتایج سناریوها به ترتیب ورودی")
    expected_value_per_share: float = Field(description="ارزش مورد انتظار هر سهم")
    expected_enterprise_value: float = Field(description="ارزش مورد انتظار بنگاه")
    expected_equity_value: float = Field(description="ارزش مورد انتظار حقوق صاحبان سهام")
    std_dev_value_per_share: float = Field(description="انحراف معیار وزنی ارزش هر سهم")
    min_value_per_share: float = Field(description="کمترین ارزش هر سهم")
    max_value_per_share: float = Field(description="بیشترین ارزش هر سهم")
    worst_scenario: str = Field(description="نام نخستین سناریو با کمترین ارزش")
    best_scenario: str = Field(description="نام نخستین سناریو با بیشترین ارزش")
    market_price: Optional[float] = Field(description="قیمت بازار اختیاری")
    expected_upside: Optional[float] = Field(description="بازده بالقوه مورد انتظار (اعشاری)")
    expected_upside_percent: Optional[float] = Field(description="بازده بالقوه مورد انتظار (درصد)")
    probability_of_upside: Optional[float] = Field(description="احتمال ارزش بالاتر از بازار (اعشاری)")
    probability_of_upside_percent: Optional[float] = Field(description="احتمال ارزش بالاتر از بازار (درصد)")


class DcfScenarioInput(_RequestBase):
    """ورودی یک سناریوی نام‌گذاری‌شدهٔ DCF."""

    name: str = Field(min_length=1, description="نام یکتای سناریو")
    probability: float = Field(description="احتمال سناریو؛ بین صفر و یک")
    projections: List[CashFlowProjectionInput] = Field(
        min_length=1, max_length=50, description="پیش‌بینی سالانه اجزای FCFF",
    )
    wacc: float = Field(description="نرخ WACC سناریو (اعشاری)")
    terminal_growth: float = Field(description="نرخ رشد پایانی سناریو (اعشاری)")


class DcfScenarioRequest(_RequestBase):
    """ورودی سناریوهای DCF؛ احتمال‌ها در دامنه بدون نرمال‌سازی بررسی می‌شوند."""

    scenarios: List[DcfScenarioInput] = Field(
        min_length=MIN_SCENARIOS, max_length=MAX_SCENARIOS,
        description="سناریوهای نام‌گذاری‌شده؛ مجموع احتمال‌ها برابر یک",
    )
    shares_outstanding: float = Field(description="تعداد سهام مشترک")
    tax_rate: float = Field(description="نرخ مالیات مشترک (اعشاری)")
    cash: float = Field(default=0.0, description="موجودی نقد و معادل")
    debt: float = Field(default=0.0, description="بدهی بهره‌دار")
    minority_interest: float = Field(default=0.0, description="منافع اقلیت")
    preferred_equity: float = Field(default=0.0, description="سهام ممتاز")
    market_price: Optional[float] = Field(default=None, description="قیمت بازار اختیاری")


class DcfSensitivityRequest(DcfRequest):
    """ورودی ماتریس حساسیت DCF؛ فیلدهای DCF را به ارث می‌برد و فقط
    پارامترهای شبکه (گام‌ها و تعداد نقاط محورها) را اضافه می‌کند.

    پیش‌فرض‌ها از ثابت‌های دامنه می‌آیند تا عددها دو جا تکرار نشوند؛
    اعتبارسنجی گام‌ها و تعداد نقاط در دامنه انجام می‌شود.
    """

    wacc_step: float = Field(
        default=DEFAULT_WACC_STEP, description="فاصله نقاط محور WACC (اعشاری)"
    )
    growth_step: float = Field(
        default=DEFAULT_GROWTH_STEP, description="فاصله نقاط محور رشد پایانی (اعشاری)"
    )
    wacc_points: int = Field(
        default=DEFAULT_SENSITIVITY_POINTS,
        description="تعداد نقاط محور WACC (فرد؛ ۳ تا ۱۱)",
    )
    growth_points: int = Field(
        default=DEFAULT_SENSITIVITY_POINTS,
        description="تعداد نقاط محور رشد پایانی (فرد؛ ۳ تا ۱۱)",
    )


class DcfSensitivityResult(_Base):
    """پاسخ ماتریس حساسیت DCF؛ معادل `DcfSensitivityResult` دامنه.

    سطرها محور WACC و ستون‌ها محور رشد پایانی هستند؛ `null` یعنی ترکیب
    نامعتبر (مثلاً نقض حداقل اختلاف WACC و رشد).

    Attributes:
        wacc_values: محور سطرها (اعشاری)، صعودی و مرکزچین روی WACC پایه
        growth_values: محور ستون‌ها (اعشاری)، صعودی و مرکزچین روی رشد پایه
        wacc_values_percent: محور WACC (درصد)
        growth_values_percent: محور رشد پایانی (درصد)
        value_per_share: ماتریس ارزش هر سهم؛ [i][j] ↔ wacc_values[i] × growth_values[j]
        enterprise_value: ماتریس ارزش بنگاه با همان شکل
        base_wacc: WACC حالت پایه (اعشاری)
        base_terminal_growth: نرخ رشد پایانی حالت پایه (اعشاری)
        base_row: اندیس WACC پایه در wacc_values
        base_col: اندیس رشد پایه در growth_values
        base_value_per_share: ارزش هر سهم در حالت پایه
        base_enterprise_value: ارزش بنگاه در حالت پایه
        valid_cells: تعداد سلول‌های معتبر
        total_cells: تعداد کل سلول‌ها
    """

    wacc_values: List[float] = Field(description="محور سطرها: مقادیر WACC (اعشاری)")
    growth_values: List[float] = Field(
        description="محور ستون‌ها: مقادیر رشد پایانی (اعشاری)"
    )
    wacc_values_percent: List[float] = Field(description="محور WACC (درصد)")
    growth_values_percent: List[float] = Field(description="محور رشد پایانی (درصد)")
    value_per_share: List[List[Optional[float]]] = Field(
        description="ماتریس ارزش هر سهم؛ null برای ترکیب نامعتبر"
    )
    enterprise_value: List[List[Optional[float]]] = Field(
        description="ماتریس ارزش بنگاه؛ null برای ترکیب نامعتبر"
    )
    base_wacc: float = Field(description="نرخ WACC حالت پایه (اعشاری)")
    base_terminal_growth: float = Field(description="نرخ رشد پایانی حالت پایه (اعشاری)")
    base_row: int = Field(description="اندیس WACC پایه در محور سطرها")
    base_col: int = Field(description="اندیس رشد پایه در محور ستون‌ها")
    base_value_per_share: float = Field(description="ارزش هر سهم در حالت پایه")
    base_enterprise_value: float = Field(description="ارزش بنگاه در حالت پایه")
    valid_cells: int = Field(description="تعداد سلول‌های معتبر ماتریس")
    total_cells: int = Field(description="تعداد کل سلول‌های ماتریس")


class ReverseDcfRequest(_RequestBase):
    """ورودی DCF معکوس؛ قیمت بازار برای یافتن رشد پایانی تلویحی.

    `terminal_growth` اختیاری، نرخ رشد پایانی خود تحلیل‌گر است و فقط برای
    محاسبه `growth_gap` استفاده می‌شود (به `reference_terminal_growth` دامنه نگاشت می‌شود).
    """

    projections: List[CashFlowProjectionInput] = Field(
        min_length=1,
        max_length=50,
        description="پیش‌بینی سالانه اجزای FCFF؛ سال = اندیس از ۱",
    )
    wacc: float = Field(description="نرخ WACC / تنزیل (اعشاری)")
    shares_outstanding: float = Field(description="تعداد سهام")
    tax_rate: float = Field(description="نرخ مالیات سراسری (اعشاری)")
    market_price: float = Field(description="قیمت بازار سهام")
    cash: float = Field(default=0.0, description="موجودی نقد و معادل")
    debt: float = Field(default=0.0, description="بدهی بهره‌دار")
    minority_interest: float = Field(default=0.0, description="منافع اقلیت")
    preferred_equity: float = Field(default=0.0, description="سهام ممتاز")
    terminal_growth: Optional[float] = Field(
        default=None,
        description="نرخ رشد پایانی تحلیل‌گر برای مقایسه (اعشاری)؛ اختیاری",
    )


class ReverseDcfResult(_Base):
    """پاسخ DCF معکوس؛ معادل `ReverseDcfResult` دامنه.

    Attributes:
        status: وضعیت حل (`solved` | `market_price_below_range` | `market_price_above_range`)
        market_price: قیمت بازار ورودی
        implied_growth: رشد پایانی تلویحی (اعشاری)؛ فقط در وضعیت solved
        implied_growth_percent: رشد پایانی تلویحی (درصد)؛ در غیر solved برابر null
        wacc: نرخ WACC (اعشاری)
        wacc_percent: نرخ WACC (درصد)
        search_min_growth: کرانه پایین بازه جستجو (اعشاری)
        search_max_growth: کرانه بالای بازه جستجو (اعشاری)
        value_per_share_at_min_growth: ارزش هر سهم در کرانه پایین
        value_per_share_at_max_growth: ارزش هر سهم در کرانه بالا
        enterprise_value: ارزش بنگاه در رشد تلویحی؛ در غیر solved برابر null
        equity_value: ارزش حقوق صاحبان سهام در رشد تلویحی؛ در غیر solved برابر null
        terminal_value_share_percent: سهم ارزش فعلی انتهای دوره از EV (درصد)
        reference_terminal_growth: نرخ رشد پایانی تحلیل‌گر (اعشاری)
        growth_gap: اختلاف رشد تلویحی و رشد مرجع (اعشاری)
        growth_gap_percent: اختلاف رشد تلویحی و رشد مرجع (درصد)
        message: پیام فارسی برای نمایش به کاربر
    """

    status: str = Field(description="وضعیت حل: solved یا خارج از بازه قیمت")
    market_price: float = Field(description="قیمت بازار سهام (ورودی)")
    implied_growth: Optional[float] = Field(
        default=None, description="رشد پایانی تلویحی (اعشاری)؛ فقط در وضعیت solved"
    )
    implied_growth_percent: Optional[float] = Field(
        default=None, description="رشد پایانی تلویحی (درصد)؛ در غیر solved برابر null"
    )
    wacc: float = Field(description="نرخ WACC (اعشاری)")
    wacc_percent: float = Field(description="نرخ WACC (درصد)")
    search_min_growth: float = Field(description="کرانه پایین بازه جستجوی رشد (اعشاری)")
    search_max_growth: float = Field(description="کرانه بالای بازه جستجوی رشد (اعشاری)")
    value_per_share_at_min_growth: float = Field(
        description="ارزش هر سهم در کرانه پایین بازه جستجو"
    )
    value_per_share_at_max_growth: float = Field(
        description="ارزش هر سهم در کرانه بالای بازه جستجو"
    )
    enterprise_value: Optional[float] = Field(
        default=None, description="ارزش بنگاه در رشد تلویحی؛ در غیر solved برابر null"
    )
    equity_value: Optional[float] = Field(
        default=None, description="ارزش حقوق صاحبان سهام در رشد تلویحی؛ در غیر solved برابر null"
    )
    terminal_value_share_percent: Optional[float] = Field(
        default=None, description="سهم ارزش فعلی انتهای دوره از EV (درصد)"
    )
    reference_terminal_growth: Optional[float] = Field(
        default=None, description="نرخ رشد پایانی تحلیل‌گر (اعشاری)"
    )
    growth_gap: Optional[float] = Field(
        default=None, description="اختلاف رشد تلویحی و رشد مرجع (اعشاری)"
    )
    growth_gap_percent: Optional[float] = Field(
        default=None, description="اختلاف رشد تلویحی و رشد مرجع (درصد)"
    )
    message: str = Field(description="پیام فارسی برای نمایش به کاربر")
