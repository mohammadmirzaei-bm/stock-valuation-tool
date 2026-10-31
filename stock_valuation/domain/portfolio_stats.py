"""آماره نمونه‌ای بازده دارایی‌ها، پیش از بهینه‌سازی سبد.

هر فهرست داخلی سری زمانی یک دارایی است و اندیس زمانی بین دارایی‌ها هم‌تراز
فرض می‌شود. این ماژول تاریخ نمی‌شناسد و نام دارایی نمی‌گیرد.

سال‌سازی حسابی است، نه مرکب‌کردن:
    میانگین سالانه = میانگین حسابی بازده دوره × تعداد دوره‌ها در سال
    کوواریانس سالانه = کوواریانس نمونه‌ای (تقسیم بر n − ddof) × همان تعداد
    نوسان سالانه = جذر واریانس سالانه
همبستگی به این مقیاس حساس نیست، چون ضریب دوره‌ها در صورت و مخرج حذف می‌شود.
این با رشد مرکب سالانه یکی نیست.

سری با واریانس نمونه‌ای صفر (سری ثابت) رد می‌شود، چون همبستگی تعریف‌نشده
است. واریانس منفی عددی خطای محاسباتی است. همبستگی کامل (±۱) با واریانس
مثبت مجاز است؛ منفرد شدن کوواریانس در آن حالت به لایه بهینه‌سازی واگذار
می‌شود.

قرارداد خطا:
    ValidationError: ورودی نامعتبر، از جمله واریانس صفر
    CalculationError: نتیجه غیرعددی یا نامتناهی
"""

import math
from dataclasses import dataclass
from typing import List, Sequence

from .errors import CalculationError, ValidationError
from .validators import (
    CORRELATION_TOLERANCE,
    MIN_OBSERVATIONS,
    SAMPLE_COVARIANCE_DDOF,
    validate_asset_count,
    validate_periods_per_year,
)

_INVALID_RESULT = "نتیجه محاسبه نامعتبر است"
# حداقل بازده = حداقل قیمت منهای یک، و باید از درجه آزادی کوواریانس بزرگ‌تر باشد.
_MIN_RETURN_OBSERVATIONS = MIN_OBSERVATIONS - SAMPLE_COVARIANCE_DDOF


@dataclass(frozen=True)
class SampleStatistics:
    """آماره‌های سالانه نمونه‌ای یک پنجره بازده هم‌تراز

    Attributes:
        mean_returns: میانگین حسابی سالانه هر دارایی (اعشاری)
        covariance: کوواریانس نمونه‌ای سالانه؛ متقارن و با قطر مثبت
        volatilities: انحراف معیار سالانه، جذر قطر کوواریانس
        correlation: همبستگی نمونه‌ای؛ قطر دقیقاً ۱ و قدر مطلق برون‌قطر حداکثر ۱
        observations: تعداد بازده‌های هر دارایی (نه تعداد قیمت)
    """

    mean_returns: List[float]
    covariance: List[List[float]]
    volatilities: List[float]
    correlation: List[List[float]]
    observations: int

    @property
    def mean_returns_percent(self) -> List[float]:
        """میانگین بازده سالانه به درصد"""
        return [value * 100.0 for value in self.mean_returns]

    @property
    def volatilities_percent(self) -> List[float]:
        """نوسان سالانه به درصد"""
        return [value * 100.0 for value in self.volatilities]


def _finite_number(value: float, field_name: str) -> float:
    """عدد متناهی (نه bool) را برمی‌گرداند."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError(f"❌ {field_name} باید عدد باشد!")
    if not math.isfinite(value):
        raise ValidationError(f"❌ {field_name} باید عدد متناهی باشد!")
    return float(value)


def _require_finite_result(value: float) -> float:
    """نتیجه نامتناهی یا NaN را به خطای محاسباتی تبدیل می‌کند."""
    if not math.isfinite(value):
        raise CalculationError(_INVALID_RESULT)
    return value


def _copy_series(
    values: Sequence[Sequence[float]],
    field_name: str,
    min_length: int,
    positive: bool,
) -> List[List[float]]:
    """کپی سری‌های هم‌طول. ورودی تغییر نمی‌کند."""
    if not isinstance(values, (list, tuple)) or len(values) == 0:
        raise ValidationError(f"❌ {field_name} باید ماتریس غیرخالی باشد!")
    validate_asset_count(len(values))
    copied: List[List[float]] = []
    length = -1
    for index, series in enumerate(values):
        label = f"{field_name} دارایی {index + 1}"
        if not isinstance(series, (list, tuple)):
            raise ValidationError(f"❌ سری {label} باید فهرست باشد!")
        if length < 0:
            length = len(series)
            if length < min_length:
                raise ValidationError(
                    f"❌ هر دارایی حداقل به {min_length} مشاهده {field_name} نیاز دارد!"
                )
        elif len(series) != length:
            raise ValidationError(f"❌ طول سری {field_name} دارایی‌ها باید برابر باشد!")
        row: List[float] = []
        for observation, value in enumerate(series):
            number = _finite_number(value, f"{label} در مشاهده {observation + 1}")
            if positive and number <= 0:
                raise ValidationError(f"❌ {label} باید مثبت باشد!")
            row.append(number)
        copied.append(row)
    return copied


def returns_from_prices(prices: Sequence[Sequence[float]]) -> List[List[float]]:
    """
    بازده ساده هر دارایی از سری قیمت

    برای هر دارایی و هر زمان t > 0، بازده برابر ``p_t / p_{t-1} - 1`` است.
    قیمت‌ها باید متناهی و مثبت و سری‌ها هم‌طول باشند. حداقل
    ``MIN_OBSERVATIONS`` قیمت لازم است تا دست‌کم دو بازده ساخته شود.
    بازده صفر (قیمت ثابت) اینجا مجاز است؛ رد شدن واریانس صفر در
    ``sample_statistics`` انجام می‌شود. چون قیمت‌ها مثبت‌اند، بازده ساده
    از −۱ بزرگ‌تر است.

    Args:
        prices: سری قیمت هر دارایی؛ فهرست بیرونی دارایی و فهرست داخلی زمان است

    Returns:
        List[List[float]]: بازده ساده، یک مشاهده کوتاه‌تر از قیمت، همان ترتیب دارایی‌ها

    Raises:
        ValidationError: اگر تعداد دارایی، طول سری‌ها یا قیمت‌ها نامعتبر باشد
        CalculationError: اگر بازده محاسبه‌شده متناهی نباشد
    """
    series = _copy_series(prices, "قیمت", MIN_OBSERVATIONS, positive=True)
    returns: List[List[float]] = []
    for asset in series:
        row: List[float] = []
        for previous, current in zip(asset, asset[1:]):
            row.append(_require_finite_result(current / previous - 1.0))
        returns.append(row)
    return returns


def sample_statistics(
    returns: Sequence[Sequence[float]],
    periods_per_year: int,
) -> SampleStatistics:
    """
    میانگین، کوواریانس، نوسان و همبستگی نمونه‌ای سالانه

    میانگین حسابی دوره در ``periods_per_year`` ضرب می‌شود و کوواریانس
    نمونه‌ای (مخرج ``n - SAMPLE_COVARIANCE_DDOF``) هم با همان ضریب سال
    می‌شود. این مقیاس خطی است و مرکب‌کردن بازده نیست. نوسان جذر واریانس
    سالانه است. همبستگی از روی کوواریانس سالانه ساخته می‌شود و با ضریب
    سال‌سازی عوض نمی‌شود.

    اگر واریانس نمونه‌ای یک دارایی صفر باشد ValidationError رخ می‌دهد
    (سری ثابت؛ همبستگی تعریف‌نشده). واریانس منفی یا نامتناهی
    CalculationError است. همبستگی کامل با واریانس مثبت پذیرفته می‌شود.
    اگر خطای شناور همبستگی را کمی بیرون از [−۱، ۱] ببرد ولی در محدوده
    ``CORRELATION_TOLERANCE`` باشد، به نزدیک‌ترین کران بریده می‌شود؛
    فراتر از تلورانس خطای محاسباتی است. ماتریس کوواریانس با یک بار محاسبه
    هر زوج و نوشتن هر دو مثلث ساخته می‌شود تا دقیقاً متقارن بماند.

    Args:
        returns: بازده دوره هر دارایی؛ هم‌طول و حداقل ``MIN_OBSERVATIONS - 1`` مشاهده
        periods_per_year: عدد صحیح ۱ تا ۳۶۶

    Returns:
        SampleStatistics: آماره‌های سالانه و تعداد بازده‌ها

    Raises:
        ValidationError: اگر ورودی یا واریانس نمونه‌ای نامعتبر باشد
        CalculationError: اگر آماره سالانه متناهی نباشد یا همبستگی از تلورانس خارج شود
    """
    if _MIN_RETURN_OBSERVATIONS <= SAMPLE_COVARIANCE_DDOF:
        raise CalculationError(_INVALID_RESULT)
    validate_periods_per_year(periods_per_year)
    series = _copy_series(
        returns, "بازده", _MIN_RETURN_OBSERVATIONS, positive=False
    )
    asset_count = len(series)
    observations = len(series[0])
    denominator = observations - SAMPLE_COVARIANCE_DDOF
    scale = float(periods_per_year)

    means = [sum(row) / observations for row in series]
    sample_covariance = [[0.0] * asset_count for _ in range(asset_count)]
    for row_index in range(asset_count):
        for column_index in range(row_index, asset_count):
            total = 0.0
            for time in range(observations):
                total += (
                    (series[row_index][time] - means[row_index])
                    * (series[column_index][time] - means[column_index])
                )
            value = _require_finite_result(total / denominator)
            sample_covariance[row_index][column_index] = value
            sample_covariance[column_index][row_index] = value
            if row_index == column_index:
                if value < 0:
                    raise CalculationError(_INVALID_RESULT)
                if value == 0:
                    raise ValidationError(
                        "❌ واریانس نمونه‌ای هر دارایی باید مثبت باشد؛ "
                        "سری ثابت پذیرفته نمی‌شود!"
                    )

    annual_means = [
        _require_finite_result(mean * scale) for mean in means
    ]
    annual_covariance = [
        [_require_finite_result(value * scale) for value in row]
        for row in sample_covariance
    ]
    volatilities = [
        _require_finite_result(math.sqrt(annual_covariance[index][index]))
        for index in range(asset_count)
    ]
    correlation = _correlation(annual_covariance)
    result = SampleStatistics(
        mean_returns=annual_means,
        covariance=annual_covariance,
        volatilities=volatilities,
        correlation=correlation,
        observations=observations,
    )
    return result


def _correlation(covariance: Sequence[Sequence[float]]) -> List[List[float]]:
    """همبستگی از کوواریانس با قطر مثبت؛ برون‌قطر کمی بیرون از [−۱، ۱] بریده می‌شود."""
    size = len(covariance)
    scales = [math.sqrt(covariance[index][index]) for index in range(size)]
    correlation = [[0.0] * size for _ in range(size)]
    for row_index in range(size):
        correlation[row_index][row_index] = 1.0
        for column_index in range(row_index + 1, size):
            value = covariance[row_index][column_index] / (
                scales[row_index] * scales[column_index]
            )
            value = _require_finite_result(value)
            if abs(value) > 1.0 + CORRELATION_TOLERANCE:
                raise CalculationError(_INVALID_RESULT)
            if value > 1.0:
                value = 1.0
            elif value < -1.0:
                value = -1.0
            correlation[row_index][column_index] = value
            correlation[column_index][row_index] = value
    return correlation
