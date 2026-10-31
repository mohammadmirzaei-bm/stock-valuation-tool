"""میانگین موزون هزینه سرمایه (WACC) — منطق خالص لایه دامنه.

قرارداد خطا:
    ValidationError: ورودی نامعتبر یا سرمایه کل نامثبت
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
    validate_tax_rate,
)

logger = logging.getLogger(__name__)


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


# ---------------------------------------------------------------------------
# WACC (میانگین موزون هزینه سرمایه)
# ---------------------------------------------------------------------------


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
    require_finite_number(equity, "ارزش حقوق صاحبان سهام")
    require_finite_number(debt, "ارزش بدهی")
    require_finite_number(cost_of_equity, "هزینه حقوق صاحبان سهام")
    require_finite_number(cost_of_debt, "هزینه بدهی")
    require_finite_number(tax_rate, "نرخ مالیات")

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
