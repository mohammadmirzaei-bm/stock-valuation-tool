"""نقاط پایانی REST سرویس ارزیابی سهام.

هر endpoint دقیقاً یک تابع خالص لایه دامنه را صدا می‌زند و خروجی آن را به
مدل پاسخ Pydantic نگاشت می‌کند؛ هیچ فرمولی در این لایه دوباره پیاده‌سازی
نمی‌شود. فیلدهایی که دامنه در اختیار نمی‌گذارد (نمایش مجدد ورودی یا مقدار
برگشتی ساده) همان‌جا پر می‌شوند.

خطاهای دامنه (`ValidationError` و `CalculationError`) توسط exception handlerهای
سراسری در `api.errors` به پاسخ 400 با بدنه `ErrorResponse` تبدیل می‌شوند.
"""

from fastapi import APIRouter

from ..domain import valuation_models as models
from . import schemas as s

router = APIRouter(prefix="/api/valuation", tags=["valuation"])


@router.post(
    "/single-period",
    response_model=s.SinglePeriodResult,
    summary="ارزش‌گذاری با مدل تک‌دوره‌ای",
)
def single_period(payload: s.SinglePeriodRequest) -> s.SinglePeriodResult:
    """محاسبه قیمت سهام با مدل تک‌دوره‌ای: `P₀ = (D₁ + P₁) / (1 + r)`."""
    breakdown = models.single_period_decomposition(payload.d1, payload.p1, payload.r)
    return s.SinglePeriodResult.model_validate(breakdown)


@router.post(
    "/zero-growth",
    response_model=s.ZeroGrowthResult,
    summary="ارزش‌گذاری با مدل رشد صفر",
)
def zero_growth(payload: s.ZeroGrowthRequest) -> s.ZeroGrowthResult:
    """محاسبه قیمت سهام با رشد صفر: `P = D / r`."""
    price = models.zero_growth_model(payload.d, payload.r)
    return s.ZeroGrowthResult(
        price=price,
        dividend=payload.d,
        required_return=payload.r,
        required_return_percent=payload.r * 100,
        dividend_yield_percent=models.annual_dividend_yield_percent(payload.d, price),
    )


@router.post(
    "/annual-dividend-yield",
    response_model=s.AnnualDividendYieldResult,
    summary="بازده سالانه سود تقسیمی",
)
def annual_dividend_yield(payload: s.AnnualDividendYieldRequest) -> s.AnnualDividendYieldResult:
    """محاسبه بازده سالانه سود تقسیمی: `(D / P) × 100`."""
    return s.AnnualDividendYieldResult(
        dividend_yield_percent=models.annual_dividend_yield_percent(payload.dividend, payload.price),
        dividend=payload.dividend,
        price=payload.price,
    )


@router.post(
    "/gordon",
    response_model=s.GordonResult,
    summary="ارزش‌گذاری با مدل رشد ثابت گوردون",
)
def gordon(payload: s.GordonRequest) -> s.GordonResult:
    """محاسبه قیمت و اجزای بازده با مدل گوردون: `P = D₀(1+g) / (r − g)`."""
    breakdown = models.gordon_breakdown(payload.d0, payload.g, payload.r)
    return s.GordonResult.model_validate(breakdown).model_copy(
        update={
            "required_return": payload.r,
            "required_return_percent": payload.r * 100,
            "growth_rate": payload.g,
            "growth_rate_percent": payload.g * 100,
        }
    )


@router.post(
    "/supernormal-growth",
    response_model=s.SupernormalResult,
    summary="ارزش‌گذاری با مدل رشد غیرعادی چندمرحله‌ای",
)
def supernormal_growth(payload: s.SupernormalRequest) -> s.SupernormalResult:
    """محاسبه قیمت با رشد غیرعادی: `P₀ = Σ[Dₜ/(1+r)ᵗ] + Pₙ/(1+r)ⁿ`."""
    result = models.supernormal_growth_model(
        payload.d0, payload.growth_rates, payload.years, payload.g_constant, payload.r
    )
    schedule = models.supernormal_schedule(payload.growth_rates, result, payload.g_constant)
    return s.SupernormalResult.model_validate(result).model_copy(
        update={
            "schedule": [s.SupernormalScheduleRow.model_validate(row) for row in schedule],
        }
    )


@router.post(
    "/dividend-projection",
    response_model=s.DividendProjectionResult,
    summary="پیش‌بینی سود تقسیمی دوره‌های آینده",
)
def dividend_projection(payload: s.DividendProjectionRequest) -> s.DividendProjectionResult:
    """پیش‌بینی سود تقسیمی با رشد ثابت: `Dₜ = D₀(1+g)ᵗ`."""
    return s.DividendProjectionResult(
        dividends=models.project_dividends(payload.d0, payload.g, payload.periods),
        periods=payload.periods,
    )


@router.post(
    "/expected-return",
    response_model=s.ExpectedReturnResult,
    summary="بازده مورد انتظار سهام",
)
def expected_return(payload: s.ExpectedReturnRequest) -> s.ExpectedReturnResult:
    """محاسبه بازده مورد انتظار: `r = (D₁ / P₀) + g`."""
    breakdown = models.expected_return_breakdown(payload.d1, payload.p0, payload.g)
    return s.ExpectedReturnResult.model_validate(breakdown)


@router.post(
    "/capm",
    response_model=s.CapmResult,
    summary="بازده مورد انتظار با مدل CAPM",
)
def capm(payload: s.CapmRequest) -> s.CapmResult:
    """محاسبه بازده مورد انتظار با CAPM: `r = r_f + β × (r_m − r_f)`."""
    breakdown = models.capm_breakdown(payload.risk_free_rate, payload.beta, payload.market_return)
    return s.CapmResult.model_validate(breakdown).model_copy(
        update={"market_return_percent": payload.market_return * 100}
    )


@router.post(
    "/preferred-stock",
    response_model=s.PreferredStockResult,
    summary="ارزش‌گذاری سهام ممتاز",
)
def preferred_stock(payload: s.PreferredStockRequest) -> s.PreferredStockResult:
    """محاسبه قیمت سهام ممتاز با سود تقسیمی ثابت و بی‌نهایت: `P = D / r`."""
    price = models.preferred_stock_valuation(payload.d, payload.r)
    return s.PreferredStockResult(
        price=price,
        dividend=payload.d,
        required_return=payload.r,
        required_return_percent=payload.r * 100,
        dividend_yield_percent=models.annual_dividend_yield_percent(payload.d, price),
    )


@router.post(
    "/risk-premium",
    response_model=s.RiskPremiumResult,
    summary="حق‌الریسک سهام در مقایسه با اوراق قرضه",
)
def risk_premium(payload: s.RiskPremiumRequest) -> s.RiskPremiumResult:
    """محاسبه حق‌الریسک: `(r − نرخ اوراق قرضه) × 100`."""
    return s.RiskPremiumResult(
        risk_premium_percent=models.risk_premium_percent(
            payload.required_return, payload.bond_rate_percent
        ),
        required_return=payload.required_return,
        required_return_percent=payload.required_return * 100,
        bond_rate_percent=payload.bond_rate_percent,
    )


@router.post(
    "/growth-opportunities",
    response_model=s.GrowthOpportunitiesResult,
    summary="ارزش‌گذاری با فرصت‌های رشد",
)
def growth_opportunities(payload: s.GrowthOpportunitiesRequest) -> s.GrowthOpportunitiesResult:
    """محاسبه قیمت با فرصت‌های رشد: `P = (EPS / r) + NPVGO`."""
    breakdown = models.growth_opportunities_breakdown(payload.eps, payload.r, payload.npvgo)
    return s.GrowthOpportunitiesResult.model_validate(breakdown)


@router.post(
    "/peg",
    response_model=s.PegResult,
    summary="نسبت PEG همراه تفسیر",
)
def peg(payload: s.PegRequest) -> s.PegResult:
    """محاسبه نسبت PEG و تفسیر آن: `PEG = (P/E) / نرخ رشد سالانه`."""
    value = models.peg_ratio(payload.pe_ratio, payload.growth_rate_percent)
    return s.PegResult(
        peg=value,
        pe_ratio=payload.pe_ratio,
        growth_rate_percent=payload.growth_rate_percent,
        interpretation=s.PegInterpretation.model_validate(models.interpret_peg(value)),
    )
