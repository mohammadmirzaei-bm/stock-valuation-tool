"""اعتبارسنجی ورودی‌های مدل‌های ارزیابی سهام.

توابع این ماژول خالص (pure) و قطعی هستند، وضعیت سراسری یا نشست برنامه را
تغییر نمی‌دهند و هیچ وابستگی‌ای به Streamlit ندارند.
"""

import math
from typing import List

from .errors import ValidationError

# حداقل اختلاف مجاز بین نرخ بازده و نرخ رشد (۰.۵ درصد)
MIN_SPREAD = 0.005

# حداکثر تعداد سال‌های پیش‌بینی صریح در مدل DCF
MAX_PROJECTIONS = 50

# گام‌های پیش‌فرض محورهای ماتریس حساسیت DCF (WACC × رشد پایانی)
DEFAULT_WACC_STEP = 0.01
DEFAULT_GROWTH_STEP = 0.005

# تعداد پیش‌فرض و بازه مجاز نقاط هر محور ماتریس حساسیت؛ فرد است تا
# حالت پایه دقیقاً در سلول مرکزی قرار بگیرد.
DEFAULT_SENSITIVITY_POINTS = 5
MIN_SENSITIVITY_POINTS = 3
MAX_SENSITIVITY_POINTS = 11

MIN_SCENARIOS = 2
MAX_SCENARIOS = 5
PROBABILITY_SUM_TOLERANCE = 1e-6
RETENTION_CURVE_STEP = 0.1

# تلورانس شناور فقط برای اعتبارسنج برچسب‌دار WACC؛ رفتار گوردون را تغییر نمی‌دهد
_WACC_SPREAD_TOLERANCE = 1e-12


def validate_positive_number(value: float, field_name: str) -> None:
    """
    اعتبارسنجی اعداد مثبت

    Args:
        value (float): مقدار ورودی
        field_name (str): نام فیلد برای نمایش خطا

    Raises:
        ValidationError: اگر مقدار منفی یا صفر باشد
    """
    if value <= 0:
        raise ValidationError(f"❌ {field_name} باید مثبت باشد!")


def validate_non_negative(value: float, field_name: str) -> None:
    """
    اعتبارسنجی اعداد نامنفی (صفر مجاز است)

    Args:
        value (float): مقدار ورودی
        field_name (str): نام فیلد برای نمایش خطا

    Raises:
        ValidationError: اگر مقدار منفی باشد
    """
    if value < 0:
        raise ValidationError(f"❌ {field_name} باید نامنفی باشد!")


def validate_tax_rate(tax_rate: float) -> None:
    """
    اعتبارسنجی نرخ مالیات: ۰ ≤ t < ۱

    Args:
        tax_rate (float): نرخ مالیات (اعشاری)

    Raises:
        ValidationError: اگر نرخ خارج از بازه باشد
    """
    if not 0 <= tax_rate < 1:
        raise ValidationError("❌ نرخ مالیات باید بین 0 و 1 (غیرشامل) باشد!")


def validate_percentage(value: float, field_name: str) -> None:
    """
    اعتبارسنجی درصدها (بین 0 و 1)

    Args:
        value (float): مقدار درصد (اعشاری)
        field_name (str): نام فیلد

    Raises:
        ValidationError: اگر مقدار خارج از بازه معقول باشد
    """
    if not 0 <= value <= 2:  # حداکثر 200% رشد
        raise ValidationError(f"❌ {field_name} باید بین 0 و 2 باشد!")


def validate_growth_rate_vs_return(growth_rate: float, return_rate: float) -> None:
    """
    اعتبارسنجی نرخ رشد در مقایسه با نرخ بازده

    Args:
        growth_rate (float): نرخ رشد
        return_rate (float): نرخ بازده

    Raises:
        ValidationError: اگر نرخ رشد بیشتر یا خیلی نزدیک به نرخ بازده باشد
    """
    if growth_rate >= return_rate:
        raise ValidationError(f"❌ نرخ بازده ({return_rate*100:.1f}%) باید بیشتر از نرخ رشد ({growth_rate*100:.1f}%) باشد!")

    if return_rate - growth_rate < MIN_SPREAD:
        raise ValidationError(
            f"❌ اختلاف نرخ بازده ({return_rate*100:.2f}%) و نرخ رشد ({growth_rate*100:.2f}%) "
            f"باید حداقل {MIN_SPREAD*100:.1f}% باشد تا مدل معتبر بماند!"
        )


def validate_terminal_growth_vs_wacc(terminal_growth: float, wacc_rate: float) -> None:
    """
    اعتبارسنجی نرخ رشد پایانی در مقایسه با WACC (پیام فارسی برچسب‌دار).

    همان قاعدهٔ ``MIN_SPREAD`` مدل گوردون را به کار می‌برد، با تلورانس شناور
    بسیار کوچک تا اختلاف‌هایی که از نظر ریاضی برابر ``MIN_SPREAD`` هستند
    (مثل ۰٫۰۹ − ۰٫۰۸۵) به‌خاطر خطای ممیز شناور رد نشوند. رفتار
    ``validate_growth_rate_vs_return`` دست‌نخورده می‌ماند.

    Args:
        terminal_growth (float): نرخ رشد پایانی (اعشاری)
        wacc_rate (float): نرخ میانگین موزون هزینه سرمایه (اعشاری)

    Raises:
        ValidationError: اگر رشد پایانی بیشتر یا خیلی نزدیک به WACC باشد
    """
    if terminal_growth >= wacc_rate:
        raise ValidationError(
            f"❌ نرخ WACC ({wacc_rate*100:.1f}%) باید بیشتر از "
            f"نرخ رشد پایانی ({terminal_growth*100:.1f}%) باشد!"
        )

    if wacc_rate - terminal_growth < MIN_SPREAD - _WACC_SPREAD_TOLERANCE:
        raise ValidationError(
            f"❌ اختلاف نرخ WACC ({wacc_rate*100:.2f}%) و نرخ رشد پایانی "
            f"({terminal_growth*100:.2f}%) باید حداقل {MIN_SPREAD*100:.1f}% باشد "
            f"تا مدل معتبر بماند!"
        )


def validate_projections_length(count: int) -> None:
    """
    اعتبارسنجی تعداد سال‌های پیش‌بینی جریان نقدی (۱ تا ``MAX_PROJECTIONS``)

    Args:
        count (int): تعداد سطرهای پیش‌بینی

    Raises:
        ValidationError: اگر تعداد خارج از بازه مجاز باشد
    """
    if count < 1:
        raise ValidationError("❌ حداقل یک سال پیش‌بینی جریان نقدی لازم است!")
    if count > MAX_PROJECTIONS:
        raise ValidationError(
            f"❌ تعداد سال‌های پیش‌بینی نباید بیشتر از {MAX_PROJECTIONS} باشد!"
        )


def validate_sensitivity_grid(wacc_step: float, growth_step: float,
                              wacc_points: int, growth_points: int) -> None:
    """
    اعتبارسنجی پارامترهای شبکه ماتریس حساسیت DCF (WACC × رشد پایانی)

    گام‌ها باید متناهی و مثبت باشند؛ تعداد نقاط هر محور باید عدد صحیح، فرد
    (تا حالت پایه دقیقاً در سلول مرکزی قرار گیرد) و بین
    ``MIN_SENSITIVITY_POINTS`` و ``MAX_SENSITIVITY_POINTS`` باشد.

    Args:
        wacc_step (float): فاصله نقاط محور WACC (اعشاری)
        growth_step (float): فاصله نقاط محور رشد پایانی (اعشاری)
        wacc_points (int): تعداد نقاط محور WACC
        growth_points (int): تعداد نقاط محور رشد پایانی

    Raises:
        ValidationError: اگر هر یک از پارامترهای شبکه نامعتبر باشد
    """
    for step, field_name in (
        (wacc_step, "گام نرخ WACC"),
        (growth_step, "گام نرخ رشد پایانی"),
    ):
        if not math.isfinite(step):
            raise ValidationError(f"❌ {field_name} باید عدد متناهی باشد!")
        if step <= 0:
            raise ValidationError(f"❌ {field_name} باید مثبت باشد!")

    for points, field_name in (
        (wacc_points, "تعداد نقاط محور WACC"),
        (growth_points, "تعداد نقاط محور رشد پایانی"),
    ):
        if isinstance(points, bool) or not isinstance(points, int):
            raise ValidationError(f"❌ {field_name} باید عدد صحیح باشد!")
        if points % 2 == 0:
            raise ValidationError(
                f"❌ {field_name} باید فرد باشد تا حالت پایه در مرکز قرار گیرد!"
            )
        if not MIN_SENSITIVITY_POINTS <= points <= MAX_SENSITIVITY_POINTS:
            raise ValidationError(
                f"❌ {field_name} باید بین {MIN_SENSITIVITY_POINTS} و "
                f"{MAX_SENSITIVITY_POINTS} باشد!"
            )


def validate_scenario_set(names: List[str], probabilities: List[float]) -> None:
    """اعتبارسنجی تعداد، نام‌ها و احتمال سناریوها بدون نرمال‌سازی."""
    if not MIN_SCENARIOS <= len(names) <= MAX_SCENARIOS:
        raise ValidationError(
            f"❌ تعداد سناریوها باید بین {MIN_SCENARIOS} و {MAX_SCENARIOS} باشد!"
        )
    if len(names) != len(probabilities):
        raise ValidationError("❌ تعداد نام‌ها و احتمال سناریوها باید برابر باشد!")
    if any(not isinstance(name, str) or not name.strip() for name in names):
        raise ValidationError("❌ نام سناریو باید غیرخالی باشد!")
    if len({name.strip() for name in names}) != len(names):
        raise ValidationError("❌ نام سناریوها باید یکتا باشد!")
    for probability in probabilities:
        if not math.isfinite(probability) or not 0 <= probability <= 1:
            raise ValidationError("❌ احتمال هر سناریو باید متناهی و بین 0 و 1 باشد!")
    total = sum(probabilities)
    if abs(total - 1.0) > PROBABILITY_SUM_TOLERANCE:
        raise ValidationError(f"❌ مجموع احتمال سناریوها ({total}) باید برابر 1 باشد!")


def validate_retention_ratio(b: float) -> None:
    """نسبت نگهداری سود باید متناهی و در بازهٔ ۰ ≤ b < ۱ باشد."""
    if not math.isfinite(b) or not 0 <= b < 1:
        raise ValidationError("❌ نسبت نگهداری سود باید متناهی و بین 0 و 1 (غیرشامل) باشد!")


def require_finite_number(value: float, field_name: str) -> None:
    """ورودی باید عدد متناهی باشد؛ در غیر این صورت ValidationError."""
    if not math.isfinite(value):
        raise ValidationError(f"❌ {field_name} باید عدد متناهی باشد!")
