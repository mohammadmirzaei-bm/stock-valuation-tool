"""پل ارزش بنگاه به ارزش حقوق صاحبان سهام — منطق خالص دامنه.

این ماژول تنها منبع حقیقت فرمول
``Equity = EV + cash − debt − minority_interest − preferred_equity``
است؛ ``dcf_valuation`` و هر تحلیل آینده (مثل ضریب‌های EV) از همین تابع
استفاده می‌کنند تا پل در کل پروژه یکسان بماند.

قرارداد خطا:
    ValidationError: ورودی نامعتبر
    CalculationError: نتیجه غیرعددی یا خطای عددی در محاسبه
"""

import logging
import math
from dataclasses import dataclass

from .errors import CalculationError, ValidationError
from .validators import (
    require_finite_number,
    validate_non_negative,
    validate_positive_number,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EquityBridge:
    """نتیجه پل ارزش بنگاه به ارزش حقوق صاحبان سهام

    Attributes:
        equity_value: ارزش حقوق صاحبان سهام (مقدار منفی خطا نیست)
        value_per_share: ارزش هر سهم (مقدار منفی خطا نیست)
    """

    equity_value: float
    value_per_share: float


def enterprise_to_equity(
    enterprise_value: float,
    cash: float,
    debt: float,
    minority_interest: float,
    preferred_equity: float,
    shares_outstanding: float,
) -> EquityBridge:
    """
    تبدیل ارزش بنگاه (EV) به ارزش حقوق صاحبان سهام و ارزش هر سهم

    پل ارزش:
    Equity = EV + cash − debt − minority_interest − preferred_equity
    و سپس ارزش هر سهم = Equity / تعداد سهام.
    ترتیب عملیات عیناً همین است تا نتایج در مقایسه با محاسبه مستقیم
    بیت‌به‌بیت یکسان بماند. مقدار منفی برای equity_value یا
    value_per_share خطا نیست (بدهی می‌تواند از EV بیشتر باشد).
    توجه: ``enterprise_value`` خروجی محاسبات است نه ورودی کاربر؛ مانند
    قرارداد ``dcf_valuation``، نامتناهی بودن آن CalculationError می‌دهد
    (نه ValidationError).

    Args:
        enterprise_value (float): ارزش بنگاه (EV)
        cash (float): موجودی نقد و معادل (نامنفی)
        debt (float): بدهی بهره‌دار (نامنفی)
        minority_interest (float): منافع اقلیت (نامنفی)
        preferred_equity (float): سهام ممتاز (نامنفی)
        shares_outstanding (float): تعداد سهام (مثبت)

    Returns:
        EquityBridge: ارزش حقوق صاحبان سهام و ارزش هر سهم

    Raises:
        ValidationError: در صورت نامعتبر بودن فیلدهای ترازنامه یا تعداد سهام
        CalculationError: اگر EV یا نتیجه محاسبه متناهی نباشد یا خطای عددی رخ دهد
    """
    require_finite_number(cash, "موجودی نقد")
    require_finite_number(debt, "بدهی")
    require_finite_number(minority_interest, "منافع اقلیت")
    require_finite_number(preferred_equity, "سهام ممتاز")
    require_finite_number(shares_outstanding, "تعداد سهام")

    validate_positive_number(shares_outstanding, "تعداد سهام")
    validate_non_negative(cash, "موجودی نقد")
    validate_non_negative(debt, "بدهی")
    validate_non_negative(minority_interest, "منافع اقلیت")
    validate_non_negative(preferred_equity, "سهام ممتاز")

    try:
        equity_value = (
            enterprise_value + cash - debt - minority_interest - preferred_equity
        )
        value_per_share = equity_value / shares_outstanding

        if not all(
            math.isfinite(value) for value in (equity_value, value_per_share)
        ):
            raise CalculationError("نتیجه محاسبه نامعتبر است")

        return EquityBridge(
            equity_value=equity_value,
            value_per_share=value_per_share,
        )
    except (ZeroDivisionError, ValueError, OverflowError) as e:
        logger.error(f"خطا در محاسبه پل EV به حقوق صاحبان سهام: {e}")
        raise CalculationError(f"خطا در محاسبه: {str(e)}")
