"""قراردادهای داده لایه API (Pydantic) برای سرویس ارزیابی سهام.

این بسته پل میان توابع خالص دامنه و JSON مبادله‌شده با فرانت‌اند React است و
همه نام‌ها را از زیرماژول‌های موضوعی دوباره صادر می‌کند تا
`from . import schemas as s` و `schemas.SomeModel` بدون تغییر کار کند.

ماژول‌ها:
    common: پایه‌های مشترک (`_Base`، `_RequestBase`) و بدنه خطا
    equity: مدل‌های سهام عادی و سود تقسیمی
    capital: میانگین موزون هزینه سرمایه (WACC)
    dcf: مدل‌های DCF بر پایه FCFF
    dcf_analysis: سناریوها، ماتریس حساسیت و DCF معکوس
    forecast: پیش‌بینی مبتنی بر محرک‌ها
    multiples: ارزش‌گذاری نسبی با ضریب همتایان
    football_field: خلاصه زمین فوتبال
    portfolio: آماره نمونه‌ای و بهینه‌سازی سبد

نکات طراحی:
    1. کلاس‌های پاسخ، آینه مدل‌های دامنه (NamedTuple / dataclass منجمد) هستند
       و نام فیلدهایشان دقیقاً یکی است؛ پس ساخت از نمونه دامنه بدون نگاشت
       دستی کار می‌کند.
    2. فیلدهای درصدی که در دامنه property هستند (مانند
       `dividend_yield_percent`) با `from_attributes` به‌صورت خودکار پر می‌شوند.
       فیلدهایی که دامنه نمی‌دهد (نمایش مجدد ورودی، یا مقدار برگشتی ساده تابع)
       `Optional` هستند و لایه endpoint مقدارشان را پر می‌کند؛ نامپرشان `None`
       می‌ماند تا در JSON قابل تشخیص باشد.
    3. کرانه‌های `Field` فقط آینه اعتبارسنج‌های دامنه هستند و هیچ قانون
       جدیدی اضافه نمی‌کنند؛ منبع حقیقت اعتبارسنجی همان `domain.validators`
       و خود توابع دامنه است (خطاها به شکل ValidationError / CalculationError
       در لایه HTTP ترجمه می‌شوند).
    4. نرخ‌ها (گوردون، رشد غیرعادی، بازده مورد انتظار، CAPM) بر حسب اعشار
       وارد می‌شوند؛ همان قرارداد دامنه. مثلاً ۱۲٪ === 0.12
       استثنای آن دو مدل دامنه‌ای است که ذاتاً درصدی کار می‌کنند:
       نرخ رشد در `risk_premium_percent` و نرخ رشد در `peg_ratio`.
"""

from .capital import WaccRequest, WaccResult
from .common import ErrorResponse
from .dcf import CashFlowProjectionInput, DcfRequest, DcfResult, FcffYearRowResult
from .dcf_analysis import (
    DcfScenarioInput,
    DcfScenarioRequest,
    DcfScenarioResult,
    DcfSensitivityRequest,
    DcfSensitivityResult,
    ReverseDcfRequest,
    ReverseDcfResult,
    ScenarioRowResult,
)
from .football_field import (
    FootballFieldRequest,
    FootballFieldResult,
    FootballFieldRowResult,
    ValuationRangeInput,
)
from .forecast import ForecastRequest, ForecastResult, ForecastYearRowResult
from .portfolio import (
    AllocationPointResult,
    AssetPointResult,
    CapitalAllocationLineResult,
    CompletePortfolioResult,
    PortfolioAnalysisResult,
    PortfolioOptimizeRequest,
    PortfolioPointResult,
    PortfolioStatisticsRequest,
    PortfolioStatisticsResult,
    PriceSeriesInput,
)
from .multiples import (
    ImpliedCaseResult,
    ImpliedValuationResult,
    MultiplesRequest,
    PeerMultipleInput,
    PeerStatisticsResult,
)
from .equity import (
    AnnualDividendYieldRequest,
    AnnualDividendYieldResult,
    CapmRequest,
    CapmResult,
    DividendProjectionRequest,
    DividendProjectionResult,
    ExpectedReturnRequest,
    ExpectedReturnResult,
    GordonRequest,
    GordonResult,
    GrowthOpportunitiesRequest,
    GrowthOpportunitiesResult,
    PegInterpretation,
    PegRequest,
    PegResult,
    PreferredStockRequest,
    PreferredStockResult,
    RetentionCurvePointResult,
    RiskPremiumRequest,
    RiskPremiumResult,
    SinglePeriodRequest,
    SinglePeriodResult,
    SupernormalRequest,
    SupernormalResult,
    SupernormalScheduleRow,
    SustainableGrowthRequest,
    SustainableGrowthResult,
    ZeroGrowthRequest,
    ZeroGrowthResult,
)

__all__ = [
    "WaccRequest",
    "WaccResult",
    "ErrorResponse",
    "CashFlowProjectionInput",
    "FcffYearRowResult",
    "DcfRequest",
    "DcfResult",
    "ScenarioRowResult",
    "DcfScenarioResult",
    "DcfScenarioInput",
    "DcfScenarioRequest",
    "DcfSensitivityRequest",
    "DcfSensitivityResult",
    "ReverseDcfRequest",
    "ReverseDcfResult",
    "SinglePeriodResult",
    "GordonResult",
    "ZeroGrowthResult",
    "PreferredStockResult",
    "AnnualDividendYieldResult",
    "ExpectedReturnResult",
    "CapmResult",
    "SupernormalScheduleRow",
    "SupernormalResult",
    "GrowthOpportunitiesResult",
    "RetentionCurvePointResult",
    "SustainableGrowthResult",
    "PegInterpretation",
    "PegResult",
    "RiskPremiumResult",
    "SinglePeriodRequest",
    "GordonRequest",
    "ZeroGrowthRequest",
    "PreferredStockRequest",
    "AnnualDividendYieldRequest",
    "ExpectedReturnRequest",
    "CapmRequest",
    "SupernormalRequest",
    "DividendProjectionRequest",
    "DividendProjectionResult",
    "GrowthOpportunitiesRequest",
    "SustainableGrowthRequest",
    "PegRequest",
    "RiskPremiumRequest",
    "ForecastRequest",
    "ForecastYearRowResult",
    "ForecastResult",
    "PeerMultipleInput",
    "MultiplesRequest",
    "PeerStatisticsResult",
    "ImpliedCaseResult",
    "ImpliedValuationResult",
    "ValuationRangeInput",
    "FootballFieldRequest",
    "FootballFieldRowResult",
    "FootballFieldResult",
    "PriceSeriesInput",
    "PortfolioStatisticsRequest",
    "PortfolioStatisticsResult",
    "PortfolioOptimizeRequest",
    "AssetPointResult",
    "PortfolioPointResult",
    "AllocationPointResult",
    "CapitalAllocationLineResult",
    "CompletePortfolioResult",
    "PortfolioAnalysisResult",
]
