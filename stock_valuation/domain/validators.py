"""اعتبارسنجی ورودی‌های مدل‌های ارزیابی سهام.

توابع این ماژول خالص (pure) و قطعی هستند، وضعیت سراسری یا نشست برنامه را
تغییر نمی‌دهند و هیچ وابستگی‌ای به Streamlit ندارند.
"""

from .errors import ValidationError

# حداقل اختلاف مجاز بین نرخ بازده و نرخ رشد (۰.۵ درصد)
MIN_SPREAD = 0.005


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
