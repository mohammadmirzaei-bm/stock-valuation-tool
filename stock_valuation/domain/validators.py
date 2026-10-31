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

# کرانه‌های نرخ رشد درآمد در پیش‌بینی مبتنی بر محرک‌ها (اعشاری)
MIN_REVENUE_GROWTH = -1.0  # انحصاری: رشد ≤ −۱۰۰٪ درآمد سال بعد را منفی می‌کند
MAX_REVENUE_GROWTH = 2.0  # حداکثر ۲۰۰٪ رشد سالانه؛ همان سقف validate_percentage

# حداکثر نسبت‌های درصدی محرک‌های پیش‌بینی (نسبت به درآمد یا درآمد افزایشی)
MAX_FORECAST_PERCENT = 1.0  # حداکثر ۱۰۰٪ از درآمد

# حداقل تعداد همتایان معتبر با ضریب مثبت برای گزارش آماره‌های ارزش‌گذاری نسبی
MIN_PEERS = 3

# بازه مجاز تعداد ردیف‌های خلاصه زمین فوتبال
MIN_FOOTBALL_RANGES = 1
MAX_FOOTBALL_RANGES = 12

# تلورانس شناور فقط برای اعتبارسنج برچسب‌دار WACC؛ رفتار گوردون را تغییر نمی‌دهد
_WACC_SPREAD_TOLERANCE = 1e-12

# حداقل قدر مطلق محور مجاز در حذف گاوسی با محورگیری جزئی.
# محوری که قدر مطلقش از این مقدار کمتر باشد، ماتریس را منفرد یا بدشرط می‌کند
# و حل دستگاه رد می‌شود. مقدار مطلق است (نسبت به مقیاس ماتریس نرمال نمی‌شود).
LINEAR_PIVOT_TOLERANCE = 1e-12

# تعداد دارایی‌های یک سبد
MIN_ASSETS = 2
MAX_ASSETS = 30
# سقف شمارش دقیق تکیه‌گاه وقتی فروش استقراضی مجاز نیست
MAX_LONG_ONLY_ASSETS = 8

# حداقل تعداد مشاهده قیمت برای هر دارایی. بازده ساده یکی کمتر است و
# کوواریانس نمونه‌ای با ddof زیر حداقل به دو بازده نیاز دارد.
MIN_OBSERVATIONS = 3
SAMPLE_COVARIANCE_DDOF = 1

# تعداد دوره‌ها در سال برای سال‌سازی خطی (روزانه، با سال کبیسه، تا ۳۶۶)
MIN_PERIODS_PER_YEAR = 1
MAX_PERIODS_PER_YEAR = 366

# تلورانس مطلق تقارن کوواریانس و عبور همبستگی از ۱.
# هیچ‌کدام نسبت به مقیاس ماتریس نرمال نمی‌شوند.
COVARIANCE_SYMMETRY_TOLERANCE = 1e-8
CORRELATION_TOLERANCE = 1e-8

# بازه مجاز تعداد نقاط مرز کارا و مقدار پیش‌فرض آن
MIN_FRONTIER_POINTS = 5
MAX_FRONTIER_POINTS = 200
DEFAULT_FRONTIER_POINTS = 50

# کران حداکثر اهرم سبد کامل (y*) و مقدار پیش‌فرض پارامتر
MIN_LEVERAGE = 0.0
MAX_LEVERAGE = 3.0
DEFAULT_MAX_LEVERAGE = 1.0

# نقطه دوم خط تخصیص سرمایه در این مضرب از نوسان سبد مماس قرار می‌گیرد
# (مضرب ۲ یعنی سبد مماس دقیقاً وسط دو نقطه کمکی است).
CAL_VOLATILITY_MULTIPLIER = 2.0

# تلورانس مطلق مجموع وزن‌ها در ورودی سبد (|Σw − 1| ≤ مقدار)
WEIGHT_SUM_TOLERANCE = 1e-6
# کمترین وزن منفی که در حالت فقط‌خرید خطای گرد کردن حساب و به صفر بریده می‌شود
LONG_ONLY_WEIGHT_TOLERANCE = 1e-12
# تلورانس مطلق برابری بازده‌ها: هدف مرز کارا با بازده تکیه‌گاه، و فشردگی بازه مرز
RETURN_MATCH_TOLERANCE = 1e-9
# واریانس منفی‌تر از این مقدار خطای محاسباتی است؛ منفی کوچک‌تر به صفر بریده می‌شود
VARIANCE_NEGATIVE_TOLERANCE = 1e-12


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


def validate_forecast_years(years: int) -> None:
    """
    اعتبارسنجی تعداد سال‌های پیش‌بینی مبتنی بر محرک‌ها (۱ تا MAX_PROJECTIONS)

    Args:
        years (int): تعداد سال‌ها؛ باید عدد صحیح باشد (bool رد می‌شود)

    Raises:
        ValidationError: اگر عدد صحیح نباشد یا خارج از بازه مجاز باشد
    """
    if isinstance(years, bool) or not isinstance(years, int):
        raise ValidationError("❌ تعداد سال‌های پیش‌بینی باید عدد صحیح باشد!")
    validate_projections_length(years)


def validate_forecast_growth(value: float, field_name: str) -> None:
    """
    اعتبارسنجی نرخ رشد محرک‌های پیش‌بینی: متناهی و بیشتر از −۱۰۰٪

    کرانه پایین انحصاری است (رشد ≤ −۱۰۰٪ درآمد سال بعد را صفر یا منفی
    می‌کند) و کرانه بالا ``MAX_REVENUE_GROWTH`` (۲۰۰٪) است؛ همان سقف
    مجاز درصدها در ``validate_percentage``.

    Args:
        value (float): نرخ رشد (اعشاری)
        field_name (str): نام فیلد

    Raises:
        ValidationError: اگر نامتناهی یا خارج از بازه باشد
    """
    if not math.isfinite(value):
        raise ValidationError(f"❌ {field_name} باید عدد متناهی باشد!")
    if not MIN_REVENUE_GROWTH < value <= MAX_REVENUE_GROWTH:
        raise ValidationError(
            f"❌ {field_name} باید بیشتر از {MIN_REVENUE_GROWTH} "
            f"و حداکثر {MAX_REVENUE_GROWTH} باشد!"
        )


def validate_forecast_percent(value: float, field_name: str) -> None:
    """
    اعتبارسنجی نسبت‌های درصدی محرک‌های پیش‌بینی: متناهی و ۰ تا ۱۰۰٪

    حاشیه سود عملیاتی و نسبت‌های استهلاک، Capex و NWC نسبت به درآمد فرض
    می‌شوند نامنفی و حداکثر برابر کل درآمد (۱۰۰٪) باشند.

    Args:
        value (float): نسبت درصدی (اعشاری)
        field_name (str): نام فیلد

    Raises:
        ValidationError: اگر نامتناهی یا خارج از بازه ۰ تا ۱ باشد
    """
    if not math.isfinite(value):
        raise ValidationError(f"❌ {field_name} باید عدد متناهی باشد!")
    if not 0 <= value <= MAX_FORECAST_PERCENT:
        raise ValidationError(
            f"❌ {field_name} باید بین 0 و {MAX_FORECAST_PERCENT} باشد!"
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


def validate_peer_count(count: int) -> None:
    """
    اعتبارسنجی تعداد همتایان معتبر با ضریب مثبت

    ضریب‌های غیرمثبت (مثل P/E شرکت زیان‌ده) از آماره‌ها کنار گذاشته
    می‌شوند؛ اگر پس از حذف کمتر از ``MIN_PEERS`` همتا بماند، آماره‌ها
    معنادار نیستند.

    Args:
        count (int): تعداد همتایان معتبر باقی‌مانده

    Raises:
        ValidationError: اگر تعداد کمتر از ``MIN_PEERS`` باشد
    """
    if count < MIN_PEERS:
        raise ValidationError(
            f"❌ حداقل {MIN_PEERS} همتای معتبر با ضریب مثبت لازم است!"
        )


def validate_valuation_metric(value: float, field_name: str) -> None:
    """
    اعتبارسنجی شاخص هدف ضریب‌های نسبی: عدد متناهی و مثبت

    ضریب‌های قیمت/سود، قیمت/فروش و EV/EBITDA برای شاخص غیرمثبت (مثل سود
    خالص منفی) معنای اقتصادی ندارند.

    Args:
        value (float): شاخص هدف (سود خالص، حقوق صاحبان سهام، درآمد، ...)
        field_name (str): نام فیلد برای نمایش خطا

    Raises:
        ValidationError: اگر مقدار عدد نباشد، نامتناهی باشد یا مثبت نباشد
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError(f"❌ {field_name} باید عدد باشد!")
    if not math.isfinite(value):
        raise ValidationError(f"❌ {field_name} باید عدد متناهی باشد!")
    if value <= 0:
        raise ValidationError(
            f"❌ {field_name} باید مثبت باشد؛ ضریب‌ها برای مقدار غیرمثبت معنا ندارند!"
        )


def validate_football_range_set(
    names: List[str],
    lows: List[float],
    mids: List[float],
    highs: List[float],
) -> None:
    """
    اعتبارسنجی مجموعه بازه‌های خلاصه زمین فوتبال

    تعداد بین ``MIN_FOOTBALL_RANGES`` و ``MAX_FOOTBALL_RANGES`` است؛ نام
    روش‌ها پس از حذف فاصله‌های ابتدا و انتها غیرخالی و یکتا هستند و هر
    بازه کرانه‌های متناهی با ``low ≤ mid ≤ high`` دارد. مقادیر منفی مجازند.

    Args:
        names (List[str]): نام روش ارزیابی هر بازه
        lows (List[float]): کرانه پایین هر بازه
        mids (List[float]): مقدار میانی هر بازه
        highs (List[float]): کرانه بالای هر بازه

    Raises:
        ValidationError: اگر تعداد، نام‌ها یا کرانه‌های بازه‌ها نامعتبر باشند
    """
    if not MIN_FOOTBALL_RANGES <= len(names) <= MAX_FOOTBALL_RANGES:
        raise ValidationError(
            f"❌ تعداد بازه‌ها باید بین {MIN_FOOTBALL_RANGES} و "
            f"{MAX_FOOTBALL_RANGES} باشد!"
        )
    if len(names) != len(lows) or len(names) != len(mids) or len(names) != len(highs):
        raise ValidationError("❌ تعداد نام‌ها و کرانه‌های بازه‌ها باید برابر باشد!")
    if any(not isinstance(name, str) or not name.strip() for name in names):
        raise ValidationError("❌ نام روش ارزیابی باید غیرخالی باشد!")
    if len({name.strip() for name in names}) != len(names):
        raise ValidationError("❌ نام روش‌های ارزیابی باید یکتا باشد!")

    for index, name in enumerate(names):
        label = name.strip()
        for value, field_name in (
            (lows[index], "کرانه پایین"),
            (mids[index], "مقدار میانی"),
            (highs[index], "کرانه بالا"),
        ):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValidationError(f"❌ {field_name} بازه «{label}» باید عدد باشد!")
            if not math.isfinite(value):
                raise ValidationError(
                    f"❌ {field_name} بازه «{label}» باید عدد متناهی باشد!"
                )
        if not lows[index] <= mids[index] <= highs[index]:
            raise ValidationError(
                f"❌ در بازه «{label}» باید کرانه پایین ≤ مقدار میانی ≤ "
                f"کرانه بالا باشد!"
            )


def validate_asset_count(count: int) -> None:
    """
    اعتبارسنجی تعداد دارایی‌های سبد

    Args:
        count (int): تعداد دارایی‌ها؛ bool پذیرفته نمی‌شود

    Raises:
        ValidationError: اگر عدد صحیح نباشد یا خارج از بازه مجاز باشد
    """
    if isinstance(count, bool) or not isinstance(count, int):
        raise ValidationError("❌ تعداد دارایی‌ها باید عدد صحیح باشد!")
    if not MIN_ASSETS <= count <= MAX_ASSETS:
        raise ValidationError(
            f"❌ تعداد دارایی‌ها باید بین {MIN_ASSETS} و {MAX_ASSETS} باشد!"
        )


def validate_asset_names(names: List[str]) -> None:
    """
    اعتبارسنجی نام دارایی‌ها: غیرخالی و یکتا

    تعداد نام‌ها همان تعداد دارایی‌هاست. یکتایی پس از حذف فاصله‌های ابتدا
    و انتها سنجیده می‌شود. این تابع نام‌ها را تغییر نمی‌دهد.

    Args:
        names (List[str]): نام دارایی‌ها به ترتیب ستون‌های بازده و کوواریانس

    Raises:
        ValidationError: اگر تعداد، نوع، خالی بودن یا تکرار نام‌ها نامعتبر باشد
    """
    if not isinstance(names, (list, tuple)):
        raise ValidationError("❌ نام دارایی‌ها باید فهرست باشد!")
    validate_asset_count(len(names))
    if any(not isinstance(name, str) or not name.strip() for name in names):
        raise ValidationError("❌ نام دارایی باید غیرخالی باشد!")
    if len({name.strip() for name in names}) != len(names):
        raise ValidationError("❌ نام دارایی‌ها باید یکتا باشد!")


def validate_periods_per_year(periods_per_year: int) -> None:
    """
    اعتبارسنجی تعداد دوره‌ها در سال برای سال‌سازی خطی آماره‌ها

    مقدار باید عدد صحیح (نه bool و نه اعشاری) در بازه ۱ تا ۳۶۶ باشد.

    Args:
        periods_per_year (int): تعداد دوره‌های بازده در یک سال

    Raises:
        ValidationError: اگر نوع یا مقدار خارج از بازه باشد
    """
    if isinstance(periods_per_year, bool) or not isinstance(periods_per_year, int):
        raise ValidationError("❌ تعداد دوره‌ها در سال باید عدد صحیح باشد!")
    if not MIN_PERIODS_PER_YEAR <= periods_per_year <= MAX_PERIODS_PER_YEAR:
        raise ValidationError(
            f"❌ تعداد دوره‌ها در سال باید بین {MIN_PERIODS_PER_YEAR} و "
            f"{MAX_PERIODS_PER_YEAR} باشد!"
        )


def validate_covariance_matrix(covariance: List[List[float]]) -> None:
    """
    اعتبارسنجی ماتریس کوواریانس مربعی

    درایه‌ها باید عدد متناهی باشند. قدر مطلق اختلاف هر زوج برون‌قطری از
    ``COVARIANCE_SYMMETRY_TOLERANCE`` (مطلق، بدون نرمال‌سازی نسبت به مقیاس)
    بیشتر نباشد. قطر باید نامنفی باشد. اگر قطری صفر باشد، کوواریانس همان
    سطر و ستون هم باید در محدوده همان تلورانس صفر باشد. اگر هر دو واریانس
    مثبت باشند، قدر مطلق همبستگی ضمنی نباید از ``1 + CORRELATION_TOLERANCE``
    بیشتر شود. ورودی تغییر نمی‌کند.

    Args:
        covariance (List[List[float]]): ماتریس کوواریانس به ترتیب دارایی‌ها

    Raises:
        ValidationError: اگر شکل، تقارن، قطر یا همبستگی ضمنی نامعتبر باشد
    """
    if not isinstance(covariance, (list, tuple)) or len(covariance) == 0:
        raise ValidationError("❌ ماتریس کوواریانس باید غیرخالی باشد!")
    size = len(covariance)
    validate_asset_count(size)
    rows: List[List[float]] = []
    for row_index, row in enumerate(covariance):
        if not isinstance(row, (list, tuple)) or len(row) != size:
            raise ValidationError("❌ ماتریس کوواریانس باید مربعی باشد!")
        copied: List[float] = []
        for column_index, value in enumerate(row):
            label = f"درایه ({row_index}, {column_index}) کوواریانس"
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValidationError(f"❌ {label} باید عدد باشد!")
            if not math.isfinite(value):
                raise ValidationError(f"❌ {label} باید عدد متناهی باشد!")
            copied.append(float(value))
        rows.append(copied)

    for row_index in range(size):
        if rows[row_index][row_index] < 0:
            raise ValidationError("❌ واریانس (قطر کوواریانس) باید نامنفی باشد!")
        for column_index in range(row_index + 1, size):
            left = rows[row_index][column_index]
            right = rows[column_index][row_index]
            if abs(left - right) > COVARIANCE_SYMMETRY_TOLERANCE:
                raise ValidationError("❌ ماتریس کوواریانس باید متقارن باشد!")
            pair = (left + right) / 2.0
            variance_left = rows[row_index][row_index]
            variance_right = rows[column_index][column_index]
            if variance_left > 0 and variance_right > 0:
                correlation = pair / math.sqrt(variance_left * variance_right)
                if (not math.isfinite(correlation)
                        or abs(correlation) > 1.0 + CORRELATION_TOLERANCE):
                    raise ValidationError(
                        "❌ قدر مطلق همبستگی ضمنی باید حداکثر 1 باشد!"
                    )
            elif abs(pair) > COVARIANCE_SYMMETRY_TOLERANCE:
                raise ValidationError(
                    "❌ با واریانس صفر، کوواریانس برون‌قطری باید صفر باشد!"
                )


def validate_mean_returns(mean_returns: List[float]) -> None:
    """
    اعتبارسنجی بردار بازده مورد انتظار دارایی‌ها

    Args:
        mean_returns (List[float]): بازده سالانه اعشاری هر دارایی؛ منفی مجاز است

    Raises:
        ValidationError: اگر تعداد، نوع یا متناهی بودن مقادیر نامعتبر باشد
    """
    if not isinstance(mean_returns, (list, tuple)):
        raise ValidationError("❌ بازده‌های مورد انتظار باید فهرست باشند!")
    validate_asset_count(len(mean_returns))
    for index, value in enumerate(mean_returns):
        label = f"بازده مورد انتظار دارایی {index + 1}"
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValidationError(f"❌ {label} باید عدد باشد!")
        if not math.isfinite(value):
            raise ValidationError(f"❌ {label} باید عدد متناهی باشد!")


def validate_risk_free_rate(risk_free_rate: float) -> None:
    """
    اعتبارسنجی نرخ بدون ریسک: عدد متناهی و نامنفی (اعشاری)

    Args:
        risk_free_rate (float): نرخ بدون ریسک سالانه

    Raises:
        ValidationError: اگر عدد متناهی نباشد یا منفی باشد
    """
    if isinstance(risk_free_rate, bool) or not isinstance(risk_free_rate, (int, float)):
        raise ValidationError("❌ نرخ بدون ریسک باید عدد باشد!")
    if not math.isfinite(risk_free_rate):
        raise ValidationError("❌ نرخ بدون ریسک باید عدد متناهی باشد!")
    if risk_free_rate < 0:
        raise ValidationError("❌ نرخ بدون ریسک باید نامنفی باشد!")


def validate_frontier_points(points: int) -> None:
    """
    اعتبارسنجی تعداد نقاط مرز کارا (``MIN_FRONTIER_POINTS`` تا ``MAX_FRONTIER_POINTS``)

    Args:
        points (int): تعداد نقاط؛ bool و اعشاری رد می‌شود

    Raises:
        ValidationError: اگر عدد صحیح نباشد یا خارج از بازه باشد
    """
    if isinstance(points, bool) or not isinstance(points, int):
        raise ValidationError("❌ تعداد نقاط مرز کارا باید عدد صحیح باشد!")
    if not MIN_FRONTIER_POINTS <= points <= MAX_FRONTIER_POINTS:
        raise ValidationError(
            f"❌ تعداد نقاط مرز کارا باید بین {MIN_FRONTIER_POINTS} و "
            f"{MAX_FRONTIER_POINTS} باشد!"
        )


def validate_weights(weights: List[float], count: int) -> None:
    """
    اعتبارسنجی وزن‌های سبد: متناهی، هم‌طول با دارایی‌ها و با مجموع ۱

    مجموع وزن‌ها تا ``WEIGHT_SUM_TOLERANCE`` (مطلق) از ۱ فاصله مجاز دارد.
    وزن منفی (فروش استقراضی) اینجا رد نمی‌شود.

    Args:
        weights (List[float]): وزن هر دارایی
        count (int): تعداد دارایی‌ها

    Raises:
        ValidationError: اگر طول، نوع، متناهی بودن یا مجموع وزن‌ها نامعتبر باشد
    """
    if not isinstance(weights, (list, tuple)) or len(weights) != count:
        raise ValidationError("❌ تعداد وزن‌ها باید برابر تعداد دارایی‌ها باشد!")
    for index, value in enumerate(weights):
        label = f"وزن دارایی {index + 1}"
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValidationError(f"❌ {label} باید عدد باشد!")
        if not math.isfinite(value):
            raise ValidationError(f"❌ {label} باید عدد متناهی باشد!")
    total = sum(weights)
    if abs(total - 1.0) > WEIGHT_SUM_TOLERANCE:
        raise ValidationError(f"❌ مجموع وزن‌ها ({total}) باید برابر 1 باشد!")


def validate_risk_aversion(risk_aversion: float) -> None:
    """
    اعتبارسنجی ریسک‌گریزی A در سبد کامل: عدد متناهی و اکیداً مثبت

    Args:
        risk_aversion (float): ضریب ریسک‌گریزی؛ کران بالا ندارد

    Raises:
        ValidationError: اگر عدد نباشد، نامتناهی باشد یا مثبت نباشد
    """
    if isinstance(risk_aversion, bool) or not isinstance(risk_aversion, (int, float)):
        raise ValidationError("❌ ریسک‌گریزی باید عدد باشد!")
    if not math.isfinite(risk_aversion) or risk_aversion <= 0:
        raise ValidationError("❌ ریسک‌گریزی باید عدد متناهی و مثبت باشد!")


def validate_max_leverage(max_leverage: float) -> None:
    """
    اعتبارسنجی سقف اهرم y* در سبد کامل

    مقدار باید متناهی و در بازه ``MIN_LEVERAGE`` تا ``MAX_LEVERAGE`` (۰ تا ۳) باشد.

    Args:
        max_leverage (float): بیشترین وزن مجاز سبد مماس در سبد کامل

    Raises:
        ValidationError: اگر عدد نباشد یا خارج از بازه باشد
    """
    if isinstance(max_leverage, bool) or not isinstance(max_leverage, (int, float)):
        raise ValidationError("❌ حداکثر اهرم باید عدد باشد!")
    if not math.isfinite(max_leverage) or not MIN_LEVERAGE <= max_leverage <= MAX_LEVERAGE:
        raise ValidationError(
            f"❌ حداکثر اهرم باید بین {MIN_LEVERAGE} و {MAX_LEVERAGE} باشد!"
        )
