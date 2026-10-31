"""بهینه‌سازی میانگین–واریانس سبد: حداقل واریانس، مماس و مرز کارا.

ورودی‌ها همه سالانه و اعشاری‌اند: بردار بازده مورد انتظار و ماتریس کوواریانس.
هیچ بهینه‌ساز عددی یا تصادف در کار نیست و ترتیب همه حلقه‌ها ثابت است:

* با فروش استقراضی (``allow_short=True``): فرمول بسته. سبد حداقل واریانس
  ``w ∝ Σ⁻¹1``، سبد مماس ``w ∝ Σ⁻¹(μ − rf·1)`` و هر نقطه مرز کارا از دستگاه
  دو‌قیدی لاگرانژ (قضیه دو‌صندوق) با ``_linalg.solve``.
* فقط‌خرید (``allow_short=False``): شمارش دقیق تکیه‌گاه برای حداکثر
  ``MAX_LONG_ONLY_ASSETS`` دارایی. زیرمجموعه‌ها به ترتیب اندازه و سپس
  لغت‌نامه‌ای (خروجی ``itertools.combinations``) بررسی می‌شوند.

قرارداد خطا:
    ValidationError: ورودی نامعتبر یا مسئله تعریف‌نشده (مثلاً مماس بدون
        بازده مازاد مثبت)
    CalculationError: ماتریس منفرد، شکست حل، یا نتیجه نامتناهی
"""

import math
from dataclasses import dataclass
from itertools import combinations
from typing import Iterator, List, Optional, Sequence, Tuple

from ._linalg import dot, mat_vec, solve, submatrix
from .errors import CalculationError, ValidationError
from .validators import (
    DEFAULT_FRONTIER_POINTS,
    LONG_ONLY_WEIGHT_TOLERANCE,
    MAX_LONG_ONLY_ASSETS,
    RETURN_MATCH_TOLERANCE,
    VARIANCE_NEGATIVE_TOLERANCE,
    validate_covariance_matrix,
    validate_frontier_points,
    validate_mean_returns,
    validate_risk_free_rate,
    validate_weights,
)

_INVALID_RESULT = "نتیجه محاسبه نامعتبر است"


@dataclass(frozen=True)
class PortfolioPoint:
    """یک سبد با وزن‌ها و آماره‌های سالانه

    Attributes:
        weights: وزن هر دارایی به ترتیب ورودی؛ مجموع ۱
        expected_return: بازده مورد انتظار سالانه (اعشاری)
        variance: واریانس سالانه
        volatility: انحراف معیار سالانه
        sharpe_ratio: نسبت شارپ؛ بدون نرخ بدون ریسک ``None`` است
    """

    weights: List[float]
    expected_return: float
    variance: float
    volatility: float
    sharpe_ratio: Optional[float]

    @property
    def weights_percent(self) -> List[float]:
        """وزن‌ها به درصد"""
        return [weight * 100.0 for weight in self.weights]

    @property
    def expected_return_percent(self) -> float:
        """بازده مورد انتظار به درصد"""
        return self.expected_return * 100.0

    @property
    def volatility_percent(self) -> float:
        """نوسان به درصد"""
        return self.volatility * 100.0


def _require_finite(value: float) -> float:
    """مقدار نامتناهی یا NaN را به خطای محاسباتی تبدیل می‌کند."""
    if not math.isfinite(value):
        raise CalculationError(_INVALID_RESULT)
    return value


def _prepare(
    mean_returns: Sequence[float],
    covariance: Sequence[Sequence[float]],
    allow_short: bool,
) -> Tuple[List[float], List[List[float]]]:
    """اعتبارسنجی و کپی ورودی‌ها؛ کوواریانس برای دقت تقارن میانگین‌گیری می‌شود."""
    validate_mean_returns(mean_returns)
    validate_covariance_matrix(covariance)
    if len(mean_returns) != len(covariance):
        raise ValidationError("❌ تعداد بازده‌ها و ابعاد کوواریانس باید برابر باشد!")
    if not isinstance(allow_short, bool):
        raise ValidationError("❌ مجاز بودن فروش استقراضی باید بولی باشد!")
    count = len(mean_returns)
    if not allow_short and count > MAX_LONG_ONLY_ASSETS:
        raise ValidationError(
            f"❌ در حالت فقط‌خرید حداکثر {MAX_LONG_ONLY_ASSETS} دارایی مجاز است!"
        )
    means = [float(value) for value in mean_returns]
    cov = [
        [(float(covariance[i][j]) + float(covariance[j][i])) / 2.0 for j in range(count)]
        for i in range(count)
    ]
    return means, cov


def _performance(
    weights: Sequence[float], means: Sequence[float], cov: Sequence[Sequence[float]]
) -> Tuple[float, float, float]:
    """(بازده، واریانس، نوسان) برای ورودی‌های آماده‌شده؛ واریانس منفی کوچک بریده می‌شود."""
    expected = _require_finite(dot(weights, means))
    variance = _require_finite(dot(weights, mat_vec(cov, weights)))
    if variance < 0:
        if variance < -VARIANCE_NEGATIVE_TOLERANCE:
            raise CalculationError(_INVALID_RESULT)
        variance = 0.0
    return expected, variance, math.sqrt(variance)


def _build_point(
    weights: Sequence[float],
    means: Sequence[float],
    cov: Sequence[Sequence[float]],
    risk_free_rate: Optional[float],
) -> PortfolioPoint:
    """ساخت ``PortfolioPoint``؛ شارپ فقط با نرخ بدون ریسک و نوسان مثبت."""
    expected, variance, volatility = _performance(weights, means, cov)
    sharpe: Optional[float] = None
    if risk_free_rate is not None:
        if volatility <= 0:
            raise CalculationError(_INVALID_RESULT)
        sharpe = _require_finite((expected - risk_free_rate) / volatility)
    return PortfolioPoint([float(w) for w in weights], expected, variance, volatility, sharpe)


def portfolio_performance(
    weights: List[float], mean_returns: List[float], covariance: List[List[float]]
) -> Tuple[float, float]:
    """
    بازده و نوسان سالانه یک سبد

    Args:
        weights: وزن هر دارایی؛ متناهی و با مجموع ۱ (تلورانس ``WEIGHT_SUM_TOLERANCE``)
        mean_returns: بازده مورد انتظار سالانه اعشاری
        covariance: کوواریانس سالانه

    Returns:
        Tuple[float, float]: (بازده مورد انتظار، نوسان)

    Raises:
        ValidationError: اگر وزن‌ها، بازده‌ها یا کوواریانس نامعتبر باشند
        CalculationError: اگر نتیجه متناهی نباشد
    """
    means, cov = _prepare(mean_returns, covariance, True)
    validate_weights(weights, len(means))
    expected, _, volatility = _performance([float(w) for w in weights], means, cov)
    return expected, volatility


def portfolio_point(
    weights: List[float],
    mean_returns: List[float],
    covariance: List[List[float]],
    risk_free_rate: Optional[float] = None,
) -> PortfolioPoint:
    """
    ساخت ``PortfolioPoint`` برای وزن‌های دلخواه (مثلاً سبد هم‌وزن)

    Args:
        weights: وزن‌ها با مجموع ۱
        mean_returns: بازده مورد انتظار سالانه
        covariance: کوواریانس سالانه
        risk_free_rate: نرخ بدون ریسک اختیاری؛ بدون آن شارپ ``None`` است

    Returns:
        PortfolioPoint: آماره‌های سبد

    Raises:
        ValidationError: اگر ورودی نامعتبر باشد
        CalculationError: اگر نوسان صفر و شارپ تعریف‌نشده یا نتیجه نامتناهی باشد
    """
    if risk_free_rate is not None:
        validate_risk_free_rate(risk_free_rate)
    means, cov = _prepare(mean_returns, covariance, True)
    validate_weights(weights, len(means))
    return _build_point([float(w) for w in weights], means, cov, risk_free_rate)


def _supports(count: int) -> Iterator[Tuple[int, ...]]:
    """همه زیرمجموعه‌های ناتهی به ترتیب اندازه صعودی و سپس لغت‌نامه‌ای."""
    for size in range(1, count + 1):
        yield from combinations(range(count), size)


def _clip_long_only(weights: Sequence[float]) -> Optional[List[float]]:
    """وزن منفی کوچک را به صفر می‌برد و بازنرمال می‌کند؛ منفی بزرگ‌تر از تلورانس ← None."""
    if min(weights) < -LONG_ONLY_WEIGHT_TOLERANCE:
        return None
    clipped = [max(value, 0.0) for value in weights]
    total = sum(clipped)
    if total <= 0 or not math.isfinite(total):
        return None
    return [value / total for value in clipped]


def _kkt_weights(
    cov: Sequence[Sequence[float]], rows: Sequence[Sequence[float]], rhs: Sequence[float]
) -> List[float]:
    """حل ``min wᵀΣw`` با قیدهای ``rows·w = rhs`` از دستگاه KKT؛ فقط وزن‌ها برمی‌گردند."""
    size = len(cov)
    extra = len(rows)
    system = [[0.0] * (size + extra) for _ in range(size + extra)]
    for i in range(size):
        for j in range(size):
            system[i][j] = cov[i][j]
        for k in range(extra):
            system[i][size + k] = rows[k][i]
            system[size + k][i] = rows[k][i]
    return solve(system, [0.0] * size + list(rhs))[:size]


def _long_only_min_variance(
    means: Sequence[float], cov: Sequence[Sequence[float]], target: Optional[float]
) -> List[float]:
    """کمینه واریانس فقط‌خرید با شمارش دقیق تکیه‌گاه؛ ``target=None`` یعنی سبد حداقل واریانس.

    Raises:
        CalculationError: اگر هیچ تکیه‌گاه شدنی‌ای پیدا نشود
    """
    count = len(means)
    best: Optional[List[float]] = None
    best_variance = math.inf
    for support in _supports(count):
        sub_cov = submatrix(cov, list(support))
        sub_means = [means[i] for i in support]
        ones = [1.0] * len(support)
        rows: List[List[float]] = [ones]
        rhs = [1.0]
        if target is not None:
            if max(sub_means) - min(sub_means) <= RETURN_MATCH_TOLERANCE:
                # بازده تکیه‌گاه ثابت است: قید بازده یا خودبه‌خود برقرار است یا
                # شدنی نیست؛ در هر دو حالت قید دوم افزونه (و دستگاه منفرد) است.
                if abs(sub_means[0] - target) > RETURN_MATCH_TOLERANCE:
                    continue
            else:
                rows = [ones, sub_means]
                rhs = [1.0, target]
        try:
            weights = _clip_long_only(_kkt_weights(sub_cov, rows, rhs))
        except CalculationError:
            continue
        if weights is None:
            continue
        variance = dot(weights, mat_vec(sub_cov, weights))
        if variance < best_variance:  # مقایسه اکید: تساوی ← زیرمجموعه اول
            best_variance = variance
            best = [0.0] * count
            for position, asset in enumerate(support):
                best[asset] = weights[position]
    if best is None:
        raise CalculationError(_INVALID_RESULT)
    return best


def _gmv_weights(
    means: Sequence[float], cov: Sequence[Sequence[float]], allow_short: bool
) -> List[float]:
    """وزن‌های سبد حداقل واریانس."""
    if not allow_short:
        return _long_only_min_variance(means, cov, None)
    solution = solve(cov, [1.0] * len(cov))
    total = sum(solution)
    if total <= 0:
        raise CalculationError(_INVALID_RESULT)
    return [_require_finite(value / total) for value in solution]


def min_variance_portfolio(
    mean_returns: List[float], covariance: List[List[float]], allow_short: bool
) -> PortfolioPoint:
    """
    سبد با کمترین واریانس (GMV)

    با فروش استقراضی ``w = Σ⁻¹1 / (1ᵀΣ⁻¹1)``؛ کوواریانس منفرد
    (مثلاً همبستگی کامل) ``CalculationError`` می‌دهد. در حالت فقط‌خرید
    شمارش دقیق تکیه‌گاه انجام می‌شود (توضیح در ``tangency_portfolio``)؛
    تکیه‌گاه‌های منفرد کنار گذاشته می‌شوند.

    Args:
        mean_returns: بازده مورد انتظار سالانه
        covariance: کوواریانس سالانه
        allow_short: آیا وزن منفی مجاز است؟

    Returns:
        PortfolioPoint: سبد GMV؛ شارپ ``None`` است

    Raises:
        ValidationError: ورودی نامعتبر یا بیش از ``MAX_LONG_ONLY_ASSETS`` دارایی فقط‌خرید
        CalculationError: کوواریانس منفرد یا نتیجه نامتناهی
    """
    means, cov = _prepare(mean_returns, covariance, allow_short)
    return _build_point(_gmv_weights(means, cov, allow_short), means, cov, None)


def tangency_portfolio(
    mean_returns: List[float],
    covariance: List[List[float]],
    risk_free_rate: float,
    allow_short: bool,
) -> PortfolioPoint:
    """
    سبد مماس (بیشینه نسبت شارپ)

    با فروش استقراضی ``w ∝ Σ⁻¹(μ − rf·1)``؛ اگر ``1ᵀΣ⁻¹(μ − rf·1) ≤ 0``
    باشد (نرخ بدون ریسک کمتر از بازده سبد حداقل واریانس نیست) سبد مماس
    تعریف نمی‌شود و ``ValidationError`` رخ می‌دهد.

    فقط‌خرید: برای هر زیرمجموعه ناتهی S (به ترتیب ثابت) جواب بدون قید
    روی S یعنی ``w ∝ Σ_S⁻¹(μ_S − rf)`` با مجموع مثبت محاسبه می‌شود و اگر همه
    وزن‌ها ≥ ‎−1e-12 باشند کاندیدا می‌شود. این روش دقیق است چون مسئله
    محدب است: بهینه فقط‌خرید با تکیه‌گاه S* در شرایط KKT صدق می‌کند و
    بر S* برابر جواب بدون قید روی همان تکیه‌گاه است؛ پس بین کاندیداها
    هست و کاندیدای دیگری هم سبد شدنی است و از بهینه بهتر نمی‌شود. تساوی
    به زیرمجموعه اول می‌رسد. زیرمجموعه‌های منفرد کنار می‌روند.

    Args:
        mean_returns: بازده مورد انتظار سالانه
        covariance: کوواریانس سالانه
        risk_free_rate: نرخ بدون ریسک؛ متناهی و نامنفی
        allow_short: آیا وزن منفی مجاز است؟

    Returns:
        PortfolioPoint: سبد مماس با شارپ

    Raises:
        ValidationError: ورودی نامعتبر، بازده مازاد مثبت وجود ندارد، یا نرخ
            بدون ریسک کمتر از بازده GMV نیست (فروش مجاز)
        CalculationError: کوواریانس منفرد یا هیچ تکیه‌گاهی شدنی نیست
    """
    validate_risk_free_rate(risk_free_rate)
    means, cov = _prepare(mean_returns, covariance, allow_short)
    rate = float(risk_free_rate)
    excess = [value - rate for value in means]
    if allow_short:
        solution = solve(cov, excess)
        total = sum(solution)
        if total <= 0:
            raise ValidationError(
                "❌ نرخ بدون ریسک کمتر از بازده سبد حداقل واریانس نیست؛ "
                "سبد مماس تعریف نمی‌شود!"
            )
        weights = [_require_finite(value / total) for value in solution]
        return _build_point(weights, means, cov, rate)

    if max(excess) <= 0:
        raise ValidationError(
            "❌ هیچ دارایی بازده بالاتر از نرخ بدون ریسک ندارد؛ سبد مماس تعریف نمی‌شود!"
        )
    best: Optional[List[float]] = None
    best_sharpe = -math.inf
    for support in _supports(len(means)):
        sub_cov = submatrix(cov, list(support))
        sub_excess = [excess[i] for i in support]
        try:
            solution = solve(sub_cov, sub_excess)
        except CalculationError:
            continue
        total = sum(solution)
        if total <= 0:
            continue
        weights = _clip_long_only([value / total for value in solution])
        if weights is None:
            continue
        variance = dot(weights, mat_vec(sub_cov, weights))
        if variance <= 0:
            continue
        sharpe = dot(weights, sub_excess) / math.sqrt(variance)
        if sharpe > best_sharpe:  # مقایسه اکید: تساوی ← زیرمجموعه اول
            best_sharpe = sharpe
            best = [0.0] * len(means)
            for position, asset in enumerate(support):
                best[asset] = weights[position]
    if best is None:
        raise CalculationError(_INVALID_RESULT)
    return _build_point(best, means, cov, rate)


def _frontier_weights(
    means: Sequence[float], cov: Sequence[Sequence[float]], allow_short: bool, target: float
) -> List[float]:
    """کمینه واریانس برای بازده هدف؛ شکست حل خطای محاسباتی است (نقطه هرگز حذف نمی‌شود)."""
    if allow_short:
        return _kkt_weights(cov, [[1.0] * len(means), list(means)], [1.0, target])
    return _long_only_min_variance(means, cov, target)


def efficient_frontier(
    mean_returns: List[float],
    covariance: List[List[float]],
    allow_short: bool,
    points: int = DEFAULT_FRONTIER_POINTS,
) -> List[PortfolioPoint]:
    """
    مرز کارا از سبد حداقل واریانس تا بیشترین بازده یک دارایی

    بازده هدف نقطه k برابر ``r_min + k·(r_max − r_min)/(points − 1)`` است که
    ``r_min`` بازده سبد GMV و ``r_max`` بیشترین بازده تک‌دارایی است. نقطه
    اول دقیقاً همان سبد GMV و هدف نقطه آخر دقیقاً ``r_max`` است. بازده
    هدف‌ها بر ``[r_min, r_max]`` می‌افتند، پس شدنی‌اند؛ اگر حل یک هدف شکست
    بخورد ``CalculationError`` می‌دهیم. با فروش استقراضی هر هدف یک دستگاه
    دو‌قیدی (مجموع و بازده) است؛ فقط‌خرید شمارش دقیق تکیه‌گاه با همان قیدها.
    اگر ``r_max ≤ r_min`` (در حد ``RETURN_MATCH_TOLERANCE``) مرز بازه‌ای ندارد
    و ``ValidationError`` رخ می‌دهد؛ با فروش استقراضی بازده GMV می‌تواند
    از همه بازده‌های تک‌دارایی بیشتر شود.

    Args:
        mean_returns: بازده مورد انتظار سالانه
        covariance: کوواریانس سالانه
        allow_short: آیا وزن منفی مجاز است؟
        points: تعداد نقاط؛ ``MIN_FRONTIER_POINTS`` تا ``MAX_FRONTIER_POINTS``

    Returns:
        List[PortfolioPoint]: ``points`` سبد با بازده صعودی؛ شارپ ``None``

    Raises:
        ValidationError: ورودی نامعتبر یا مرز بدون بازه
        CalculationError: کوواریانس منفرد یا شکست حل یک نقطه
    """
    validate_frontier_points(points)
    means, cov = _prepare(mean_returns, covariance, allow_short)
    gmv = _build_point(_gmv_weights(means, cov, allow_short), means, cov, None)
    low, high = gmv.expected_return, max(means)
    if high - low <= RETURN_MATCH_TOLERANCE:
        raise ValidationError(
            "❌ بازده سبد حداقل واریانس کمتر از بیشترین بازده دارایی‌ها نیست؛ "
            "مرز کارا بازه‌ای برای ترسیم ندارد!"
        )
    frontier = [gmv]
    for index in range(1, points):
        target = high if index == points - 1 else low + (high - low) * index / (points - 1)
        weights = _frontier_weights(means, cov, allow_short, target)
        frontier.append(_build_point(weights, means, cov, None))
    return frontier
