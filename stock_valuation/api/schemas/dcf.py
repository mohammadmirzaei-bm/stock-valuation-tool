"""قراردادهای Pydantic ارزش‌گذاری جریان نقدی تنزیل‌شده (DCF)."""

from typing import List

from pydantic import Field

from .common import _Base, _RequestBase


class CashFlowProjectionInput(_RequestBase):
    """یک سال اجزای FCFF؛ سال = اندیس در فهرست درخواست."""

    ebit: float = Field(description="سود عملیاتی قبل از بهره و مالیات")
    depreciation: float = Field(description="استهلاک و هزینه‌های غیرنقدی")
    capex: float = Field(description="مخارج سرمایه‌ای؛ مثبت = خروج نقد")
    delta_nwc: float = Field(description="تغییر سرمایه در گردش؛ مثبت = افزایش NWC")


class FcffYearRowResult(_Base):
    """یک سطر جدول سالانه DCF؛ معادل `FcffYearRow` دامنه."""

    year: int = Field(description="شماره سال (۱ تا n)")
    ebit: float = Field(description="سود عملیاتی سال")
    nopat: float = Field(description="سود عملیاتی بعد از مالیات")
    depreciation: float = Field(description="استهلاک")
    capex: float = Field(description="مخارج سرمایه‌ای")
    delta_nwc: float = Field(description="تغییر سرمایه در گردش")
    fcff: float = Field(description="جریان نقدی آزاد بنگاه")
    discount_factor: float = Field(description="ضریب تنزیل")
    present_value: float = Field(description="ارزش فعلی FCFF سال")


class DcfRequest(_RequestBase):
    """ورودی ارزش‌گذاری DCF؛ کرانه‌های عددی در دامنه اعمال می‌شوند."""

    projections: List[CashFlowProjectionInput] = Field(
        min_length=1,
        max_length=50,
        description="پیش‌بینی سالانه اجزای FCFF؛ سال = اندیس از ۱",
    )
    wacc: float = Field(description="نرخ WACC / تنزیل (اعشاری)")
    terminal_growth: float = Field(description="نرخ رشد پایانی (اعشاری)")
    shares_outstanding: float = Field(description="تعداد سهام")
    tax_rate: float = Field(description="نرخ مالیات سراسری (اعشاری)")
    cash: float = Field(default=0.0, description="موجودی نقد و معادل")
    debt: float = Field(default=0.0, description="بدهی بهره‌دار")
    minority_interest: float = Field(default=0.0, description="منافع اقلیت")
    preferred_equity: float = Field(default=0.0, description="سهام ممتاز")


class DcfResult(_Base):
    """پاسخ DCF؛ معادل `DcfBreakdown` دامنه."""

    enterprise_value: float = Field(description="ارزش بنگاه (EV)")
    equity_value: float = Field(description="ارزش حقوق صاحبان سهام")
    value_per_share: float = Field(description="ارزش هر سهم")
    wacc: float = Field(description="نرخ WACC (اعشاری)")
    wacc_percent: float = Field(description="نرخ WACC (درصد)")
    terminal_growth: float = Field(description="نرخ رشد پایانی (اعشاری)")
    terminal_growth_percent: float = Field(description="نرخ رشد پایانی (درصد)")
    terminal_value: float = Field(description="ارزش انتهای دوره (تنزیل‌نشده)")
    pv_terminal_value: float = Field(description="ارزش فعلی ارزش انتهای دوره")
    pv_fcff_total: float = Field(description="مجموع ارزش فعلی FCFFهای دوره صریح")
    cash: float = Field(description="موجودی نقد")
    debt: float = Field(description="بدهی")
    minority_interest: float = Field(description="منافع اقلیت")
    preferred_equity: float = Field(description="سهام ممتاز")
    shares_outstanding: float = Field(description="تعداد سهام")
    terminal_value_share_percent: float = Field(
        description="سهم ارزش فعلی انتهای دوره از EV (درصد)"
    )
    years: List[FcffYearRowResult] = Field(description="جدول سالانه پیش‌بینی")
