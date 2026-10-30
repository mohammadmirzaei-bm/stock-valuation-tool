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
from typing import List, NamedTuple, Tuple

from .errors import CalculationError, ValidationError
from .validators import (
    validate_growth_rate_vs_return,
    validate_non_negative,
    validate_percentage,
    validate_positive_number,
    validate_projections_length,
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

