"""مدل‌های ارزیابی سهام — منطق دامنه بدون وابستگی به لایه نمایش.

تمام توابع این ماژول خالص (pure) و قطعی هستند: ورودی‌ها را به‌صورت صریح
دریافت می‌کنند، هیچ وضعیت سراسری یا نشست (session) را نمی‌خوانند یا تغییر
نمی‌دهند و خروجی را بازمی‌گردانند. بنابراین بدون نصب Streamlit نیز
قابل استفاده و آزمون هستند.

قرارداد خطا:
    ValidationError: ورودی نامعتبر یا ترکیب نامعتبر پارامترها
    CalculationError: نتیجه غیرعددی یا خطای عددی در محاسبه
"""

import logging
import math
from dataclasses import dataclass
from typing import List, NamedTuple, Optional, Tuple

from .errors import CalculationError, ValidationError
from .validators import (
    DEFAULT_GROWTH_STEP,
    DEFAULT_SENSITIVITY_POINTS,
    DEFAULT_WACC_STEP,
    MIN_SPREAD,
    RETENTION_CURVE_STEP,
    validate_growth_rate_vs_return,
    validate_non_negative,
    validate_percentage,
    validate_positive_number,
    validate_projections_length,
    validate_retention_ratio,
    validate_scenario_set,
    validate_sensitivity_grid,
    validate_tax_rate,
    validate_terminal_growth_vs_wacc,
)

logger = logging.getLogger(__name__)


class SupernormalResult(NamedTuple):
    """نتیجه محاسبه مدل رشد غیرعادی

    Attributes:
        p0: قیمت فعلی سهام
        dividends: سودهای تقسیمی دوره غیرعادی (D₁ تا Dₙ)
        d_terminal: سود تقسیمی سال نخست پس از دوره غیرعادی (Dₙ₊₁)
        p_terminal: قیمت انتهای دوره غیرعادی (Pₙ)
        pv_dividends: ارزش فعلی سودهای تقسیمی دوره غیرعادی
        pv_p_terminal: ارزش فعلی قیمت انتهای دوره
    """

    p0: float
    dividends: List[float]
    d_terminal: float
    p_terminal: float
    pv_dividends: List[float]
    pv_p_terminal: float

    @property
    def pv_dividends_total(self) -> float:
        """مجموع ارزش فعلی سودهای تقسیمی دوره غیرعادی"""
        return sum(self.pv_dividends)


@dataclass(frozen=True)
class SinglePeriodDecomposition:
    """اجزای تنزیل‌شده ارزش در مدل تک‌دوره‌ای

    Attributes:
        p0: قیمت فعلی سهام
        pv_dividend: ارزش فعلی سود تقسیمی پایان سال
        pv_terminal_price: ارزش فعلی قیمت پایان سال
    """

    p0: float
    pv_dividend: float
    pv_terminal_price: float


@dataclass(frozen=True)
class GordonBreakdown:
    """اجزای مدل رشد ثابت گوردون

    Attributes:
        price: قیمت سهام
        d1: سود تقسیمی سال آینده
        dividend_yield: بازده سود تقسیمی (اعشاری)
        capital_gains_yield: بازده رشد سرمایه (اعشاری)
    """

    price: float
    d1: float
    dividend_yield: float
    capital_gains_yield: float

    @property
    def dividend_yield_percent(self) -> float:
        """بازده سود تقسیمی به درصد"""
        return self.dividend_yield * 100

    @property
    def capital_gains_yield_percent(self) -> float:
        """بازده رشد سرمایه به درصد"""
        return self.capital_gains_yield * 100


@dataclass(frozen=True)
class ExpectedReturnBreakdown:
    """اجزای بازده مورد انتظار سهام

    Attributes:
        r: کل بازده مورد انتظار (اعشاری)
        dividend_yield: بازده سود تقسیمی (اعشاری)
        capital_gains_yield: بازده رشد سرمایه (اعشاری)
    """

    r: float
    dividend_yield: float
    capital_gains_yield: float

    @property
    def dividend_yield_percent(self) -> float:
        """بازده سود تقسیمی به درصد"""
        return self.dividend_yield * 100

    @property
    def capital_gains_yield_percent(self) -> float:
        """بازده رشد سرمایه به درصد"""
        return self.capital_gains_yield * 100

    @property
    def total_percent(self) -> float:
        """کل بازده مورد انتظار به درصد"""
        return self.r * 100


@dataclass(frozen=True)
class CapmBreakdown:
    """اجزای بازده مورد انتظار مدل CAPM

    Attributes:
        required_return: نرخ بازده مورد انتظار سهام (اعشاری)
        risk_free_rate: نرخ بدون ریسک (اعشاری)
        beta: ضریب بتای سهام
        market_return: بازده مورد انتظار بازار (اعشاری)
        market_risk_premium: صرف ریسک بازار rm - rf (اعشاری)
        risk_premium: صرف ریسک سهام β × (rm - rf) (اعشاری)
    """

    required_return: float
    risk_free_rate: float
    beta: float
    market_return: float
    market_risk_premium: float
    risk_premium: float

    @property
    def required_return_percent(self) -> float:
        """نرخ بازده مورد انتظار سهام به درصد"""
        return self.required_return * 100

    @property
    def risk_free_rate_percent(self) -> float:
        """نرخ بدون ریسک به درصد"""
        return self.risk_free_rate * 100

    @property
    def market_risk_premium_percent(self) -> float:
        """صرف ریسک بازار به درصد"""
        return self.market_risk_premium * 100

    @property
    def risk_premium_percent(self) -> float:
        """صرف ریسک سهام به درصد"""
        return self.risk_premium * 100


@dataclass(frozen=True)
class GrowthOpportunitiesBreakdown:
    """اجزای ارزش در مدل فرصت‌های رشد

    Attributes:
        total_value: قیمت کل سهام
        no_growth_value: ارزش سهام بدون رشد (EPS/r)
        npvgo: ارزش فعلی خالص فرصت‌های رشد
        growth_share_percent: سهم فرصت‌های رشد از کل ارزش (درصد)
    """

    total_value: float
    no_growth_value: float
    npvgo: float
    growth_share_percent: float


@dataclass(frozen=True)
class RetentionCurvePoint:
    """نقطهٔ منحنی نگهداری سود؛ قیمت و NPVGO در اختلاف نامعتبر برابر None هستند."""

    retention_ratio: float
    sustainable_growth: float
    price: Optional[float]
    npvgo: Optional[float]

    @property
    def retention_ratio_percent(self) -> float:
        """نسبت نگهداری سود به درصد"""
        return self.retention_ratio * 100

    @property
    def sustainable_growth_percent(self) -> float:
        """نرخ رشد پایدار به درصد"""
        return self.sustainable_growth * 100


@dataclass(frozen=True)
class SustainableGrowthBreakdown:
    """اجزای ارزش‌گذاری رشد پایدار و فرصت‌های رشد از بازده سرمایه‌گذاری مجدد."""

    eps: float
    required_return: float
    roe: float
    retention_ratio: float
    payout_ratio: float
    sustainable_growth: float
    next_dividend: float
    price: float
    no_growth_value: float
    npvgo: float
    growth_share_percent: float
    justified_pe: float
    growth_creates_value: bool
    retention_curve: List[RetentionCurvePoint]

    @property
    def required_return_percent(self) -> float:
        """نرخ بازده مورد انتظار به درصد"""
        return self.required_return * 100

    @property
    def roe_percent(self) -> float:
        """بازده حقوق صاحبان سهام به درصد"""
        return self.roe * 100

    @property
    def retention_ratio_percent(self) -> float:
        """نسبت نگهداری سود به درصد"""
        return self.retention_ratio * 100

    @property
    def payout_ratio_percent(self) -> float:
        """نسبت تقسیم سود به درصد"""
        return self.payout_ratio * 100

    @property
    def sustainable_growth_percent(self) -> float:
        """نرخ رشد پایدار به درصد"""
        return self.sustainable_growth * 100


@dataclass(frozen=True)
class SupernormalScheduleRow:
    """یک سطر از زمان‌بندی سود تقسیمی مدل رشد غیرعادی

    Attributes:
        period: شماره سال دوره غیرعادی؛ برای سطر انتهای دوره صفر است
        growth_rate: نرخ رشد سال (اعشاری)
        dividend: سود تقسیمی سال
        present_value: ارزش فعلی سود تقسیمی سال
        is_terminal: آیا این سطر مربوط به ارزش انتهای دوره است
    """

    period: int
    growth_rate: float
    dividend: float
    present_value: float
    is_terminal: bool = False

    @property
    def growth_rate_percent(self) -> float:
        """نرخ رشد سال به درصد"""
        return self.growth_rate * 100


@dataclass(frozen=True)
class PegInterpretation:
    """تفسیر نسبت PEG

    Attributes:
        category: دسته معنایی (very_undervalued، undervalued، fair،
            near_fair، overvalued)
        level: شدت پیام برای انتخاب نوع نمایش (success، info، warning، error)
        message: متن پیام کاربر
    """

    category: str
    level: str
    message: str


@dataclass(frozen=True)
class CashFlowProjection:
    """یک سال پیش‌بینی اجزای جریان نقدی آزاد برای مدل DCF

    شماره سال برابر اندیس در فهرست است (۱ تا n). نرخ مالیات سراسری است
    و در این سطر ذخیره نمی‌شود.

    Attributes:
        ebit: سود عملیاتی قبل از بهره و مالیات
        depreciation: استهلاک و هزینه‌های غیرنقدی
        capex: مخارج سرمایه‌ای؛ مقدار مثبت یعنی خروج نقد
        delta_nwc: تغییر سرمایه در گردش؛ مقدار مثبت یعنی افزایش NWC (کاهش FCFF)
    """

    ebit: float
    depreciation: float
    capex: float
    delta_nwc: float


@dataclass(frozen=True)
class DcfScenario:
    """ورودی یک سناریوی نام‌گذاری‌شده با احتمال و پیش‌بینی مستقل DCF."""

    name: str
    probability: float
    projections: List[CashFlowProjection]
    wacc_rate: float
    terminal_growth: float


@dataclass(frozen=True)
class WaccBreakdown:
    """اجزای میانگین موزون هزینه سرمایه (WACC)

    Attributes:
        wacc: نرخ WACC (اعشاری)
        equity: ارزش بازار حقوق صاحبان سهام
        debt: ارزش بازار بدهی بهره‌دار
        total_capital: مجموع سرمایه (E + D)
        equity_weight: وزن حقوق صاحبان سهام (E/V)
        debt_weight: وزن بدهی (D/V)
        cost_of_equity: هزینه حقوق صاحبان سهام (اعشاری)
        cost_of_debt: هزینه بدهی قبل از مالیات (اعشاری)
        after_tax_cost_of_debt: هزینه بدهی بعد از مالیات (اعشاری)
        tax_rate: نرخ مالیات (اعشاری)
    """

    wacc: float
    equity: float
    debt: float
    total_capital: float
    equity_weight: float
    debt_weight: float
    cost_of_equity: float
    cost_of_debt: float
    after_tax_cost_of_debt: float
    tax_rate: float

    @property
    def wacc_percent(self) -> float:
        """نرخ WACC به درصد"""
        return self.wacc * 100

    @property
    def cost_of_equity_percent(self) -> float:
        """هزینه حقوق صاحبان سهام به درصد"""
        return self.cost_of_equity * 100

    @property
    def cost_of_debt_percent(self) -> float:
        """هزینه بدهی قبل از مالیات به درصد"""
        return self.cost_of_debt * 100

    @property
    def after_tax_cost_of_debt_percent(self) -> float:
        """هزینه بدهی بعد از مالیات به درصد"""
        return self.after_tax_cost_of_debt * 100

    @property
    def tax_rate_percent(self) -> float:
        """نرخ مالیات به درصد"""
        return self.tax_rate * 100

    @property
    def equity_weight_percent(self) -> float:
        """وزن حقوق صاحبان سهام به درصد"""
        return self.equity_weight * 100

    @property
    def debt_weight_percent(self) -> float:
        """وزن بدهی به درصد"""
        return self.debt_weight * 100


@dataclass(frozen=True)
class FcffYearRow:
    """یک سطر از جدول سالانه FCFF و ارزش فعلی در مدل DCF

    Attributes:
        year: شماره سال (۱ تا n)
        ebit: سود عملیاتی سال
        nopat: سود عملیاتی بعد از مالیات؛ EBIT × (1 − t)
        depreciation: استهلاک
        capex: مخارج سرمایه‌ای (خروج نقد مثبت)
        delta_nwc: تغییر سرمایه در گردش
        fcff: جریان نقدی آزاد بنگاه در سال t
        discount_factor: ضریب تنزیل 1 / (1+WACC)^t
        present_value: ارزش فعلی FCFF سال
    """

    year: int
    ebit: float
    nopat: float
    depreciation: float
    capex: float
    delta_nwc: float
    fcff: float
    discount_factor: float
    present_value: float


@dataclass(frozen=True)
class DcfBreakdown:
    """اجزای ارزش‌گذاری جریان نقدی تنزیل‌شده (DCF بر پایه FCFF)

    Attributes:
        enterprise_value: ارزش بنگاه (EV)
        equity_value: ارزش حقوق صاحبان سهام
        value_per_share: ارزش هر سهم
        wacc: نرخ تنزیل استفاده‌شده (اعشاری)
        terminal_growth: نرخ رشد پایانی (اعشاری)
        terminal_value: ارزش انتهای دوره در سال n (تنزیل‌نشده)
        pv_terminal_value: ارزش فعلی ارزش انتهای دوره
        pv_fcff_total: مجموع ارزش فعلی FCFFهای دوره صریح
        cash: موجودی نقد و معادل
        debt: بدهی بهره‌دار
        minority_interest: منافع اقلیت
        preferred_equity: سهام ممتاز
        shares_outstanding: تعداد سهام
        terminal_value_share_percent: سهم PV(TV) از EV (درصد)
        years: سطرهای سالانه پیش‌بینی
    """

    enterprise_value: float
    equity_value: float
    value_per_share: float
    wacc: float
    terminal_growth: float
    terminal_value: float
    pv_terminal_value: float
    pv_fcff_total: float
    cash: float
    debt: float
    minority_interest: float
    preferred_equity: float
    shares_outstanding: float
    terminal_value_share_percent: float
    years: List[FcffYearRow]

    @property
    def wacc_percent(self) -> float:
        """نرخ WACC به درصد"""
        return self.wacc * 100

    @property
    def terminal_growth_percent(self) -> float:
        """نرخ رشد پایانی به درصد"""
        return self.terminal_growth * 100


@dataclass(frozen=True)
class ScenarioRow:
    """ارزش و سهم وزنی یک سناریو؛ بازده بدون قیمت بازار برابر None است."""

    name: str
    probability: float
    wacc: float
    terminal_growth: float
    enterprise_value: float
    equity_value: float
    value_per_share: float
    terminal_value_share_percent: float
    weighted_value_per_share: float
    upside: Optional[float]

    @property
    def probability_percent(self) -> float:
        """احتمال سناریو به درصد"""
        return self.probability * 100

    @property
    def wacc_percent(self) -> float:
        """نرخ WACC به درصد"""
        return self.wacc * 100

    @property
    def terminal_growth_percent(self) -> float:
        """نرخ رشد پایانی به درصد"""
        return self.terminal_growth * 100

    @property
    def upside_percent(self) -> Optional[float]:
        """بازده بالقوه به درصد؛ بدون قیمت بازار None"""
        return None if self.upside is None else self.upside * 100


@dataclass(frozen=True)
class ScenarioValuationResult:
    """ارزش مورد انتظار و ریسک سناریوهای DCF با حفظ ترتیب ورودی."""

    scenarios: List[ScenarioRow]
    expected_value_per_share: float
    expected_enterprise_value: float
    expected_equity_value: float
    std_dev_value_per_share: float
    min_value_per_share: float
    max_value_per_share: float
    worst_scenario: str
    best_scenario: str
    market_price: Optional[float]
    expected_upside: Optional[float]
    probability_of_upside: Optional[float]

    @property
    def expected_upside_percent(self) -> Optional[float]:
        """بازده بالقوه مورد انتظار به درصد؛ بدون قیمت بازار None"""
        return None if self.expected_upside is None else self.expected_upside * 100

    @property
    def probability_of_upside_percent(self) -> Optional[float]:
        """احتمال ارزش بالاتر از بازار به درصد؛ بدون قیمت بازار None"""
        return None if self.probability_of_upside is None else self.probability_of_upside * 100


@dataclass(frozen=True)
class DcfSensitivityResult:
    """ماتریس حساسیت ارزش DCF نسبت به WACC و نرخ رشد پایانی

    سطرها محور WACC و ستون‌ها محور رشد پایانی هستند؛ سلول نامعتبر
    (مثلاً نقض حداقل اختلاف WACC و رشد) مقدار ``None`` می‌گیرد.

    Attributes:
        wacc_values: محور سطرها (اعشاری)، صعودی و مرکزچین روی WACC پایه
        growth_values: محور ستون‌ها (اعشاری)، صعودی و مرکزچین روی رشد پایه
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

    wacc_values: List[float]
    growth_values: List[float]
    value_per_share: List[List[Optional[float]]]
    enterprise_value: List[List[Optional[float]]]
    base_wacc: float
    base_terminal_growth: float
    base_row: int
    base_col: int
    base_value_per_share: float
    base_enterprise_value: float
    valid_cells: int
    total_cells: int

    @property
    def wacc_values_percent(self) -> List[float]:
        """محور WACC به درصد"""
        return [value * 100 for value in self.wacc_values]

    @property
    def growth_values_percent(self) -> List[float]:
        """محور رشد پایانی به درصد"""
        return [value * 100 for value in self.growth_values]


@dataclass(frozen=True)
class ReverseDcfResult:
    """نتیجه DCF معکوس: رشد پایانی تلویحی قیمت بازار

    Attributes:
        status: وضعیت حل؛ یکی از ``solved``، ``market_price_below_range``
            یا ``market_price_above_range``
        market_price: قیمت بازار سهام (ورودی)
        implied_growth: نرخ رشد پایانی تلویحی (اعشاری)؛ فقط در وضعیت solved
        wacc: نرخ WACC استفاده‌شده (اعشاری)
        search_min_growth: کرانه پایین بازه جستجو (اعشاری)
        search_max_growth: کرانه بالای بازه جستجو (اعشاری)
        value_per_share_at_min_growth: ارزش هر سهم در کرانه پایین جستجو
        value_per_share_at_max_growth: ارزش هر سهم در کرانه بالای جستجو
        enterprise_value: ارزش بنگاه در رشد تلویحی؛ در غیر solved برابر None
        equity_value: ارزش حقوق صاحبان سهام در رشد تلویحی؛ در غیر solved None
        terminal_value_share_percent: سهم ارزش فعلی انتهای دوره از EV (درصد)
        reference_terminal_growth: نرخ رشد پایانی تحلیل‌گر (اختیاری)
        growth_gap: اختلاف رشد تلویحی و رشد مرجع (اعشاری)
        message: پیام فارسی برای نمایش به کاربر
    """

    status: str
    market_price: float
    implied_growth: Optional[float]
    wacc: float
    search_min_growth: float
    search_max_growth: float
    value_per_share_at_min_growth: float
    value_per_share_at_max_growth: float
    enterprise_value: Optional[float]
    equity_value: Optional[float]
    terminal_value_share_percent: Optional[float]
    reference_terminal_growth: Optional[float]
    growth_gap: Optional[float]
    message: str

    @property
    def implied_growth_percent(self) -> Optional[float]:
        """رشد پایانی تلویحی به درصد؛ اگر حل نشده باشد None"""
        if self.implied_growth is None:
            return None
        return self.implied_growth * 100

    @property
    def growth_gap_percent(self) -> Optional[float]:
        """اختلاف رشد تلویحی و رشد مرجع به درصد؛ در صورت نبود مقدار None"""
        if self.growth_gap is None:
            return None
        return self.growth_gap * 100

    @property
    def wacc_percent(self) -> float:
        """نرخ WACC به درصد"""
        return self.wacc * 100


def _require_finite_number(value: float, field_name: str) -> None:
    """ورودی باید عدد متناهی باشد؛ در غیر این صورت ValidationError."""
    if not math.isfinite(value):
        raise ValidationError(f"❌ {field_name} باید عدد متناهی باشد!")


# ---------------------------------------------------------------------------
# مدل‌های اصلی ارزیابی
# ---------------------------------------------------------------------------

def single_period_model(d1: float, p1: float, r: float) -> float:
    """
    محاسبه قیمت سهام با مدل تک‌دوره‌ای

    فرمول: P₀ = (D₁ + P₁) / (1 + r)

    Args:
        d1 (float): سود تقسیمی مورد انتظار در پایان سال
        p1 (float): قیمت مورد انتظار در پایان سال
        r (float): نرخ بازده مورد انتظار (اعشاری)

    Returns:
        float: قیمت فعلی سهام

    Raises:
        ValidationError: در صورت ورودی نامعتبر
        CalculationError: در صورت خطای محاسباتی
    """
    try:
        validate_positive_number(d1, "سود تقسیمی")
        validate_positive_number(p1, "قیمت مورد انتظار")
        validate_positive_number(r, "نرخ بازده")

        result = (d1 + p1) / (1 + r)

        if not math.isfinite(result):
            raise CalculationError("نتیجه محاسبه نامعتبر است")

        return result

    except (ZeroDivisionError, ValueError) as e:
        logger.error(f"خطا در محاسبه مدل تک‌دوره‌ای: {e}")
        raise CalculationError(f"خطا در محاسبه: {str(e)}")


def single_period_decomposition(d1: float, p1: float, r: float) -> SinglePeriodDecomposition:
    """
    تجزیه تنزیل‌شده ارزش در مدل تک‌دوره‌ای

    هر دو جزء با همان نرخ بازده تنزیل می‌شوند تا مجموعشان برابر P₀ باشد.

    Args:
        d1 (float): سود تقسیمی مورد انتظار در پایان سال
        p1 (float): قیمت مورد انتظار در پایان سال
        r (float): نرخ بازده مورد انتظار (اعشاری)

    Returns:
        SinglePeriodDecomposition: قیمت فعلی و ارزش فعلی دو جزء

    Raises:
        ValidationError: در صورت ورودی نامعتبر
        CalculationError: در صورت خطای محاسباتی
    """
    p0 = single_period_model(d1, p1, r)
    return SinglePeriodDecomposition(
        p0=p0,
        pv_dividend=d1 / (1 + r),
        pv_terminal_price=p1 / (1 + r),
    )


def zero_growth_model(d: float, r: float) -> float:
    """
    محاسبه قیمت سهام با مدل رشد صفر (برای سهام ممتاز یا سهام با سود ثابت)

    فرمول: P = D / r

    Args:
        d (float): سود تقسیمی ثابت
        r (float): نرخ بازده مورد انتظار (اعشاری)

    Returns:
        float: قیمت سهام

    Raises:
        ValidationError: در صورت ورودی نامعتبر
        CalculationError: در صورت خطای محاسباتی
    """
    try:
        validate_positive_number(d, "سود تقسیمی")
        validate_positive_number(r, "نرخ بازده")

        result = d / r

        if not math.isfinite(result):
            raise CalculationError("نتیجه محاسبه نامعتبر است")

        return result

    except (ZeroDivisionError, ValueError) as e:
        logger.error(f"خطا در محاسبه مدل رشد صفر: {e}")
        raise CalculationError(f"خطا در محاسبه: {str(e)}")


def annual_dividend_yield_percent(dividend: float, price: float) -> float:
    """
    محاسبه بازده سالانه سود تقسیمی

    فرمول: (D / P) × 100

    Args:
        dividend (float): سود تقسیمی سالانه
        price (float): قیمت سهام

    Returns:
        float: بازده سالانه به درصد

    Raises:
        ValidationError: در صورت ورودی نامعتبر
        CalculationError: در صورت خطای محاسباتی
    """
    try:
        validate_positive_number(dividend, "سود تقسیمی")
        validate_positive_number(price, "قیمت سهام")

        result = (dividend / price) * 100

        if not math.isfinite(result):
            raise CalculationError("نتیجه محاسبه نامعتبر است")

        return result

    except (ZeroDivisionError, ValueError) as e:
        logger.error(f"خطا در محاسبه بازده سالانه سود تقسیمی: {e}")
        raise CalculationError(f"خطا در محاسبه: {str(e)}")


def constant_growth_model(d0: float, g: float, r: float) -> float:
    """
    محاسبه قیمت سهام با مدل رشد ثابت گوردون

    فرمول: P = D₁ / (r - g) = D₀(1+g) / (r - g)

    Args:
        d0 (float): سود تقسیمی فعلی
        g (float): نرخ رشد ثابت (اعشاری)
        r (float): نرخ بازده مورد انتظار (اعشاری)

    Returns:
        float: قیمت سهام

    Raises:
        ValidationError: در صورت ورودی نامعتبر
        CalculationError: در صورت خطای محاسباتی
    """
    try:
        validate_positive_number(d0, "سود تقسیمی فعلی")
        validate_percentage(g, "نرخ رشد")
        validate_positive_number(r, "نرخ بازده")
        validate_growth_rate_vs_return(g, r)

        d1 = d0 * (1 + g)
        result = d1 / (r - g)

        if not math.isfinite(result):
            raise CalculationError("نتیجه محاسبه نامعتبر است")

        return result

    except (ZeroDivisionError, ValueError) as e:
        logger.error(f"خطا در محاسبه مدل گوردون: {e}")
        raise CalculationError(f"خطا در محاسبه: {str(e)}")


def gordon_breakdown(d0: float, g: float, r: float) -> GordonBreakdown:
    """
    تجزیه قیمت و بازده‌های مدل رشد ثابت گوردون

    Args:
        d0 (float): سود تقسیمی فعلی
        g (float): نرخ رشد ثابت (اعشاری)
        r (float): نرخ بازده مورد انتظار (اعشاری)

    Returns:
        GordonBreakdown: قیمت، سود تقسیمی سال آینده و اجزای بازده

    Raises:
        ValidationError: در صورت ورودی نامعتبر
        CalculationError: در صورت خطای محاسباتی
    """
    price = constant_growth_model(d0, g, r)
    d1 = d0 * (1 + g)
    return GordonBreakdown(
        price=price,
        d1=d1,
        dividend_yield=d1 / price,
        capital_gains_yield=g,
    )


def project_dividends(d0: float, g: float, periods: int) -> List[float]:
    """
    پیش‌بینی سود تقسیمی دوره‌های آینده

    فرمول: Dₜ = D₀(1+g)ᵗ

    Args:
        d0 (float): سود تقسیمی فعلی
        g (float): نرخ رشد ثابت (اعشاری)
        periods (int): تعداد دوره‌های پیش‌بینی

    Returns:
        List[float]: سودهای تقسیمی پیش‌بینی‌شده از دوره ۱ تا periods

    Raises:
        ValidationError: در صورت ورودی نامعتبر
        CalculationError: در صورت سرریز عددی یا نتیجه غیرعددی
    """
    validate_positive_number(d0, "سود تقسیمی فعلی")
    validate_percentage(g, "نرخ رشد")

    if periods <= 0:
        raise ValidationError("تعداد دوره‌های پیش‌بینی باید حداقل ۱ باشد")

    try:
        dividends = [d0 * math.pow(1 + g, period) for period in range(1, periods + 1)]
    except OverflowError as e:
        logger.error(f"خطا در پیش‌بینی سود تقسیمی: {e}")
        raise CalculationError(f"خطا در محاسبه: {str(e)}")

    if not all(math.isfinite(value) for value in dividends):
        raise CalculationError("نتیجه محاسبه نامعتبر است")

    return dividends


def supernormal_growth_model(d0: float, growth_rates: List[float], years: int,
                             g_constant: float, r: float) -> SupernormalResult:
    """
    محاسبه قیمت سهام با مدل رشد غیرعادی (دو مرحله‌ای یا چند مرحله‌ای)

    فرمول: P₀ = Σ[Dₜ/(1+r)ᵗ] + Pₙ/(1+r)ⁿ
    که Pₙ = Dₙ₊₁ / (r - g_constant)

    Args:
        d0 (float): سود تقسیمی فعلی
        growth_rates (List[float]): فهرست نرخ‌های رشد برای دوره غیرعادی
        years (int): تعداد سال‌های دوره غیرعادی
        g_constant (float): نرخ رشد ثابت پس از دوره غیرعادی
        r (float): نرخ بازده مورد انتظار

    Returns:
        SupernormalResult: قیمت فعلی، سودهای تقسیمی، سود تقسیمی انتهای دوره (Dₙ₊₁)،
        قیمت انتهای دوره (Pₙ) و ارزش فعلی آنها

    Raises:
        ValidationError: در صورت ورودی نامعتبر
        CalculationError: در صورت خطای محاسباتی
    """
    try:
        validate_positive_number(d0, "سود تقسیمی فعلی")
        validate_positive_number(r, "نرخ بازده")
        validate_percentage(g_constant, "نرخ رشد ثابت")
        validate_growth_rate_vs_return(g_constant, r)

        if years <= 0 or not growth_rates:
            raise ValidationError("تعداد سال‌های رشد غیرعادی باید حداقل ۱ باشد")

        if len(growth_rates) != years:
            raise ValidationError("تعداد نرخ‌های رشد باید با تعداد سال‌ها برابر باشد")

        for i, g in enumerate(growth_rates):
            validate_percentage(g, f"نرخ رشد سال {i+1}")

        dividends = []
        pv_dividends = []
        current_d = d0

        # محاسبه سودهای تقسیمی و ارزش فعلی آنها برای دوره غیرعادی
        for i, g in enumerate(growth_rates):
            current_d = current_d * (1 + g)
            dividends.append(current_d)

            # استفاده از math.pow برای قدرت‌گیری
            pv_dividend = current_d / math.pow(1 + r, i + 1)
            pv_dividends.append(pv_dividend)

        # محاسبه ارزش انتهای دوره (Terminal Value)
        d_terminal = dividends[-1] * (1 + g_constant)  # سود سال بعد از پایان دوره غیرعادی
        p_terminal = d_terminal / (r - g_constant)  # قیمت انتهای دوره

        # ارزش فعلی قیمت انتهای دوره
        pv_p_terminal = p_terminal / math.pow(1 + r, years)

        # قیمت فعلی کل
        p0 = sum(pv_dividends) + pv_p_terminal

        if not math.isfinite(p0):
            raise CalculationError("نتیجه محاسبه نامعتبر است")

        return SupernormalResult(
            p0=p0,
            dividends=dividends,
            d_terminal=d_terminal,
            p_terminal=p_terminal,
            pv_dividends=pv_dividends,
            pv_p_terminal=pv_p_terminal,
        )

    except (ZeroDivisionError, ValueError, OverflowError) as e:
        logger.error(f"خطا در محاسبه مدل رشد غیرعادی: {e}")
        raise CalculationError(f"خطا در محاسبه: {str(e)}")


def supernormal_schedule(growth_rates: List[float], result: SupernormalResult,
                         g_constant: float) -> List[SupernormalScheduleRow]:
    """
    ساخت زمان‌بندی سود تقسیمی و ارزش فعلی برای نمایش مدل رشد غیرعادی

    Args:
        growth_rates (List[float]): نرخ‌های رشد دوره غیرعادی (اعشاری)
        result (SupernormalResult): خروجی مدل رشد غیرعادی
        g_constant (float): نرخ رشد ثابت پس از دوره غیرعادی

    Returns:
        List[SupernormalScheduleRow]: سطرهای دوره غیرعادی و سطر انتهای دوره

    Raises:
        ValidationError: اگر نرخ‌های رشد با خروجی مدل هم‌خوانی نداشته باشند
    """
    if not (len(growth_rates) == len(result.dividends) == len(result.pv_dividends)):
        raise ValidationError("تعداد نرخ‌های رشد با خروجی مدل هم‌خوانی ندارد")

    rows = [
        SupernormalScheduleRow(
            period=i + 1,
            growth_rate=g,
            dividend=dividend,
            present_value=pv_dividend,
        )
        for i, (g, dividend, pv_dividend) in enumerate(
            zip(growth_rates, result.dividends, result.pv_dividends)
        )
    ]
    rows.append(
        SupernormalScheduleRow(
            period=0,
            growth_rate=g_constant,
            dividend=result.d_terminal,
            present_value=result.pv_p_terminal,
            is_terminal=True,
        )
    )
    return rows


def expected_return(d1: float, p0: float, g: float) -> float:
    """
    محاسبه بازده مورد انتظار سهام

    فرمول: r = (D₁/P₀) + g

    Args:
        d1 (float): سود تقسیمی مورد انتظار سال آینده
        p0 (float): قیمت فعلی سهام
        g (float): نرخ رشد سود تقسیمی (اعشاری)

    Returns:
        float: نرخ بازده مورد انتظار (اعشاری)

    Raises:
        ValidationError: در صورت ورودی نامعتبر
        CalculationError: در صورت خطای محاسباتی
    """
    try:
        validate_positive_number(d1, "سود تقسیمی مورد انتظار")
        validate_positive_number(p0, "قیمت فعلی سهام")
        validate_percentage(g, "نرخ رشد")

        dividend_yield = d1 / p0
        result = dividend_yield + g

        if not math.isfinite(result):
            raise CalculationError("نتیجه محاسبه نامعتبر است")

        return result

    except (ZeroDivisionError, ValueError) as e:
        logger.error(f"خطا در محاسبه بازده مورد انتظار: {e}")
        raise CalculationError(f"خطا در محاسبه: {str(e)}")


def expected_return_breakdown(d1: float, p0: float, g: float) -> ExpectedReturnBreakdown:
    """
    تجزیه بازده مورد انتظار به اجزای آن

    Args:
        d1 (float): سود تقسیمی مورد انتظار سال آینده
        p0 (float): قیمت فعلی سهام
        g (float): نرخ رشد سود تقسیمی (اعشاری)

    Returns:
        ExpectedReturnBreakdown: بازده کل و اجزای آن

    Raises:
        ValidationError: در صورت ورودی نامعتبر
        CalculationError: در صورت خطای محاسباتی
    """
    r = expected_return(d1, p0, g)
    return ExpectedReturnBreakdown(
        r=r,
        dividend_yield=d1 / p0,
        capital_gains_yield=g,
    )


def capm_required_return(risk_free_rate: float, beta: float,
                         market_return: float) -> float:
    """
    محاسبه نرخ بازده مورد انتظار سهام با مدل قیمت‌گذاری دارایی سرمایه‌ای (CAPM)

    فرمول: r = rf + β × (rm - rf)

    Args:
        risk_free_rate (float): نرخ بدون ریسک (اعشاری)
        beta (float): ضریب بتای سهام (حساسیت به بازار)
        market_return (float): بازده مورد انتظار بازار (اعشاری)

    Returns:
        float: نرخ بازده مورد انتظار سهام (اعشاری)

    Raises:
        ValidationError: در صورت ورودی نامعتبر یا بازده بازار ناکافی
        CalculationError: در صورت خطای محاسباتی
    """
    try:
        validate_positive_number(risk_free_rate, "نرخ بدون ریسک")
        validate_positive_number(beta, "ضریب بتا")
        validate_positive_number(market_return, "بازده بازار")

        if market_return <= risk_free_rate:
            raise ValidationError(
                f"❌ بازده بازار ({market_return*100:.1f}%) باید بیشتر از "
                f"نرخ بدون ریسک ({risk_free_rate*100:.1f}%) باشد!"
            )

        market_risk_premium = market_return - risk_free_rate
        risk_premium = beta * market_risk_premium
        result = risk_free_rate + risk_premium

        if not math.isfinite(result):
            raise CalculationError("نتیجه محاسبه نامعتبر است")

        return result

    except (ZeroDivisionError, ValueError, OverflowError) as e:
        logger.error(f"خطا در محاسبه مدل CAPM: {e}")
        raise CalculationError(f"خطا در محاسبه: {str(e)}")


def capm_breakdown(risk_free_rate: float, beta: float,
                   market_return: float) -> CapmBreakdown:
    """
    تجزیه بازده مورد انتظار مدل CAPM به اجزای آن

    Args:
        risk_free_rate (float): نرخ بدون ریسک (اعشاری)
        beta (float): ضریب بتای سهام
        market_return (float): بازده مورد انتظار بازار (اعشاری)

    Returns:
        CapmBreakdown: بازده مورد انتظار، صرف ریسک بازار و صرف ریسک سهام

    Raises:
        ValidationError: در صورت ورودی نامعتبر
        CalculationError: در صورت خطای محاسباتی
    """
    required_return = capm_required_return(risk_free_rate, beta, market_return)
    market_risk_premium = market_return - risk_free_rate
    return CapmBreakdown(
        required_return=required_return,
        risk_free_rate=risk_free_rate,
        beta=beta,
        market_return=market_return,
        market_risk_premium=market_risk_premium,
        risk_premium=beta * market_risk_premium,
    )


def preferred_stock_valuation(d: float, r: float) -> float:
    """
    محاسبه قیمت سهام ممتاز

    فرمول: P = D / r
    سهام ممتاز معمولاً سود تقسیمی ثابت و بی‌نهایت دارند

    Args:
        d (float): سود تقسیمی ثابت سالانه
        r (float): نرخ بازده مورد انتظار (اعشاری)

    Returns:
        float: قیمت سهام ممتاز

    Raises:
        ValidationError: در صورت ورودی نامعتبر
        CalculationError: در صورت خطای محاسباتی
    """
    return zero_growth_model(d, r)  # منطق یکسان با مدل رشد صفر


def risk_premium_percent(required_return: float, bond_rate_percent: float) -> float:
    """
    محاسبه حق‌الریسک سهام در مقایسه با اوراق قرضه

    فرمول: (r - نرخ اوراق قرضه) × 100

    Args:
        required_return (float): نرخ بازده مورد انتظار سهام (اعشاری)
        bond_rate_percent (float): نرخ اوراق قرضه مشابه (درصد)

    Returns:
        float: حق‌الریسک بر حسب واحد درصد

    Raises:
        ValidationError: در صورت ورودی نامعتبر
    """
    validate_positive_number(required_return, "نرخ بازده")
    validate_positive_number(bond_rate_percent, "نرخ اوراق قرضه")

    return (required_return - bond_rate_percent / 100) * 100


def growth_opportunities_valuation(eps: float, r: float, npvgo: float) -> Tuple[float, float]:
    """
    محاسبه قیمت سهام با در نظر گیری فرصت‌های رشد

    فرمول: P = (EPS/r) + NPVGO

    Args:
        eps (float): سود هر سهم
        r (float): نرخ بازده مورد انتظار (اعشاری)
        npvgo (float): ارزش فعلی خالص فرصت‌های رشد

    Returns:
        Tuple[float, float]: قیمت کل سهام، ارزش بدون رشد

    Raises:
        ValidationError: در صورت ورودی نامعتبر
        CalculationError: در صورت خطای محاسباتی
    """
    try:
        validate_positive_number(eps, "سود هر سهم")
        validate_positive_number(r, "نرخ بازده")
        # NPVGO می‌تواند منفی باشد (فرصت‌های بد)

        no_growth_value = eps / r
        total_value = no_growth_value + npvgo

        if not math.isfinite(total_value):
            raise CalculationError("نتیجه محاسبه نامعتبر است")

        return total_value, no_growth_value

    except (ZeroDivisionError, ValueError) as e:
        logger.error(f"خطا در محاسبه ارزیابی با فرصت‌های رشد: {e}")
        raise CalculationError(f"خطا در محاسبه: {str(e)}")


def growth_opportunities_breakdown(eps: float, r: float,
                                   npvgo: float) -> GrowthOpportunitiesBreakdown:
    """
    تجزیه ارزش سهام به بخش بدون رشد و فرصت‌های رشد

    Args:
        eps (float): سود هر سهم
        r (float): نرخ بازده مورد انتظار (اعشاری)
        npvgo (float): ارزش فعلی خالص فرصت‌های رشد

    Returns:
        GrowthOpportunitiesBreakdown: ارزش کل، ارزش بدون رشد و سهم فرصت‌های رشد

    Raises:
        ValidationError: در صورت ورودی نامعتبر
        CalculationError: در صورت خطای محاسباتی
    """
    total_value, no_growth_value = growth_opportunities_valuation(eps, r, npvgo)
    growth_share_percent = (npvgo / total_value) * 100 if total_value != 0 else 0

    return GrowthOpportunitiesBreakdown(
        total_value=total_value,
        no_growth_value=no_growth_value,
        npvgo=npvgo,
        growth_share_percent=growth_share_percent,
    )


def _sustainable_growth_core(
    eps: float, r: float, roe: float, retention_ratio: float
) -> Tuple[float, float, float, float]:
    """محاسبهٔ مشترک رشد، سود تقسیمی، قیمت و NPVGO برای نتیجه و منحنی."""
    growth = retention_ratio * roe
    validate_growth_rate_vs_return(growth, r)
    dividend = eps * (1 - retention_ratio)
    price = dividend / (r - growth)
    npvgo = price - eps / r
    if not all(math.isfinite(value) for value in (growth, dividend, price, npvgo)):
        raise CalculationError("نتیجه محاسبه نامعتبر است")
    return growth, dividend, price, npvgo


def sustainable_growth_valuation(
    eps: float, r: float, roe: float, retention_ratio: float
) -> SustainableGrowthBreakdown:
    """ارزش‌گذاری رشد پایدار با g = b × ROE و استخراج فرصت‌های رشد.

    Args:
        eps: سود هر سهم سال آینده؛ مثبت
        r: نرخ بازده مورد انتظار؛ اعشاری و مثبت
        roe: بازده حقوق صاحبان سهام؛ اعشاری، مثبت و حداکثر ۲
        retention_ratio: نسبت نگهداری سود؛ ۰ ≤ b < ۱

    Returns:
        SustainableGrowthBreakdown: اجزای ارزش و ده نقطهٔ منحنی نگهداری سود

    Raises:
        ValidationError: ورودی یا اختلاف نرخ رشد و بازده نامعتبر
        CalculationError: نتیجهٔ غیرمتناهی یا ناسازگاری تجزیهٔ ارزش
    """
    for value, name in ((eps, "سود هر سهم"), (r, "نرخ بازده"), (roe, "ROE"),
                        (retention_ratio, "نسبت نگهداری سود")):
        _require_finite_number(value, name)
    validate_positive_number(eps, "سود هر سهم")
    validate_positive_number(r, "نرخ بازده")
    validate_positive_number(roe, "ROE")
    validate_percentage(roe, "ROE")
    validate_retention_ratio(retention_ratio)

    try:
        growth, dividend, price, npvgo = _sustainable_growth_core(eps, r, roe, retention_ratio)
        breakdown = growth_opportunities_breakdown(eps, r, npvgo)
        if not math.isclose(breakdown.total_value, price, rel_tol=1e-9, abs_tol=0.0):
            raise CalculationError("نتیجه محاسبه نامعتبر است")

        curve: List[RetentionCurvePoint] = []
        for index in range(10):
            b = round(index * RETENTION_CURVE_STEP, 10)
            try:
                point_growth, _, point_price, point_npvgo = _sustainable_growth_core(eps, r, roe, b)
            except ValidationError:
                point_growth, point_price, point_npvgo = b * roe, None, None
            curve.append(RetentionCurvePoint(b, point_growth, point_price, point_npvgo))

        result = SustainableGrowthBreakdown(
            eps=eps, required_return=r, roe=roe, retention_ratio=retention_ratio,
            payout_ratio=1 - retention_ratio, sustainable_growth=growth,
            next_dividend=dividend, price=price, no_growth_value=breakdown.no_growth_value,
            npvgo=npvgo, growth_share_percent=breakdown.growth_share_percent,
            justified_pe=price / eps, growth_creates_value=roe > r, retention_curve=curve,
        )
        if not all(math.isfinite(value) for value in (
            result.eps, result.required_return, result.roe, result.retention_ratio,
            result.payout_ratio, result.sustainable_growth, result.next_dividend,
            result.price, result.no_growth_value, result.npvgo, result.growth_share_percent,
            result.justified_pe, result.required_return_percent, result.roe_percent,
            result.retention_ratio_percent, result.payout_ratio_percent,
            result.sustainable_growth_percent, breakdown.total_value,
        )):
            raise CalculationError("نتیجه محاسبه نامعتبر است")
        for point in curve:
            if not all(value is None or math.isfinite(value) for value in (
                point.retention_ratio, point.sustainable_growth, point.price, point.npvgo,
                point.retention_ratio_percent, point.sustainable_growth_percent,
            )):
                raise CalculationError("نتیجه محاسبه نامعتبر است")
        return result
    except (ZeroDivisionError, ValueError, OverflowError) as exc:
        raise CalculationError("نتیجه محاسبه نامعتبر است") from exc


def peg_ratio(pe_ratio: float, growth_rate: float) -> float:
    """
    محاسبه نسبت PEG (Price/Earnings to Growth)

    فرمول: PEG = (P/E) / نرخ رشد سالانه سود

    Args:
        pe_ratio (float): نسبت P/E
        growth_rate (float): نرخ رشد سالانه سود (درصد)

    Returns:
        float: نسبت PEG

    Raises:
        ValidationError: در صورت ورودی نامعتبر
        CalculationError: در صورت خطای محاسباتی
    """
    try:
        validate_positive_number(pe_ratio, "نسبت P/E")
        validate_positive_number(growth_rate, "نرخ رشد سود")

        if growth_rate > 100:
            raise ValidationError("نرخ رشد بیش از 100% غیرمنطقی است!")

        result = pe_ratio / growth_rate

        if not math.isfinite(result):
            raise CalculationError("نتیجه محاسبه نامعتبر است")

        return result

    except (ZeroDivisionError, ValueError) as e:
        logger.error(f"خطا در محاسبه نسبت PEG: {e}")
        raise CalculationError(f"خطا در محاسبه: {str(e)}")


def interpret_peg(peg: float) -> PegInterpretation:
    """
    تفسیر نسبت PEG بر اساس آستانه‌های استاندارد

    Args:
        peg (float): نسبت PEG محاسبه‌شده

    Returns:
        PegInterpretation: دسته، سطح پیام و متن تفسیر

    Raises:
        ValidationError: اگر نسبت PEG مثبت نباشد
    """
    validate_positive_number(peg, "نسبت PEG")

    if peg < 0.5:
        return PegInterpretation(
            category="very_undervalued",
            level="success",
            message="🟢 نسبت PEG خیلی کم: احتمالاً سهم بسیار کم‌ارزش است",
        )
    if peg < 1:
        return PegInterpretation(
            category="undervalued",
            level="info",
            message="🟡 نسبت PEG کمتر از 1: احتمالاً سهم کم‌ارزش است",
        )
    if peg == 1:
        return PegInterpretation(
            category="fair",
            level="info",
            message="⚖️ نسبت PEG برابر 1: سهم منصفانه قیمت‌گذاری شده",
        )
    if peg < 1.5:
        return PegInterpretation(
            category="near_fair",
            level="warning",
            message="🟠 نسبت PEG بین 1-1.5: قیمت‌گذاری نزدیک به منصفانه",
        )
    return PegInterpretation(
        category="overvalued",
        level="error",
        message="🔴 نسبت PEG بیشتر از 1.5: احتمالاً سهم بیش‌ارزش است",
    )


# ---------------------------------------------------------------------------
# WACC و DCF (بر پایه FCFF)
# ---------------------------------------------------------------------------

# کرانه پایین جستجوی نرخ رشد پایانی در DCF معکوس
# (بازار ممکن است کاهش را قیمت‌گذاری کند)
REVERSE_DCF_MIN_GROWTH = -0.20


def calculate_fcff(ebit: float, tax_rate: float, depreciation: float,
                   capex: float, delta_nwc: float) -> float:
    """
    محاسبه جریان نقدی آزاد بنگاه (FCFF)

    فرمول: FCFF = EBIT(1 − t) + Dep − Capex − ΔNWC

    قرارداد علامت: Capex مثبت یعنی خروج نقد؛ ΔNWC مثبت یعنی افزایش سرمایه
    در گردش (کاهش FCFF).

    Args:
        ebit (float): سود عملیاتی قبل از بهره و مالیات
        tax_rate (float): نرخ مالیات (اعشاری؛ ۰ ≤ t < ۱)
        depreciation (float): استهلاک و هزینه‌های غیرنقدی
        capex (float): مخارج سرمایه‌ای (خروج نقد مثبت)
        delta_nwc (float): تغییر سرمایه در گردش

    Returns:
        float: جریان نقدی آزاد بنگاه

    Raises:
        ValidationError: در صورت ورودی نامعتبر
        CalculationError: در صورت خطای محاسباتی
    """
    _require_finite_number(ebit, "سود عملیاتی (EBIT)")
    _require_finite_number(tax_rate, "نرخ مالیات")
    _require_finite_number(depreciation, "استهلاک")
    _require_finite_number(capex, "مخارج سرمایه‌ای")
    _require_finite_number(delta_nwc, "تغییر سرمایه در گردش")
    validate_tax_rate(tax_rate)

    try:
        result = ebit * (1 - tax_rate) + depreciation - capex - delta_nwc
        if not math.isfinite(result):
            raise CalculationError("نتیجه محاسبه نامعتبر است")
        return result
    except (ZeroDivisionError, ValueError, OverflowError) as e:
        logger.error(f"خطا در محاسبه FCFF: {e}")
        raise CalculationError(f"خطا در محاسبه: {str(e)}")


def wacc(equity: float, debt: float, cost_of_equity: float,
         cost_of_debt: float, tax_rate: float) -> float:
    """
    محاسبه میانگین موزون هزینه سرمایه (WACC)

    فرمول: WACC = (E/V)×rₑ + (D/V)×r_d×(1 − t) که V = E + D

    بدهی صفر برای بنگاه تمام‌سهامی مجاز است؛ در آن حالت WACC = rₑ.

    Args:
        equity (float): ارزش بازار حقوق صاحبان سهام (باید مثبت باشد)
        debt (float): ارزش بازار بدهی (نامنفی؛ صفر مجاز)
        cost_of_equity (float): هزینه حقوق صاحبان سهام (اعشاری؛ مثبت)
        cost_of_debt (float): هزینه بدهی قبل از مالیات (اعشاری؛ نامنفی)
        tax_rate (float): نرخ مالیات (اعشاری؛ ۰ ≤ t < ۱)

    Returns:
        float: نرخ WACC (اعشاری)

    Raises:
        ValidationError: در صورت ورودی نامعتبر
        CalculationError: در صورت خطای محاسباتی
    """
    return wacc_breakdown(equity, debt, cost_of_equity, cost_of_debt, tax_rate).wacc


def wacc_breakdown(equity: float, debt: float, cost_of_equity: float,
                   cost_of_debt: float, tax_rate: float) -> WaccBreakdown:
    """
    تجزیه میانگین موزون هزینه سرمایه به اجزای آن

    Args:
        equity (float): ارزش بازار حقوق صاحبان سهام
        debt (float): ارزش بازار بدهی
        cost_of_equity (float): هزینه حقوق صاحبان سهام (اعشاری)
        cost_of_debt (float): هزینه بدهی قبل از مالیات (اعشاری)
        tax_rate (float): نرخ مالیات (اعشاری)

    Returns:
        WaccBreakdown: WACC، وزن‌ها و هزینه بدهی بعد از مالیات

    Raises:
        ValidationError: در صورت ورودی نامعتبر
        CalculationError: در صورت خطای محاسباتی
    """
    _require_finite_number(equity, "ارزش حقوق صاحبان سهام")
    _require_finite_number(debt, "ارزش بدهی")
    _require_finite_number(cost_of_equity, "هزینه حقوق صاحبان سهام")
    _require_finite_number(cost_of_debt, "هزینه بدهی")
    _require_finite_number(tax_rate, "نرخ مالیات")

    validate_positive_number(equity, "ارزش حقوق صاحبان سهام")
    validate_non_negative(debt, "ارزش بدهی")
    validate_positive_number(cost_of_equity, "هزینه حقوق صاحبان سهام")
    validate_non_negative(cost_of_debt, "هزینه بدهی")
    validate_tax_rate(tax_rate)

    total_capital = equity + debt
    if total_capital <= 0:
        raise ValidationError(
            "❌ مجموع سرمایه (حقوق صاحبان سهام + بدهی) باید مثبت باشد!"
        )

    try:
        equity_weight = equity / total_capital
        debt_weight = debt / total_capital
        after_tax_cost_of_debt = cost_of_debt * (1 - tax_rate)
        result = (
            equity_weight * cost_of_equity
            + debt_weight * after_tax_cost_of_debt
        )

        if not math.isfinite(result):
            raise CalculationError("نتیجه محاسبه نامعتبر است")

        return WaccBreakdown(
            wacc=result,
            equity=equity,
            debt=debt,
            total_capital=total_capital,
            equity_weight=equity_weight,
            debt_weight=debt_weight,
            cost_of_equity=cost_of_equity,
            cost_of_debt=cost_of_debt,
            after_tax_cost_of_debt=after_tax_cost_of_debt,
            tax_rate=tax_rate,
        )
    except (ZeroDivisionError, ValueError, OverflowError) as e:
        logger.error(f"خطا در محاسبه WACC: {e}")
        raise CalculationError(f"خطا در محاسبه: {str(e)}")


def dcf_valuation(
    projections: List[CashFlowProjection],
    wacc_rate: float,
    terminal_growth: float,
    shares_outstanding: float,
    tax_rate: float,
    cash: float = 0.0,
    debt: float = 0.0,
    minority_interest: float = 0.0,
    preferred_equity: float = 0.0,
) -> DcfBreakdown:
    """
    ارزش‌گذاری بنگاه با تنزیل جریان نقدی آزاد (DCF بر پایه FCFF)

    جریان‌های سال t در پایان سال با (1+WACC)^t تنزیل می‌شوند.
    ارزش انتهای دوره: TV = FCFFₙ(1+g)/(WACC−g) و PV(TV) = TV/(1+WACC)^n.
    پل ارزش حقوق صاحبان سهام:
    Equity = EV + cash − debt − minority_interest − preferred_equity
    (مقدار منفی برای equity_value یا value_per_share خطا نیست).

    Args:
        projections (List[CashFlowProjection]): پیش‌بینی سالانه اجزای FCFF؛
            سال = اندیس فهرست از ۱ تا n
        wacc_rate (float): نرخ تنزیل / WACC (اعشاری؛ مثبت)
        terminal_growth (float): نرخ رشد پایانی گوردون (اعشاری)
        shares_outstanding (float): تعداد سهام (مثبت)
        tax_rate (float): نرخ مالیات سراسری (اعشاری؛ ۰ ≤ t < ۱)
        cash (float): موجودی نقد (نامنفی)
        debt (float): بدهی بهره‌دار (نامنفی)
        minority_interest (float): منافع اقلیت (نامنفی)
        preferred_equity (float): سهام ممتاز (نامنفی)

    Returns:
        DcfBreakdown: ارزش بنگاه، ارزش حقوق صاحبان سهام و جدول سالانه

    Raises:
        ValidationError: در صورت ورودی نامعتبر یا FCFF پایانی غیرمثبت
        CalculationError: در صورت خطای محاسباتی
    """
    if not isinstance(projections, list):
        raise ValidationError("❌ حداقل یک سال پیش‌بینی جریان نقدی لازم است!")

    validate_projections_length(len(projections))

    _require_finite_number(wacc_rate, "نرخ WACC")
    _require_finite_number(terminal_growth, "نرخ رشد پایانی")
    _require_finite_number(shares_outstanding, "تعداد سهام")
    _require_finite_number(tax_rate, "نرخ مالیات")
    _require_finite_number(cash, "موجودی نقد")
    _require_finite_number(debt, "بدهی")
    _require_finite_number(minority_interest, "منافع اقلیت")
    _require_finite_number(preferred_equity, "سهام ممتاز")

    validate_positive_number(wacc_rate, "نرخ WACC")
    validate_positive_number(shares_outstanding, "تعداد سهام")
    validate_tax_rate(tax_rate)
    validate_non_negative(cash, "موجودی نقد")
    validate_non_negative(debt, "بدهی")
    validate_non_negative(minority_interest, "منافع اقلیت")
    validate_non_negative(preferred_equity, "سهام ممتاز")
    validate_terminal_growth_vs_wacc(terminal_growth, wacc_rate)

    try:
        years: List[FcffYearRow] = []
        for index, row in enumerate(projections, start=1):
            if not isinstance(row, CashFlowProjection):
                raise ValidationError("❌ هر سطر پیش‌بینی باید از نوع CashFlowProjection باشد!")

            fcff = calculate_fcff(
                row.ebit, tax_rate, row.depreciation, row.capex, row.delta_nwc
            )
            nopat = row.ebit * (1 - tax_rate)
            discount_factor = 1.0 / math.pow(1 + wacc_rate, index)
            present_value = fcff * discount_factor

            if not all(
                math.isfinite(value)
                for value in (nopat, discount_factor, present_value)
            ):
                raise CalculationError("نتیجه محاسبه نامعتبر است")

            years.append(
                FcffYearRow(
                    year=index,
                    ebit=row.ebit,
                    nopat=nopat,
                    depreciation=row.depreciation,
                    capex=row.capex,
                    delta_nwc=row.delta_nwc,
                    fcff=fcff,
                    discount_factor=discount_factor,
                    present_value=present_value,
                )
            )

        terminal_fcff = years[-1].fcff
        if terminal_fcff <= 0:
            raise ValidationError(
                "❌ جریان نقدی آزاد پایانی باید مثبت باشد؛ "
                "مدل رشد گوردون در غیر این صورت بی‌معناست!"
            )

        n = len(years)
        terminal_value = terminal_fcff * (1 + terminal_growth) / (wacc_rate - terminal_growth)
        pv_terminal_value = terminal_value / math.pow(1 + wacc_rate, n)
        pv_fcff_total = sum(row.present_value for row in years)
        enterprise_value = pv_fcff_total + pv_terminal_value
        equity_value = (
            enterprise_value + cash - debt - minority_interest - preferred_equity
        )
        value_per_share = equity_value / shares_outstanding
        terminal_value_share_percent = (
            (pv_terminal_value / enterprise_value) * 100
            if enterprise_value != 0
            else 0.0
        )

        if not all(
            math.isfinite(value)
            for value in (
                terminal_value,
                pv_terminal_value,
                pv_fcff_total,
                enterprise_value,
                equity_value,
                value_per_share,
                terminal_value_share_percent,
            )
        ):
            raise CalculationError("نتیجه محاسبه نامعتبر است")

        return DcfBreakdown(
            enterprise_value=enterprise_value,
            equity_value=equity_value,
            value_per_share=value_per_share,
            wacc=wacc_rate,
            terminal_growth=terminal_growth,
            terminal_value=terminal_value,
            pv_terminal_value=pv_terminal_value,
            pv_fcff_total=pv_fcff_total,
            cash=cash,
            debt=debt,
            minority_interest=minority_interest,
            preferred_equity=preferred_equity,
            shares_outstanding=shares_outstanding,
            terminal_value_share_percent=terminal_value_share_percent,
            years=years,
        )
    except (ZeroDivisionError, ValueError, OverflowError) as e:
        logger.error(f"خطا در محاسبه DCF: {e}")
        raise CalculationError(f"خطا در محاسبه: {str(e)}")


def dcf_scenario_valuation(
    scenarios: List[DcfScenario],
    shares_outstanding: float,
    tax_rate: float,
    cash: float = 0.0,
    debt: float = 0.0,
    minority_interest: float = 0.0,
    preferred_equity: float = 0.0,
    market_price: Optional[float] = None,
) -> ScenarioValuationResult:
    """ارزش‌گذاری سناریوهای DCF و آمار وزنی بدون تغییر احتمال‌ها یا ورودی‌ها.

    Args:
        scenarios: دو تا پنج سناریوی نام‌گذاری‌شده؛ مجموع احتمال‌ها برابر یک
        shares_outstanding: تعداد سهام مشترک؛ مثبت
        tax_rate: نرخ مالیات مشترک؛ اعشاری
        cash: موجودی نقد مشترک
        debt: بدهی بهره‌دار مشترک
        minority_interest: منافع اقلیت مشترک
        preferred_equity: سهام ممتاز مشترک
        market_price: قیمت بازار اختیاری؛ متناهی و مثبت

    Returns:
        ScenarioValuationResult: سطرها به ترتیب ورودی و آمار ارزش و ریسک

    Raises:
        ValidationError: ورودی نامعتبر؛ شکست یک سناریو کل درخواست را رد می‌کند
        CalculationError: خطای عددی؛ خطای سناریو نام آن را نیز دارد
    """
    if not isinstance(scenarios, list) or any(not isinstance(item, DcfScenario) for item in scenarios):
        raise ValidationError("❌ سناریوها باید فهرستی از DcfScenario باشند!")
    validate_scenario_set(
        [scenario.name for scenario in scenarios],
        [scenario.probability for scenario in scenarios],
    )
    if market_price is not None:
        _require_finite_number(market_price, "قیمت بازار")
        validate_positive_number(market_price, "قیمت بازار")

    try:
        rows: List[ScenarioRow] = []
        for scenario in scenarios:
            try:
                breakdown = dcf_valuation(
                    scenario.projections, scenario.wacc_rate, scenario.terminal_growth,
                    shares_outstanding, tax_rate, cash=cash, debt=debt,
                    minority_interest=minority_interest, preferred_equity=preferred_equity,
                )
            except (ValidationError, CalculationError) as exc:
                raise type(exc)(f"سناریو «{scenario.name}» — {exc}") from exc
            row = ScenarioRow(
                name=scenario.name, probability=scenario.probability,
                wacc=breakdown.wacc, terminal_growth=breakdown.terminal_growth,
                enterprise_value=breakdown.enterprise_value, equity_value=breakdown.equity_value,
                value_per_share=breakdown.value_per_share,
                terminal_value_share_percent=breakdown.terminal_value_share_percent,
                weighted_value_per_share=scenario.probability * breakdown.value_per_share,
                upside=None if market_price is None else breakdown.value_per_share / market_price - 1,
            )
            if not all(value is None or math.isfinite(value) for value in (
                row.probability, row.wacc, row.terminal_growth, row.enterprise_value,
                row.equity_value, row.value_per_share, row.terminal_value_share_percent,
                row.weighted_value_per_share, row.upside, row.probability_percent,
                row.wacc_percent, row.terminal_growth_percent, row.upside_percent,
            )):
                raise CalculationError("نتیجه محاسبه نامعتبر است")
            rows.append(row)

        expected = sum(row.weighted_value_per_share for row in rows)
        variance = sum(row.probability * (row.value_per_share - expected) ** 2 for row in rows)
        worst = min(rows, key=lambda row: row.value_per_share)
        best = max(rows, key=lambda row: row.value_per_share)
        result = ScenarioValuationResult(
            scenarios=rows, expected_value_per_share=expected,
            expected_enterprise_value=sum(row.probability * row.enterprise_value for row in rows),
            expected_equity_value=sum(row.probability * row.equity_value for row in rows),
            std_dev_value_per_share=math.sqrt(variance),
            min_value_per_share=worst.value_per_share, max_value_per_share=best.value_per_share,
            worst_scenario=worst.name, best_scenario=best.name, market_price=market_price,
            expected_upside=None if market_price is None else expected / market_price - 1,
            probability_of_upside=None if market_price is None else sum(
                row.probability for row in rows if row.value_per_share > market_price
            ),
        )
        if not all(value is None or math.isfinite(value) for value in (
            result.expected_value_per_share, result.expected_enterprise_value,
            result.expected_equity_value, result.std_dev_value_per_share,
            result.min_value_per_share, result.max_value_per_share, result.market_price,
            result.expected_upside, result.probability_of_upside,
            result.expected_upside_percent, result.probability_of_upside_percent,
        )):
            raise CalculationError("نتیجه محاسبه نامعتبر است")
        return result
    except (ZeroDivisionError, ValueError, OverflowError) as exc:
        raise CalculationError("نتیجه محاسبه نامعتبر است") from exc


def dcf_sensitivity(
    projections: List[CashFlowProjection],
    wacc_rate: float,
    terminal_growth: float,
    shares_outstanding: float,
    tax_rate: float,
    cash: float = 0.0,
    debt: float = 0.0,
    minority_interest: float = 0.0,
    preferred_equity: float = 0.0,
    wacc_step: float = DEFAULT_WACC_STEP,
    growth_step: float = DEFAULT_GROWTH_STEP,
    wacc_points: int = DEFAULT_SENSITIVITY_POINTS,
    growth_points: int = DEFAULT_SENSITIVITY_POINTS,
) -> DcfSensitivityResult:
    """
    ماتریس حساسیت ارزش DCF نسبت به WACC و نرخ رشد پایانی

    هر سلول با فراخوانی ``dcf_valuation`` برای همان ترکیب محاسبه می‌شود؛
    هیچ فرمول تنزیل یا ارزش انتهای دوره‌ای در این تابع تکرار نمی‌شود.
    سلولی که ``dcf_valuation`` آن را نامعتبر بداند (مثلاً WACC نامثبت یا
    نقض حداقل اختلاف) به‌جای شکست کل ماتریس، ``None`` می‌شود. محورها صعودی
    و مرکزچین روی حالت پایه‌اند؛ بنابراین سلول مرکزی دقیقاً همان نتیجه
    حالت پایه است.

    Args:
        projections (List[CashFlowProjection]): پیش‌بینی سالانه اجزای FCFF
        wacc_rate (float): WACC حالت پایه (اعشاری؛ مثبت)
        terminal_growth (float): نرخ رشد پایانی حالت پایه (اعشاری)
        shares_outstanding (float): تعداد سهام (مثبت)
        tax_rate (float): نرخ مالیات سراسری (اعشاری؛ ۰ ≤ t < ۱)
        cash (float): موجودی نقد (نامنفی)
        debt (float): بدهی بهره‌دار (نامنفی)
        minority_interest (float): منافع اقلیت (نامنفی)
        preferred_equity (float): سهام ممتاز (نامنفی)
        wacc_step (float): فاصله نقاط محور WACC (اعشاری؛ مثبت)
        growth_step (float): فاصله نقاط محور رشد پایانی (اعشاری؛ مثبت)
        wacc_points (int): تعداد نقاط محور WACC (فرد؛ ۳ تا ۱۱)
        growth_points (int): تعداد نقاط محور رشد پایانی (فرد؛ ۳ تا ۱۱)

    Returns:
        DcfSensitivityResult: محورها، ماتریس‌ها و اطلاعات حالت پایه

    Raises:
        ValidationError: در صورت نامعتبر بودن پارامترهای شبکه یا حالت پایه
        CalculationError: در صورت خطای محاسباتی در حالت پایه
    """
    validate_sensitivity_grid(wacc_step, growth_step, wacc_points, growth_points)

    # حالت پایه؛ خطای آن کل درخواست را نامعتبر می‌کند و باید بالا برود.
    base = dcf_valuation(
        projections,
        wacc_rate,
        terminal_growth,
        shares_outstanding,
        tax_rate,
        cash=cash,
        debt=debt,
        minority_interest=minority_interest,
        preferred_equity=preferred_equity,
    )

    base_row = wacc_points // 2
    base_col = growth_points // 2

    # round(..., 10) نویز ممیز شناور (مثل 0.09999999999) را حذف می‌کند.
    wacc_values = [
        round(wacc_rate + (index - base_row) * wacc_step, 10)
        for index in range(wacc_points)
    ]
    growth_values = [
        round(terminal_growth + (index - base_col) * growth_step, 10)
        for index in range(growth_points)
    ]

    value_per_share: List[List[Optional[float]]] = []
    enterprise_value: List[List[Optional[float]]] = []
    valid_cells = 0

    for row_index, wacc_value in enumerate(wacc_values):
        value_row: List[Optional[float]] = []
        enterprise_row: List[Optional[float]] = []
        for col_index, growth_value in enumerate(growth_values):
            if row_index == base_row and col_index == base_col:
                # سلول مرکزی عیناً نتیجه حالت پایه است.
                value_row.append(base.value_per_share)
                enterprise_row.append(base.enterprise_value)
                valid_cells += 1
                continue

            try:
                cell = dcf_valuation(
                    projections,
                    wacc_value,
                    growth_value,
                    shares_outstanding,
                    tax_rate,
                    cash=cash,
                    debt=debt,
                    minority_interest=minority_interest,
                    preferred_equity=preferred_equity,
                )
            except (ValidationError, CalculationError):
                # ترکیب نامعتبر فقط همان سلول را None می‌کند.
                value_row.append(None)
                enterprise_row.append(None)
                continue

            value_row.append(cell.value_per_share)
            enterprise_row.append(cell.enterprise_value)
            valid_cells += 1

        value_per_share.append(value_row)
        enterprise_value.append(enterprise_row)

    return DcfSensitivityResult(
        wacc_values=wacc_values,
        growth_values=growth_values,
        value_per_share=value_per_share,
        enterprise_value=enterprise_value,
        base_wacc=wacc_rate,
        base_terminal_growth=terminal_growth,
        base_row=base_row,
        base_col=base_col,
        base_value_per_share=base.value_per_share,
        base_enterprise_value=base.enterprise_value,
        valid_cells=valid_cells,
        total_cells=wacc_points * growth_points,
    )


def reverse_dcf_implied_growth(
    projections: List[CashFlowProjection],
    wacc_rate: float,
    shares_outstanding: float,
    tax_rate: float,
    market_price: float,
    cash: float = 0.0,
    debt: float = 0.0,
    minority_interest: float = 0.0,
    preferred_equity: float = 0.0,
    reference_terminal_growth: Optional[float] = None,
) -> ReverseDcfResult:
    """
    نرخ رشد پایانی تلویحی قیمت بازار با DCF معکوس

    ارزش هر سهم نسبت به نرخ رشد پایانی (با FCFF پایانی مثبت) اکیداً صعودی
    است؛ بنابراین رشد تلویحی با نصف‌سازی بازه ``[REVERSE_DCF_MIN_GROWTH,
    WACC − MIN_SPREAD]`` روی خروجی ``dcf_valuation`` پیدا می‌شود. اگر قیمت
    بازار بیرون این بازه باشد، پاسخ به‌جای خطا وضعیت ``market_price_below_range``
    یا ``market_price_above_range`` می‌گیرد.

    Args:
        projections (List[CashFlowProjection]): پیش‌بینی سالانه اجزای FCFF
        wacc_rate (float): نرخ تنزیل / WACC (اعشاری؛ مثبت)
        shares_outstanding (float): تعداد سهام (مثبت)
        tax_rate (float): نرخ مالیات سراسری (اعشاری؛ ۰ ≤ t < ۱)
        market_price (float): قیمت بازار سهام (مثبت)
        cash (float): موجودی نقد (نامنفی)
        debt (float): بدهی بهره‌دار (نامنفی)
        minority_interest (float): منافع اقلیت (نامنفی)
        preferred_equity (float): سهام ممتاز (نامنفی)
        reference_terminal_growth (Optional[float]): نرخ رشد پایانی تحلیل‌گر؛
            فقط برای محاسبه ``growth_gap`` و صرفاً از نظر متناهی‌بودن بررسی می‌شود

    Returns:
        ReverseDcfResult: رشد تلویحی، تفکیک ارزش در آن نرخ و وضعیت حل

    Raises:
        ValidationError: در صورت ورودی نامعتبر (از جمله FCFF پایانی غیرمثبت)
        CalculationError: در صورت شکست همگرایی جستجوی نصف‌سازی
    """
    _require_finite_number(market_price, "قیمت بازار")
    validate_positive_number(market_price, "قیمت بازار")
    if reference_terminal_growth is not None:
        _require_finite_number(reference_terminal_growth, "نرخ رشد پایانی مرجع")

    def value_at(growth_rate: float) -> DcfBreakdown:
        """ارزش‌گذاری DCF در یک نرخ رشد پایانی مشخص"""
        return dcf_valuation(
            projections,
            wacc_rate,
            growth_rate,
            shares_outstanding,
            tax_rate,
            cash=cash,
            debt=debt,
            minority_interest=minority_interest,
            preferred_equity=preferred_equity,
        )

    search_min_growth = REVERSE_DCF_MIN_GROWTH
    search_max_growth = wacc_rate - MIN_SPREAD

    # خطای ورودی در کرانه‌ها بالا می‌رود؛ فقط ترکیب‌های نامعتبر سلول نیستند.
    value_at_min = value_at(search_min_growth).value_per_share
    value_at_max = value_at(search_max_growth).value_per_share

    tolerance = 1e-9 * max(1.0, market_price)
    implied_growth: Optional[float] = None
    status = "solved"

    if abs(value_at_min - market_price) <= tolerance:
        implied_growth = search_min_growth
    elif abs(value_at_max - market_price) <= tolerance:
        implied_growth = search_max_growth
    elif value_at_min > market_price:
        status = "market_price_below_range"
    elif value_at_max < market_price:
        status = "market_price_above_range"
    else:
        low = search_min_growth
        high = search_max_growth
        for _ in range(200):
            middle = (low + high) / 2
            value = value_at(middle).value_per_share
            if abs(value - market_price) <= tolerance:
                implied_growth = middle
                break
            if value < market_price:
                low = middle
            else:
                high = middle
            if high - low < 1e-12:
                implied_growth = (low + high) / 2
                break
        if implied_growth is None:
            raise CalculationError(
                "❌ همگرایی جستجوی رشد تلویحی در DCF معکوس ممکن نشد!"
            )

    enterprise_value: Optional[float] = None
    equity_value: Optional[float] = None
    terminal_value_share_percent: Optional[float] = None
    if implied_growth is not None:
        breakdown = value_at(implied_growth)
        enterprise_value = breakdown.enterprise_value
        equity_value = breakdown.equity_value
        terminal_value_share_percent = breakdown.terminal_value_share_percent

    growth_gap: Optional[float] = None
    if implied_growth is not None and reference_terminal_growth is not None:
        growth_gap = implied_growth - reference_terminal_growth

    if status == "market_price_below_range":
        message = (
            f"قیمت بازار حتی از ارزش با کمترین نرخ رشد قابل جستجو "
            f"({search_min_growth * 100:.2f}%) هم کمتر است؛ "
            f"بازه جستجو: {search_min_growth * 100:.2f}% تا "
            f"{search_max_growth * 100:.2f}%"
        )
    elif status == "market_price_above_range":
        message = (
            f"قیمت بازار حتی از ارزش با بیشترین نرخ رشد مجاز "
            f"({search_max_growth * 100:.2f}%) هم بیشتر است؛ "
            f"بازه جستجو: {search_min_growth * 100:.2f}% تا "
            f"{search_max_growth * 100:.2f}%"
        )
    else:
        message = (
            f"بازار با این قیمت، رشد پایانی حدود {implied_growth * 100:.2f}% "
            f"را فرض کرده است"
        )

    return ReverseDcfResult(
        status=status,
        market_price=market_price,
        implied_growth=implied_growth,
        wacc=wacc_rate,
        search_min_growth=search_min_growth,
        search_max_growth=search_max_growth,
        value_per_share_at_min_growth=value_at_min,
        value_per_share_at_max_growth=value_at_max,
        enterprise_value=enterprise_value,
        equity_value=equity_value,
        terminal_value_share_percent=terminal_value_share_percent,
        reference_terminal_growth=reference_terminal_growth,
        growth_gap=growth_gap,
        message=message,
    )

