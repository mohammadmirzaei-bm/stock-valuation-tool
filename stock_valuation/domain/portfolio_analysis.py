"""تحلیل سبد: دارایی‌ها، مرز کارا، خط تخصیص سرمایه و سبد کامل.

این ماژول فقط توابع ``domain.portfolio`` را صدا می‌زند و فرمول بهینه‌سازی را
تکرار نمی‌کند. آماره نمونه‌ای را هم حساب نمی‌کند؛ بازده و کوواریانس سالانه
باید از قبل آماده باشند. آن دو ماژول این ماژول را import نمی‌کنند.

سبد کامل: ``y* = (E[Rp] − rf) / (A · σp²)`` روی سبد مماس، سپس برش به
``[0, max_leverage]``. چون سبد مماس فقط وقتی ساخته می‌شود که بازده مازادش
مثبت باشد، ``y*`` در مسیر موفق همیشه مثبت است و پرچم ``clipped_to_zero``
در ``analyze_portfolio`` روشن نمی‌شود. شاخه دفاعی برش به صفر هست و جدا
آزموده می‌شود.

خط تخصیص سرمایه دو نقطه کمکی دارد: ``(بازده = rf، نوسان = ۰)`` و نقطه‌ای در
``CAL_VOLATILITY_MULTIPLIER`` برابرِ نوسان سبد مماس. با مضرب ۲، سبد مماس
دقیقاً وسط این پاره‌خط است.

قرارداد خطا:
    ValidationError: ورودی نامعتبر، از جمله شکست تعریف سبد مماس
    CalculationError: نتیجه نامتناهی
"""

import math
from dataclasses import dataclass
from typing import List, Sequence

from .errors import CalculationError, ValidationError
from .portfolio import (
    PortfolioPoint,
    efficient_frontier,
    min_variance_portfolio,
    portfolio_point,
    tangency_portfolio,
)
from .validators import (
    CAL_VOLATILITY_MULTIPLIER,
    DEFAULT_FRONTIER_POINTS,
    DEFAULT_MAX_LEVERAGE,
    validate_asset_names,
    validate_max_leverage,
    validate_risk_aversion,
)

_INVALID_RESULT = "نتیجه محاسبه نامعتبر است"


@dataclass(frozen=True)
class AssetPoint:
    """یک دارایی برای نمودار پراکندگی بازده–نوسان

    Attributes:
        name: نام دارایی پس از حذف فاصله‌های ابتدا و انتها
        expected_return: بازده مورد انتظار سالانه (اعشاری)
        volatility: انحراف معیار سالانه (جذر واریانس همان دارایی)
    """

    name: str
    expected_return: float
    volatility: float

    @property
    def expected_return_percent(self) -> float:
        """بازده مورد انتظار به درصد"""
        return self.expected_return * 100.0

    @property
    def volatility_percent(self) -> float:
        """نوسان به درصد"""
        return self.volatility * 100.0


@dataclass(frozen=True)
class AllocationPoint:
    """یک نقطه روی خط تخصیص سرمایه

    Attributes:
        expected_return: بازده مورد انتظار (اعشاری)
        volatility: نوسان
    """

    expected_return: float
    volatility: float

    @property
    def expected_return_percent(self) -> float:
        """بازده مورد انتظار به درصد"""
        return self.expected_return * 100.0

    @property
    def volatility_percent(self) -> float:
        """نوسان به درصد"""
        return self.volatility * 100.0


@dataclass(frozen=True)
class CapitalAllocationLine:
    """خط تخصیص سرمایه از نرخ بدون ریسک با شیب شارپ سبد مماس

    Attributes:
        risk_free_rate: عرض از مبدأ (اعشاری)
        slope: شیب، برابر نسبت شارپ سبد مماس
        points: دو نقطه کمکی؛ اولی در نوسان صفر و دومی در مضرب نام‌گذاری‌شده
            از نوسان سبد مماس
    """

    risk_free_rate: float
    slope: float
    points: List[AllocationPoint]

    @property
    def risk_free_rate_percent(self) -> float:
        """نرخ بدون ریسک به درصد"""
        return self.risk_free_rate * 100.0


@dataclass(frozen=True)
class CompletePortfolio:
    """سبد کامل: ترکیب سبد مماس و دارایی بدون ریسک

    Attributes:
        risk_aversion: ضریب ریسک‌گریزی A
        tangency_weight: وزن سبد مماس پس از برش، همان y*
        risk_free_weight: وزن دارایی بدون ریسک، برابر ``1 − y*``
        risky_weights: وزن هر دارایی ریسک‌دار، برابر ``y*`` در وزن مماس
        expected_return: بازده سبد کامل
        volatility: نوسان سبد کامل
        leverage_capped: آیا y* به سقف اهرم بریده شده است؟
        clipped_to_zero: آیا y* به‌خاطر بازده مازاد نامثبت به صفر بریده شده است؟
    """

    risk_aversion: float
    tangency_weight: float
    risk_free_weight: float
    risky_weights: List[float]
    expected_return: float
    volatility: float
    leverage_capped: bool
    clipped_to_zero: bool

    @property
    def tangency_weight_percent(self) -> float:
        """وزن سبد مماس به درصد"""
        return self.tangency_weight * 100.0

    @property
    def risk_free_weight_percent(self) -> float:
        """وزن دارایی بدون ریسک به درصد"""
        return self.risk_free_weight * 100.0

    @property
    def risky_weights_percent(self) -> List[float]:
        """وزن دارایی‌های ریسک‌دار به درصد"""
        return [weight * 100.0 for weight in self.risky_weights]

    @property
    def expected_return_percent(self) -> float:
        """بازده سبد کامل به درصد"""
        return self.expected_return * 100.0

    @property
    def volatility_percent(self) -> float:
        """نوسان سبد کامل به درصد"""
        return self.volatility * 100.0


@dataclass(frozen=True)
class PortfolioAnalysis:
    """خروجی تحلیل سبد

    Attributes:
        assets: دارایی‌ها به ترتیب ورودی، برای نمودار پراکندگی
        min_variance: سبد حداقل واریانس؛ شارپ آن ``None`` است
        tangency: سبد مماس
        frontier: مرز کارا؛ شارپ نقاط آن ``None`` است
        equal_weight: سبد معیار با وزن برابر، همراه با شارپ
        capital_allocation_line: خط تخصیص سرمایه
        complete_portfolio: سبد کامل پس از برش اهرم
    """

    assets: List[AssetPoint]
    min_variance: PortfolioPoint
    tangency: PortfolioPoint
    frontier: List[PortfolioPoint]
    equal_weight: PortfolioPoint
    capital_allocation_line: CapitalAllocationLine
    complete_portfolio: CompletePortfolio


def _finite(value: float) -> float:
    """نتیجه نامتناهی را به خطای محاسباتی تبدیل می‌کند."""
    if not math.isfinite(value):
        raise CalculationError(_INVALID_RESULT)
    return value


def _complete_portfolio(
    tangency: PortfolioPoint,
    risk_free_rate: float,
    risk_aversion: float,
    max_leverage: float,
) -> CompletePortfolio:
    """y* سبد مماس را حساب و به ``[0, max_leverage]`` برش می‌کند.

    اگر بازده مازاد نامثبت باشد y* صفر و ``clipped_to_zero`` روشن می‌شود.
    ``analyze_portfolio`` به این شاخه نمی‌رسد، چون سبد مماس در آن صورت اصلاً
    ساخته نمی‌شود. واریانس نامثبت با بازده مازاد مثبت خطای محاسباتی است.
    """
    excess = tangency.expected_return - risk_free_rate
    variance = tangency.variance
    clipped_to_zero = False
    leverage_capped = False
    if excess <= 0:
        weight = 0.0
        clipped_to_zero = True
    elif variance <= 0:
        raise CalculationError(_INVALID_RESULT)
    else:
        weight = _finite(excess / (risk_aversion * variance))
        if weight < 0:
            weight = 0.0
            clipped_to_zero = True
        elif weight > max_leverage:
            weight = float(max_leverage)
            leverage_capped = True
    risky = [_finite(weight * value) for value in tangency.weights]
    return CompletePortfolio(
        risk_aversion=float(risk_aversion),
        tangency_weight=weight,
        risk_free_weight=_finite(1.0 - weight),
        risky_weights=risky,
        expected_return=_finite(risk_free_rate + weight * excess),
        volatility=_finite(weight * tangency.volatility),
        leverage_capped=leverage_capped,
        clipped_to_zero=clipped_to_zero,
    )


def _allocation_line(tangency: PortfolioPoint, risk_free_rate: float) -> CapitalAllocationLine:
    """دو نقطه کمکی خط تخصیص سرمایه."""
    if tangency.sharpe_ratio is None:
        raise CalculationError(_INVALID_RESULT)
    slope = _finite(tangency.sharpe_ratio)
    end_volatility = _finite(CAL_VOLATILITY_MULTIPLIER * tangency.volatility)
    end_return = _finite(risk_free_rate + slope * end_volatility)
    return CapitalAllocationLine(
        risk_free_rate=float(risk_free_rate),
        slope=slope,
        points=[
            AllocationPoint(float(risk_free_rate), 0.0),
            AllocationPoint(end_return, end_volatility),
        ],
    )


def _assets(
    names: Sequence[str],
    mean_returns: Sequence[float],
    covariance: Sequence[Sequence[float]],
) -> List[AssetPoint]:
    """نقاط پراکندگی؛ قطر کوواریانس پس از اعتبارسنجی خوانده می‌شود."""
    assets: List[AssetPoint] = []
    for index, name in enumerate(names):
        variance = covariance[index][index]
        if isinstance(variance, bool) or not isinstance(variance, (int, float)):
            raise ValidationError("❌ واریانس دارایی باید عدد باشد!")
        if variance < 0:
            raise CalculationError(_INVALID_RESULT)
        volatility = _finite(math.sqrt(variance)) if variance > 0 else 0.0
        assets.append(
            AssetPoint(name, _finite(float(mean_returns[index])), volatility)
        )
    return assets


def analyze_portfolio(
    asset_names: Sequence[str],
    mean_returns: Sequence[float],
    covariance: Sequence[Sequence[float]],
    risk_free_rate: float,
    risk_aversion: float,
    allow_short: bool = False,
    max_leverage: float = DEFAULT_MAX_LEVERAGE,
    frontier_points: int = DEFAULT_FRONTIER_POINTS,
) -> PortfolioAnalysis:
    """
    تحلیل کامل سبد از بازده و کوواریانس سالانه

    نام‌ها باید غیرخالی، یکتا و هم‌تعداد با بازده‌ها باشند. سبد مماس، سبد
    حداقل واریانس و مرز کارا از ``domain.portfolio`` می‌آیند. سبد معیار
    وزن ``1/n`` دارد. ``y* = (E[Rp] − rf) / (A · σp²)`` و برای داده مرجع
    گام قبل با ``A = 3`` دقیقاً ``2.8125 / 3 = 0.9375`` است، چون
    ``(E[Rp] − rf) / σp²`` همان ``1ᵀΣ⁻¹(μ − rf)`` است.

    Args:
        asset_names: نام دارایی‌ها به ترتیب بردار بازده
        mean_returns: بازده مورد انتظار سالانه (اعشاری)
        covariance: کوواریانس سالانه
        risk_free_rate: نرخ بدون ریسک؛ متناهی و نامنفی
        risk_aversion: ریسک‌گریزی A؛ متناهی و مثبت
        allow_short: فروش استقراضی؛ پیش‌فرض فقط‌خرید
        max_leverage: سقف y*؛ پیش‌فرض ۱ و حداکثر ۳
        frontier_points: تعداد نقاط مرز کارا؛ پیش‌فرض ۵۰

    Returns:
        PortfolioAnalysis: دارایی‌ها، سبدها، خط تخصیص و سبد کامل

    Raises:
        ValidationError: نام، ابعاد، ریسک‌گریزی، اهرم یا تعریف‌نشدن سبد مماس
        CalculationError: نتیجه نامتناهی، از جمله سرریز y*
    """
    validate_asset_names(asset_names)
    if not isinstance(mean_returns, (list, tuple)) or len(asset_names) != len(mean_returns):
        raise ValidationError("❌ تعداد نام‌ها و بازده‌ها باید برابر باشد!")
    validate_risk_aversion(risk_aversion)
    validate_max_leverage(max_leverage)
    names = [name.strip() for name in asset_names]
    count = len(names)
    equal_weights = [1.0 / count] * count

    minimum = min_variance_portfolio(mean_returns, covariance, allow_short)
    tangency = tangency_portfolio(
        mean_returns, covariance, risk_free_rate, allow_short
    )
    frontier = efficient_frontier(
        mean_returns, covariance, allow_short, frontier_points
    )
    equal_weight = portfolio_point(
        equal_weights, mean_returns, covariance, risk_free_rate
    )
    return PortfolioAnalysis(
        assets=_assets(names, mean_returns, covariance),
        min_variance=minimum,
        tangency=tangency,
        frontier=frontier,
        equal_weight=equal_weight,
        capital_allocation_line=_allocation_line(tangency, risk_free_rate),
        complete_portfolio=_complete_portfolio(
            tangency, risk_free_rate, risk_aversion, max_leverage
        ),
    )
