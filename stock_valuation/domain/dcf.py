"""ارزش‌گذاری جریان نقدی تنزیل‌شده (DCF بر پایه FCFF) — منطق خالص دامنه.

قرارداد خطا:
    ValidationError: ورودی نامعتبر یا FCFF پایانی نامثبت
    CalculationError: نتیجه غیرعددی یا خطای عددی در محاسبه
"""

import logging
import math
from dataclasses import dataclass
from typing import List

from .bridge import enterprise_to_equity
from .errors import CalculationError, ValidationError
from .validators import (
    require_finite_number,
    validate_non_negative,
    validate_positive_number,
    validate_projections_length,
    validate_tax_rate,
    validate_terminal_growth_vs_wacc,
)

logger = logging.getLogger(__name__)


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
    require_finite_number(ebit, "سود عملیاتی (EBIT)")
    require_finite_number(tax_rate, "نرخ مالیات")
    require_finite_number(depreciation, "استهلاک")
    require_finite_number(capex, "مخارج سرمایه‌ای")
    require_finite_number(delta_nwc, "تغییر سرمایه در گردش")
    validate_tax_rate(tax_rate)

    try:
        result = ebit * (1 - tax_rate) + depreciation - capex - delta_nwc
        if not math.isfinite(result):
            raise CalculationError("نتیجه محاسبه نامعتبر است")
        return result
    except (ZeroDivisionError, ValueError, OverflowError) as e:
        logger.error(f"خطا در محاسبه FCFF: {e}")
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

    require_finite_number(wacc_rate, "نرخ WACC")
    require_finite_number(terminal_growth, "نرخ رشد پایانی")
    require_finite_number(shares_outstanding, "تعداد سهام")
    require_finite_number(tax_rate, "نرخ مالیات")
    require_finite_number(cash, "موجودی نقد")
    require_finite_number(debt, "بدهی")
    require_finite_number(minority_interest, "منافع اقلیت")
    require_finite_number(preferred_equity, "سهام ممتاز")

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
        # تنها منبع حقیقت پل EV ← حقوق صاحبان سهام در domain.bridge است.
        bridge = enterprise_to_equity(
            enterprise_value,
            cash,
            debt,
            minority_interest,
            preferred_equity,
            shares_outstanding,
        )
        equity_value = bridge.equity_value
        value_per_share = bridge.value_per_share
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
