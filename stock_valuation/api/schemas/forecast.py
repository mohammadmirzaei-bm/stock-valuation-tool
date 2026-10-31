"""قراردادهای Pydantic پیش‌بینی مبتنی بر محرک‌ها."""

from typing import List, Optional, Union

from pydantic import Field

from ...domain.validators import MAX_PROJECTIONS
from .common import _Base, _RequestBase
from .dcf import CashFlowProjectionInput


class ForecastRequest(_RequestBase):
    """ورودی پیش‌بینی سالانه از محرک‌های درآمد و حاشیه.

    هر محرک یا یک عدد است (اعمال به همه سال‌ها) یا فهرستی به طول
    دقیقاً ``years``؛ کرانه‌های عددی در دامنه اعمال می‌شوند.
    """

    base_revenue: float = Field(
        description="آخرین درآمد تاریخی (متناهی و مثبت)"
    )
    years: int = Field(
        ge=1,
        le=MAX_PROJECTIONS,
        description="تعداد سال‌های پیش‌بینی (۱ تا MAX_PROJECTIONS)",
    )
    revenue_growth: Union[float, List[float]] = Field(
        description="نرخ رشد درآمد هر سال (اعشاری؛ بیشتر از −۱۰۰٪) یا یک عدد برای همه سال‌ها"
    )
    ebitda_margin: Union[float, List[float]] = Field(
        description="حاشیه سود عملیاتی (۰ تا ۱) یا فهرست سالانه"
    )
    da_pct_revenue: Union[float, List[float]] = Field(
        description="نسبت استهلاک به درآمد (۰ تا ۱) یا فهرست سالانه"
    )
    capex_pct_revenue: Union[float, List[float]] = Field(
        description="نسبت مخارج سرمایه‌ای به درآمد (۰ تا ۱) یا فهرست سالانه"
    )
    nwc_pct_incremental_revenue: Union[float, List[float]] = Field(
        description="نسبت سرمایه در گردش به درآمد افزایشی (۰ تا ۱) یا فهرست سالانه"
    )
    terminal_growth: Optional[float] = Field(
        default=None,
        description="نرخ رشد پایانی (اعشاری)؛ برای نرمال‌سازی سال پایانی لازم است",
    )
    normalize_terminal_year: bool = Field(
        default=False,
        description="نرمال‌سازی آخرین سال به حالت پایدار (Capex = استهلاک)",
    )


class ForecastYearRowResult(_Base):
    """یک سطر جدول پیش‌بینی؛ معادل `ForecastYearRow` دامنه."""

    year: int = Field(description="شماره سال (۱ تا n)")
    revenue: float = Field(description="درآمد سال")
    growth: float = Field(description="نرخ رشد درآمد سال (اعشاری)")
    growth_percent: float = Field(description="نرخ رشد درآمد سال (درصد)")
    ebitda: float = Field(description="سود عملیاتی قبل از استهلاک و مالیات")
    ebitda_margin: float = Field(description="حاشیه سود عملیاتی سال (اعشاری)")
    ebitda_margin_percent: float = Field(description="حاشیه سود عملیاتی سال (درصد)")
    ebit: float = Field(description="سود عملیاتی = EBITDA − استهلاک")
    depreciation: float = Field(description="استهلاک سال")
    capex: float = Field(description="مخارج سرمایه‌ای (خروج نقد مثبت)")
    delta_nwc: float = Field(description="تغییر سرمایه در گردش؛ مثبت = افزایش NWC")


class ForecastResult(_Base):
    """پاسخ پیش‌بینی؛ معادل `ForecastResult` دامنه.

    فیلد `projections` دقیقاً همان شکلی است که `DcfRequest.projections`
    می‌پذیرد و می‌تواند مستقیماً به نقطه پایانی `/dcf` داده شود.
    """

    projections: List[CashFlowProjectionInput] = Field(
        description="سطرهای آماده مصرف در مدل DCF (همان شکل DcfRequest.projections)"
    )
    revenues: List[float] = Field(description="درآمد هر سال")
    ebitda: List[float] = Field(description="EBITDA هر سال")
    rows: List[ForecastYearRowResult] = Field(description="جدول سالانه کامل پیش‌بینی")
