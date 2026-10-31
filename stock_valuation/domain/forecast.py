"""پیش‌بینی مبتنی بر محرک‌ها — ساخت سطرهای CashFlowProjection از چند پارامتر.

این ماژول فقط به ``domain.dcf`` وابسته است (برای ``CashFlowProjection``) و
خروجی‌اش مستقیماً به ``dcf_valuation``، ``dcf_scenario_valuation``،
``dcf_sensitivity`` و ``reverse_dcf_implied_growth`` داده می‌شود. جهت
وابستگی یک‌طرفه است: ``dcf`` هرگز از این ماژول import نمی‌کند.

قرارداد خطا:
    ValidationError: ورودی نامعتبر
    CalculationError: نتیجه غیرعددی یا خطای عددی در محاسبه
"""

import logging
import math
from dataclasses import dataclass
from typing import Callable, List, Optional, Sequence, Union

from .dcf import CashFlowProjection
from .errors import CalculationError, ValidationError
from .validators import (
    require_finite_number,
    validate_forecast_growth,
    validate_forecast_percent,
    validate_forecast_years,
    validate_positive_number,
)

logger = logging.getLogger(__name__)

# یک محرک یا یک عدد (اعمال به همه سال‌ها) یا فهرستی به طول years است
DriverValue = Union[float, Sequence[float]]


@dataclass(frozen=True)
class ForecastDrivers:
    """محرک‌های پیش‌بینی درآمد و اجزای FCFF

    هر فیلد یا یک عدد (اعمال به همه سال‌ها) یا فهرستی به طول دقیقاً
    ``years`` می‌پذیرد. نرخ مالیات محرک نیست و سراسری به ``dcf_valuation``
    داده می‌شود.

    Attributes:
        revenue_growth: نرخ رشد درآمد هر سال (اعشاری؛ بیشتر از −۱۰۰٪)
        ebitda_margin: حاشیه سود عملیاتی (۰ تا ۱)
        da_pct_revenue: نسبت استهلاک به درآمد (۰ تا ۱)
        capex_pct_revenue: نسبت مخارج سرمایه‌ای به درآمد (۰ تا ۱)
        nwc_pct_incremental_revenue: نسبت سرمایه در گردش به درآمد افزایشی (۰ تا ۱)
    """

    revenue_growth: DriverValue
    ebitda_margin: DriverValue
    da_pct_revenue: DriverValue
    capex_pct_revenue: DriverValue
    nwc_pct_incremental_revenue: DriverValue


@dataclass(frozen=True)
class ForecastYearRow:
    """یک سطر سالانه پیش‌بینی مبتنی بر محرک‌ها

    Attributes:
        year: شماره سال (۱ تا n)
        revenue: درآمد سال
        growth: نرخ رشد درآمد سال (اعشاری)
        ebitda: سود عملیاتی قبل از استهلاک و مالیات
        ebitda_margin: حاشیه سود عملیاتی سال (اعشاری)
        ebit: سود عملیاتی = EBITDA − استهلاک
        depreciation: استهلاک سال
        capex: مخارج سرمایه‌ای (خروج نقد مثبت)
        delta_nwc: تغییر سرمایه در گردش؛ مثبت = افزایش NWC (کاهش FCFF)
    """

    year: int
    revenue: float
    growth: float
    ebitda: float
    ebitda_margin: float
    ebit: float
    depreciation: float
    capex: float
    delta_nwc: float

    @property
    def growth_percent(self) -> float:
        """نرخ رشد درآمد سال به درصد"""
        return self.growth * 100

    @property
    def ebitda_margin_percent(self) -> float:
        """حاشیه سود عملیاتی سال به درصد"""
        return self.ebitda_margin * 100


@dataclass(frozen=True)
class ForecastResult:
    """نتیجه پیش‌بینی مبتنی بر محرک‌ها؛ آماده مصرف در مدل‌های DCF

    Attributes:
        projections: سطرهای ``CashFlowProjection`` برای ``dcf_valuation`` و تحلیل‌های آن
        revenues: درآمد هر سال
        ebitda: سود عملیاتی قبل از استهلاک هر سال
        rows: جدول سالانه کامل برای نمایش در UI
    """

    projections: List[CashFlowProjection]
    revenues: List[float]
    ebitda: List[float]
    rows: List[ForecastYearRow]


def _resolve_driver(
    value: DriverValue,
    years: int,
    field_name: str,
    validator: Callable[[float, str], None],
) -> List[float]:
    """تبدیل یک محرک به فهرست سالانه به طول دقیقاً ``years``

    عدد تکی به همه سال‌ها اعمال می‌شود؛ فهرست باید دقیقاً ``years`` عضو
    داشته باشد. bool و str در هر دو حالت رد می‌شوند.

    Args:
        value: عدد یا فهرست اعداد
        years: تعداد سال‌های پیش‌بینی
        field_name: نام فارسی فیلد برای پیام خطا
        validator: اعتبارسنج کرانه‌ای هر مقدار

    Raises:
        ValidationError: اگر نوع، طول یا مقادیر نامعتبر باشند
    """
    def _check(item: object) -> float:
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise ValidationError(f"❌ هر مقدار {field_name} باید عدد باشد!")
        number = float(item)
        validator(number, field_name)
        return number

    if isinstance(value, bool) or isinstance(value, str):
        raise ValidationError(f"❌ {field_name} باید عدد یا فهرست اعداد باشد!")
    if isinstance(value, (int, float)):
        return [_check(value)] * years
    if isinstance(value, (list, tuple)):
        if len(value) != years:
            raise ValidationError(
                f"❌ طول فهرست {field_name} باید برابر تعداد سال‌های "
                f"پیش‌بینی ({years}) باشد!"
            )
        return [_check(item) for item in value]
    raise ValidationError(f"❌ {field_name} باید عدد یا فهرست اعداد باشد!")


def build_projections(
    base_revenue: float,
    drivers: ForecastDrivers,
    years: int,
    terminal_growth: Optional[float] = None,
    normalize_terminal_year: bool = False,
) -> ForecastResult:
    """
    ساخت پیش‌بینی سالانه FCFF از محرک‌های بنگاه

    برای هر سال:
    ``revenue_t = revenue_{t−1} × (1 + growth_t)`` (سال ۱ از ``base_revenue``
    رشد می‌کند)، ``ebitda_t = revenue_t × margin_t``،
    ``depreciation_t = revenue_t × da_pct_t``،
    ``ebit_t = ebitda_t − depreciation_t``،
    ``capex_t = revenue_t × capex_pct_t`` و
    ``delta_nwc_t = (revenue_t − revenue_{t−1}) × nwc_pct_t``.
    قرارداد علامت مانند ``CashFlowProjection`` است: delta_nwc مثبت یعنی
    افزایش NWC (کاهش FCFF) و با رشد منفی مقدارش منفی می‌شود (بدون قدرمطلق).

    با ``normalize_terminal_year=True`` فقط در آخرین سال، Capex برابر
    استهلاک (حالت پایدار) و ``delta_nwc = nwc_pct × revenue_n × g/(1+g)``
    قرار می‌گیرد. این نرمال‌سازی مهم است چون ارزش انتهای دوره گوردون
    از همان FCFF صریح آخرین سال ساخته می‌شود (TV = FCFFₙ(1+g)/(WACC−g))؛
    اگر سال پایانی سرمایه‌گذاری غیرپایدار داشته باشد، TV حاصل بی‌معنی است.

    Args:
        base_revenue (float): آخرین درآمد تاریخی (متناهی و مثبت)
        drivers (ForecastDrivers): محرک‌های رشد و حاشیه؛ عدد تکی یا فهرست سالانه
        years (int): تعداد سال‌های پیش‌بینی (۱ تا MAX_PROJECTIONS)
        terminal_growth (Optional[float]): نرخ رشد پایانی؛ برای نرمال‌سازی
            سال پایانی لازم است و در غیر این صورت صرفاً اعتبارسنجی می‌شود
        normalize_terminal_year (bool): نرمال‌سازی آخرین سال به حالت پایدار

    Returns:
        ForecastResult: سطرهای CashFlowProjection، درآمدها، EBITDAها و جدول کامل

    Raises:
        ValidationError: در صورت ورودی نامعتبر
        CalculationError: در صورت خطای محاسباتی
    """
    if not isinstance(drivers, ForecastDrivers):
        raise ValidationError("❌ محرک‌ها باید از نوع ForecastDrivers باشند!")
    validate_forecast_years(years)
    require_finite_number(base_revenue, "درآمد پایه")
    validate_positive_number(base_revenue, "درآمد پایه")

    growth = _resolve_driver(drivers.revenue_growth, years, "نرخ رشد درآمد", validate_forecast_growth)
    margin = _resolve_driver(drivers.ebitda_margin, years, "حاشیه سود عملیاتی (EBITDA)", validate_forecast_percent)
    da_pct = _resolve_driver(drivers.da_pct_revenue, years, "نسبت استهلاک به درآمد", validate_forecast_percent)
    capex_pct = _resolve_driver(drivers.capex_pct_revenue, years, "نسبت مخارج سرمایه‌ای به درآمد", validate_forecast_percent)
    nwc_pct = _resolve_driver(drivers.nwc_pct_incremental_revenue, years, "نسبت سرمایه در گردش به درآمد افزایشی", validate_forecast_percent)

    if terminal_growth is None:
        if normalize_terminal_year:
            raise ValidationError(
                "❌ نرمال‌سازی سال پایانی بدون نرخ رشد پایانی ممکن نیست!"
            )
    else:
        validate_forecast_growth(terminal_growth, "نرخ رشد پایانی")

    try:
        projections: List[CashFlowProjection] = []
        rows: List[ForecastYearRow] = []
        revenues: List[float] = []
        ebitda_values: List[float] = []

        previous_revenue = base_revenue
        for index in range(years):
            revenue = previous_revenue * (1 + growth[index])
            ebitda = revenue * margin[index]
            depreciation = revenue * da_pct[index]
            ebit = ebitda - depreciation
            capex = revenue * capex_pct[index]
            delta_nwc = (revenue - previous_revenue) * nwc_pct[index]

            if normalize_terminal_year and index == years - 1:
                # حالت پایدار: سرمایه‌گذاری فقط جایگزین استهلاک است و
                # ΔNWC از مدل رشد پایانی گوردون می‌آید.
                capex = depreciation
                delta_nwc = (
                    nwc_pct[index] * revenue * terminal_growth / (1 + terminal_growth)
                )

            rows.append(
                ForecastYearRow(
                    year=index + 1,
                    revenue=revenue,
                    growth=growth[index],
                    ebitda=ebitda,
                    ebitda_margin=margin[index],
                    ebit=ebit,
                    depreciation=depreciation,
                    capex=capex,
                    delta_nwc=delta_nwc,
                )
            )
            projections.append(
                CashFlowProjection(
                    ebit=ebit,
                    depreciation=depreciation,
                    capex=capex,
                    delta_nwc=delta_nwc,
                )
            )
            revenues.append(revenue)
            ebitda_values.append(ebitda)
            previous_revenue = revenue

        all_values: List[float] = revenues + ebitda_values
        for row in rows:
            all_values.extend((row.ebit, row.depreciation, row.capex, row.delta_nwc))
        if not all(math.isfinite(value) for value in all_values):
            raise CalculationError("نتیجه محاسبه نامعتبر است")

        return ForecastResult(
            projections=projections,
            revenues=revenues,
            ebitda=ebitda_values,
            rows=rows,
        )
    except (ZeroDivisionError, ValueError, OverflowError) as e:
        logger.error(f"خطا در محاسبه پیش‌بینی مبتنی بر محرک‌ها: {e}")
        raise CalculationError(f"خطا در محاسبه: {str(e)}")
