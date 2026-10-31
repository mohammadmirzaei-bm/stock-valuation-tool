"""نقاط پایانی آماره و بهینه‌سازی سبد.

پیشوند این روتر `/api/portfolio` است و جدا از `/api/valuation` سوار می‌شود.
هر endpoint دقیقاً یک تابع دامنه را صدا می‌زند.
"""

from fastapi import APIRouter

from ...domain.portfolio_analysis import analyze_portfolio
from ...domain.portfolio_stats import statistics_from_prices
from .. import schemas as s

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


@router.post(
    "/statistics",
    response_model=s.PortfolioStatisticsResult,
    summary="آماره سالانه بازده از سری قیمت هم‌تراز",
)
def statistics(payload: s.PortfolioStatisticsRequest) -> s.PortfolioStatisticsResult:
    """میانگین، کوواریانس، نوسان و همبستگی سالانه به ترتیب دارایی‌های ورودی."""
    result = statistics_from_prices(
        [asset.name for asset in payload.assets],
        [asset.prices for asset in payload.assets],
        payload.periods_per_year,
    )
    return s.PortfolioStatisticsResult.model_validate(result, from_attributes=True)


@router.post(
    "/optimize",
    response_model=s.PortfolioAnalysisResult,
    summary="مرز کارا، سبد مماس، خط تخصیص سرمایه و سبد کامل",
)
def optimize(payload: s.PortfolioOptimizeRequest) -> s.PortfolioAnalysisResult:
    """تحلیل سبد از بازده و کوواریانس سالانه."""
    result = analyze_portfolio(
        payload.asset_names,
        payload.mean_returns,
        payload.covariance,
        payload.risk_free_rate,
        payload.risk_aversion,
        allow_short=payload.allow_short,
        max_leverage=payload.max_leverage,
        frontier_points=payload.frontier_points,
    )
    return s.PortfolioAnalysisResult.model_validate(result, from_attributes=True)
