"""قراردادهای Pydantic آماره و بهینه‌سازی سبد."""

from typing import List, Optional

from pydantic import Field

from ...domain.validators import (
    DEFAULT_FRONTIER_POINTS,
    DEFAULT_MAX_LEVERAGE,
    MAX_ASSETS,
    MAX_FRONTIER_POINTS,
    MAX_LEVERAGE,
    MAX_PERIODS_PER_YEAR,
    MIN_ASSETS,
    MIN_FRONTIER_POINTS,
    MIN_LEVERAGE,
    MIN_OBSERVATIONS,
    MIN_PERIODS_PER_YEAR,
)
from .common import _Base, _RequestBase


class PriceSeriesInput(_RequestBase):
    """سری قیمت یک دارایی؛ هم‌ترازی زمانی با بقیه دارایی‌ها بر عهده فرانت‌اند است."""

    name: str = Field(min_length=1, description="نام یکتای دارایی")
    prices: List[float] = Field(
        min_length=MIN_OBSERVATIONS,
        description="قیمت‌های مثبت و متناهی، هم‌طول با سایر دارایی‌ها",
    )


class PortfolioStatisticsRequest(_RequestBase):
    """ورودی آماره سالانه از قیمت‌های هم‌تراز."""

    assets: List[PriceSeriesInput] = Field(
        min_length=MIN_ASSETS,
        max_length=MAX_ASSETS,
        description="دارایی‌ها به ترتیب ستون‌های کوواریانس",
    )
    periods_per_year: int = Field(
        ge=MIN_PERIODS_PER_YEAR,
        le=MAX_PERIODS_PER_YEAR,
        description="تعداد دوره‌های بازده در سال؛ عدد صحیح ۱ تا ۳۶۶",
    )


class PortfolioStatisticsResult(_Base):
    """پاسخ آماره نمونه‌ای سالانه؛ معادل `SampleStatistics` دامنه."""

    mean_returns: List[float] = Field(description="میانگین حسابی سالانه (اعشاری)")
    mean_returns_percent: List[float] = Field(description="میانگین سالانه به درصد")
    covariance: List[List[float]] = Field(description="کوواریانس نمونه‌ای سالانه")
    volatilities: List[float] = Field(description="نوسان سالانه (اعشاری)")
    volatilities_percent: List[float] = Field(description="نوسان سالانه به درصد")
    correlation: List[List[float]] = Field(description="همبستگی نمونه‌ای")
    observations: int = Field(description="تعداد بازده هر دارایی، نه تعداد قیمت")


class PortfolioOptimizeRequest(_RequestBase):
    """ورودی تحلیل سبد از بازده و کوواریانس سالانه."""

    asset_names: List[str] = Field(
        min_length=MIN_ASSETS,
        max_length=MAX_ASSETS,
        description="نام یکتای دارایی‌ها به ترتیب بردار بازده",
    )
    mean_returns: List[float] = Field(
        min_length=MIN_ASSETS,
        max_length=MAX_ASSETS,
        description="بازده مورد انتظار سالانه (اعشاری)",
    )
    covariance: List[List[float]] = Field(
        description="کوواریانس سالانه؛ مربعی، متقارن و با قطر نامنفی"
    )
    risk_free_rate: float = Field(ge=0, description="نرخ بدون ریسک سالانه (اعشاری، نامنفی)")
    risk_aversion: float = Field(gt=0, description="ریسک‌گریزی A؛ متناهی و مثبت")
    allow_short: bool = Field(default=False, description="آیا فروش استقراضی مجاز است؟")
    max_leverage: float = Field(
        default=DEFAULT_MAX_LEVERAGE,
        ge=MIN_LEVERAGE,
        le=MAX_LEVERAGE,
        description="سقف وزن سبد مماس در سبد کامل؛ ۰ تا ۳",
    )
    frontier_points: int = Field(
        default=DEFAULT_FRONTIER_POINTS,
        ge=MIN_FRONTIER_POINTS,
        le=MAX_FRONTIER_POINTS,
        description="تعداد نقاط مرز کارا",
    )


class AssetPointResult(_Base):
    """یک دارایی برای نمودار پراکندگی؛ معادل `AssetPoint` دامنه."""

    name: str = Field(description="نام دارایی")
    expected_return: float = Field(description="بازده مورد انتظار سالانه (اعشاری)")
    expected_return_percent: float = Field(description="بازده مورد انتظار به درصد")
    volatility: float = Field(description="نوسان سالانه (اعشاری)")
    volatility_percent: float = Field(description="نوسان سالانه به درصد")


class PortfolioPointResult(_Base):
    """یک سبد؛ معادل `PortfolioPoint` دامنه. شارپ بدون نرخ بدون ریسک null است."""

    weights: List[float] = Field(description="وزن دارایی‌ها")
    weights_percent: List[float] = Field(description="وزن‌ها به درصد")
    expected_return: float = Field(description="بازده مورد انتظار (اعشاری)")
    expected_return_percent: float = Field(description="بازده مورد انتظار به درصد")
    variance: float = Field(description="واریانس سالانه")
    volatility: float = Field(description="نوسان سالانه (اعشاری)")
    volatility_percent: float = Field(description="نوسان سالانه به درصد")
    sharpe_ratio: Optional[float] = Field(description="نسبت شارپ؛ اگر تعریف نشده باشد null")


class AllocationPointResult(_Base):
    """نقطه کمکی خط تخصیص سرمایه؛ معادل `AllocationPoint` دامنه."""

    expected_return: float = Field(description="بازده مورد انتظار (اعشاری)")
    expected_return_percent: float = Field(description="بازده مورد انتظار به درصد")
    volatility: float = Field(description="نوسان (اعشاری)")
    volatility_percent: float = Field(description="نوسان به درصد")


class CapitalAllocationLineResult(_Base):
    """خط تخصیص سرمایه؛ معادل `CapitalAllocationLine` دامنه."""

    risk_free_rate: float = Field(description="عرض از مبدأ (اعشاری)")
    risk_free_rate_percent: float = Field(description="نرخ بدون ریسک به درصد")
    slope: float = Field(description="شیب؛ نسبت شارپ سبد مماس")
    points: List[AllocationPointResult] = Field(
        description="دو نقطه کمکی: نرخ بدون ریسک با نوسان صفر، و امتداد نوسان سبد مماس"
    )


class CompletePortfolioResult(_Base):
    """سبد کامل؛ معادل `CompletePortfolio` دامنه."""

    risk_aversion: float = Field(description="ضریب ریسک‌گریزی")
    tangency_weight: float = Field(description="وزن سبد مماس پس از برش (y*)")
    tangency_weight_percent: float = Field(description="وزن سبد مماس به درصد")
    risk_free_weight: float = Field(description="وزن دارایی بدون ریسک")
    risk_free_weight_percent: float = Field(description="وزن دارایی بدون ریسک به درصد")
    risky_weights: List[float] = Field(description="وزن دارایی‌های ریسک‌دار")
    risky_weights_percent: List[float] = Field(description="وزن دارایی‌های ریسک‌دار به درصد")
    expected_return: float = Field(description="بازده سبد کامل (اعشاری)")
    expected_return_percent: float = Field(description="بازده سبد کامل به درصد")
    volatility: float = Field(description="نوسان سبد کامل (اعشاری)")
    volatility_percent: float = Field(description="نوسان سبد کامل به درصد")
    leverage_capped: bool = Field(description="آیا y* به سقف اهرم بریده شده است؟")
    clipped_to_zero: bool = Field(description="آیا y* به‌خاطر بازده مازاد نامثبت صفر شده است؟")


class PortfolioAnalysisResult(_Base):
    """پاسخ تحلیل سبد؛ معادل `PortfolioAnalysis` دامنه."""

    assets: List[AssetPointResult] = Field(description="دارایی‌ها برای نمودار پراکندگی")
    min_variance: PortfolioPointResult = Field(description="سبد حداقل واریانس")
    tangency: PortfolioPointResult = Field(description="سبد مماس")
    frontier: List[PortfolioPointResult] = Field(description="مرز کارا")
    equal_weight: PortfolioPointResult = Field(description="سبد معیار با وزن برابر")
    capital_allocation_line: CapitalAllocationLineResult = Field(description="خط تخصیص سرمایه")
    complete_portfolio: CompletePortfolioResult = Field(description="سبد کامل")
