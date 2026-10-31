"""خلاصه زمین فوتبال — بازه‌های ارزش روش‌های مختلف در یک نگاه.

این ماژول بازه‌های ارزش صریح را خلاصه می‌کند و از خروجی‌های موجود
``domain.dcf_analysis`` و ``domain.multiples`` بازه می‌سازد. جهت وابستگی
یک‌طرفه است: آن دو ماژول هرگز از این ماژول import نمی‌کنند.

قرارداد خطا:
    ValidationError: ورودی نامعتبر
    CalculationError: نتیجه غیرعددی یا خطای عددی در محاسبه
"""

import math
import statistics
from dataclasses import dataclass
from typing import List, Optional

from .dcf_analysis import DcfSensitivityResult, ScenarioValuationResult
from .errors import CalculationError, ValidationError
from .multiples import ImpliedValuation
from .validators import (
    require_finite_number,
    validate_football_range_set,
    validate_positive_number,
)


@dataclass(frozen=True)
class ValuationRange:
    """بازه ارزش یک روش ارزیابی؛ کرانه‌ها می‌توانند منفی باشند

    Attributes:
        method: نام روش ارزیابی (در خلاصه باید غیرخالی و یکتا باشد)
        low: کرانه پایین
        mid: مقدار میانی (مثلاً ارزش پایه یا میانه)
        high: کرانه بالا
    """

    method: str
    low: float
    mid: float
    high: float


@dataclass(frozen=True)
class FootballFieldRow:
    """یک ردیف خلاصه زمین فوتبال

    Attributes:
        method: نام روش ارزیابی (بدون فاصله ابتدا و انتها)
        low: کرانه پایین
        mid: مقدار میانی
        high: کرانه بالا
        upside_of_mid: بازده قیمت میانی نسبت به قیمت بازار (اعشاری)؛
            بدون قیمت بازار ``None`` است
        market_position: موقعیت قیمت بازار نسبت به بازه؛ یکی از
            ``below`` (زیر بازه)، ``inside`` (داخل بازه، شامل کرانه‌ها)
            یا ``above`` (بالای بازه)؛ بدون قیمت بازار ``None`` است
    """

    method: str
    low: float
    mid: float
    high: float
    upside_of_mid: Optional[float]
    market_position: Optional[str]

    @property
    def upside_of_mid_percent(self) -> Optional[float]:
        """بازده قیمت میانی نسبت به بازار به درصد؛ بدون قیمت بازار None"""
        return None if self.upside_of_mid is None else self.upside_of_mid * 100


@dataclass(frozen=True)
class FootballFieldResult:
    """خلاصه زمین فوتبال: ردیف‌ها، دامنه کل، همپوشانی و موقعیت بازار

    Attributes:
        rows: ردیف‌ها به ترتیب ورودی
        overall_low: کمترین کرانه پایین
        overall_high: بیشترین کرانه بالا
        median_of_mids: میانه مقادیر میانی
        mean_of_mids: میانگین مقادیر میانی
        overlap_low: بیشترین کرانه پایین (شروع ناحیه همپوشانی)
        overlap_high: کمترین کرانه بالا (پایان ناحیه همپوشانی)
        has_overlap: آیا همه بازه‌ها ناحیه مشترکی دارند؟
        market_price: قیمت بازار (اختیاری)؛ بدون آن ``None``
        market_price_in_overlap: آیا قیمت بازار داخل ناحیه همپوشانی است؟
            بدون قیمت بازار ``None`` است؛ اگر همپوشانی وجود نداشته باشد
            همیشه ``False`` است.
    """

    rows: List[FootballFieldRow]
    overall_low: float
    overall_high: float
    median_of_mids: float
    mean_of_mids: float
    overlap_low: float
    overlap_high: float
    has_overlap: bool
    market_price: Optional[float]
    market_price_in_overlap: Optional[bool]


def football_field_summary(
    ranges: List[ValuationRange],
    market_price: Optional[float] = None,
) -> FootballFieldResult:
    """
    خلاصه زمین فوتبال از فهرست بازه‌های ارزش روش‌های مختلف

    ردیف‌ها به ترتیب ورودی حفظ می‌شوند. ``overlap_low`` بیشترین کرانه
    پایین و ``overlap_high`` کمترین کرانه بالاست؛ اگر
    ``overlap_low > overlap_high`` باشد هیچ ناحیه همپوشانی وجود ندارد.
    با قیمت بازار، برای هر روش بازده قیمت میانی و موقعیت بازار نسبت به
    بازه (``below``، ``inside`` یا ``above``) گزارش می‌شود؛ قیمت برابر
    کرانه‌ها «inside» شمرده می‌شود. بدون قیمت بازار، فیلدهای بازار
    ``None`` می‌مانند (نه صفر).

    Args:
        ranges: یک تا ``MAX_FOOTBALL_RANGES`` بازه با نام یکتا
        market_price: قیمت بازار اختیاری؛ متناهی و مثبت

    Returns:
        FootballFieldResult: ردیف‌ها و آماره‌های دامنه و همپوشانی

    Raises:
        ValidationError: در صورت نامعتبر بودن بازه‌ها یا قیمت بازار
        CalculationError: اگر آماره‌های محاسبه‌شده متناهی نباشند
    """
    if not isinstance(ranges, (list, tuple)) or any(
        not isinstance(item, ValuationRange) for item in ranges
    ):
        raise ValidationError("❌ بازه‌ها باید فهرستی از ValuationRange باشند!")
    validate_football_range_set(
        [item.method for item in ranges],
        [item.low for item in ranges],
        [item.mid for item in ranges],
        [item.high for item in ranges],
    )
    if market_price is not None:
        require_finite_number(market_price, "قیمت بازار")
        validate_positive_number(market_price, "قیمت بازار")

    rows: List[FootballFieldRow] = []
    for item in ranges:
        upside_of_mid: Optional[float] = None
        market_position: Optional[str] = None
        if market_price is not None:
            upside_of_mid = item.mid / market_price - 1
            if market_price < item.low:
                market_position = "below"
            elif market_price > item.high:
                market_position = "above"
            else:
                market_position = "inside"
        rows.append(
            FootballFieldRow(
                method=item.method.strip(),
                low=item.low,
                mid=item.mid,
                high=item.high,
                upside_of_mid=upside_of_mid,
                market_position=market_position,
            )
        )

    lows = [item.low for item in ranges]
    mids = [item.mid for item in ranges]
    highs = [item.high for item in ranges]
    overlap_low = max(lows)
    overlap_high = min(highs)
    has_overlap = overlap_low <= overlap_high

    result = FootballFieldResult(
        rows=rows,
        overall_low=min(lows),
        overall_high=max(highs),
        median_of_mids=statistics.median(mids),
        mean_of_mids=sum(mids) / len(mids),
        overlap_low=overlap_low,
        overlap_high=overlap_high,
        has_overlap=has_overlap,
        market_price=market_price,
        market_price_in_overlap=(
            None
            if market_price is None
            else has_overlap and overlap_low <= market_price <= overlap_high
        ),
    )

    numbers = [
        result.overall_low,
        result.overall_high,
        result.median_of_mids,
        result.mean_of_mids,
        result.overlap_low,
        result.overlap_high,
    ]
    for row in result.rows:
        numbers.extend([row.low, row.mid, row.high])
        if row.upside_of_mid is not None:
            numbers.append(row.upside_of_mid)
    if not all(math.isfinite(value) for value in numbers):
        raise CalculationError("نتیجه محاسبه نامعتبر است")
    return result


def range_from_sensitivity(
    method: str, result: DcfSensitivityResult
) -> ValuationRange:
    """
    ساخت بازه ارزش از ماتریس حساسیت DCF

    کرانه‌ها کمینه و بیشینه سلول‌های معتبر (غیر ``None``) ماتریس ارزش هر
    سهم‌اند و مقدار میانی همان ارزش حالت پایه است که در سلول مرکزی
    ماتریس قرار دارد.

    Args:
        method: نام روش ارزیابی
        result: خروجی ``dcf_sensitivity``

    Returns:
        ValuationRange: کمینه، ارزش پایه و بیشینه سلول‌های معتبر

    Raises:
        ValidationError: اگر ماتریس هیچ سلول معتبری نداشته باشد
    """
    values = [
        value
        for row in result.value_per_share
        for value in row
        if value is not None
    ]
    if not values:
        raise ValidationError("❌ ماتریس حساسیت هیچ سلول معتبری ندارد!")
    return ValuationRange(
        method=method,
        low=min(values),
        mid=result.base_value_per_share,
        high=max(values),
    )


def range_from_scenarios(
    method: str, result: ScenarioValuationResult
) -> ValuationRange:
    """
    ساخت بازه ارزش از سناریوهای وزنی DCF

    Args:
        method: نام روش ارزیابی
        result: خروجی ``dcf_scenario_valuation``

    Returns:
        ValuationRange: کمترین ارزش هر سهم، ارزش مورد انتظار و بیشترین
        ارزش هر سهم
    """
    return ValuationRange(
        method=method,
        low=result.min_value_per_share,
        mid=result.expected_value_per_share,
        high=result.max_value_per_share,
    )


def range_from_implied(
    method: str, implied: ImpliedValuation
) -> ValuationRange:
    """
    ساخت بازه ارزش از ارزش تلویحی ضریب‌های همتایان

    Args:
        method: نام روش ارزیابی
        implied: خروجی ``implied_valuation``

    Returns:
        ValuationRange: ارزش هر سهم در چارک اول، میانه و چارک سوم
    """
    return ValuationRange(
        method=method,
        low=implied.low.value_per_share,
        mid=implied.mid.value_per_share,
        high=implied.high.value_per_share,
    )
