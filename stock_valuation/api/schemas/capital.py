"""قراردادهای Pydantic میانگین موزون هزینه سرمایه (WACC)."""

from pydantic import Field

from .common import _Base, _RequestBase


class WaccRequest(_RequestBase):
    """ورودی میانگین موزون هزینه سرمایه؛ کرانه‌های عددی در دامنه اعمال می‌شوند."""

    equity: float = Field(description="ارزش بازار حقوق صاحبان سهام")
    debt: float = Field(description="ارزش بازار بدهی؛ صفر برای بنگاه تمام‌سهامی مجاز است")
    cost_of_equity: float = Field(description="هزینه حقوق صاحبان سهام (اعشاری)")
    cost_of_debt: float = Field(description="هزینه بدهی قبل از مالیات (اعشاری)")
    tax_rate: float = Field(description="نرخ مالیات (اعشاری)")


class WaccResult(_Base):
    """پاسخ WACC؛ معادل `WaccBreakdown` دامنه."""

    wacc: float = Field(description="نرخ WACC (اعشاری)")
    wacc_percent: float = Field(description="نرخ WACC (درصد)")
    equity: float = Field(description="ارزش بازار حقوق صاحبان سهام")
    debt: float = Field(description="ارزش بازار بدهی")
    total_capital: float = Field(description="مجموع سرمایه (E + D)")
    equity_weight: float = Field(description="وزن حقوق صاحبان سهام (اعشاری)")
    debt_weight: float = Field(description="وزن بدهی (اعشاری)")
    equity_weight_percent: float = Field(description="وزن حقوق صاحبان سهام (درصد)")
    debt_weight_percent: float = Field(description="وزن بدهی (درصد)")
    cost_of_equity: float = Field(description="هزینه حقوق صاحبان سهام (اعشاری)")
    cost_of_equity_percent: float = Field(description="هزینه حقوق صاحبان سهام (درصد)")
    cost_of_debt: float = Field(description="هزینه بدهی قبل از مالیات (اعشاری)")
    cost_of_debt_percent: float = Field(description="هزینه بدهی قبل از مالیات (درصد)")
    after_tax_cost_of_debt: float = Field(description="هزینه بدهی بعد از مالیات (اعشاری)")
    after_tax_cost_of_debt_percent: float = Field(description="هزینه بدهی بعد از مالیات (درصد)")
    tax_rate: float = Field(description="نرخ مالیات (اعشاری)")
    tax_rate_percent: float = Field(description="نرخ مالیات (درصد)")
