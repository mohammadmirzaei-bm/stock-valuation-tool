"""نقاط پایانی تحلیل‌های تکمیلی DCF: سناریوها، حساسیت و DCF معکوس."""

from fastapi import APIRouter

from ...domain import dcf_analysis
from .. import schemas as s
from ._common import _to_projections

router = APIRouter()


@router.post(
    "/dcf-scenarios",
    response_model=s.DcfScenarioResult,
    summary="ارزش‌گذاری سناریوهای وزنی DCF و ریسک ارزش هر سهم",
)
def dcf_scenarios(payload: s.DcfScenarioRequest) -> s.DcfScenarioResult:
    """ارزش‌گذاری همهٔ سناریوها با احتمال‌های ورودی و ترازنامهٔ مشترک."""
    scenarios = [
        dcf_analysis.DcfScenario(
            name=row.name, probability=row.probability,
            projections=_to_projections(row.projections),
            wacc_rate=row.wacc, terminal_growth=row.terminal_growth,
        )
        for row in payload.scenarios
    ]
    breakdown = dcf_analysis.dcf_scenario_valuation(
        scenarios, payload.shares_outstanding, payload.tax_rate,
        cash=payload.cash, debt=payload.debt, minority_interest=payload.minority_interest,
        preferred_equity=payload.preferred_equity, market_price=payload.market_price,
    )
    return s.DcfScenarioResult.model_validate(breakdown, from_attributes=True)


@router.post(
    "/dcf-sensitivity",
    response_model=s.DcfSensitivityResult,
    summary="ماتریس حساسیت DCF نسبت به WACC و رشد پایانی",
)
def dcf_sensitivity(payload: s.DcfSensitivityRequest) -> s.DcfSensitivityResult:
    """ماتریس ارزش هر سهم و EV برای ترکیب‌های WACC × رشد پایانی؛ سلول نامعتبر null است."""
    result = dcf_analysis.dcf_sensitivity(
        _to_projections(payload.projections),
        payload.wacc,
        payload.terminal_growth,
        payload.shares_outstanding,
        payload.tax_rate,
        cash=payload.cash,
        debt=payload.debt,
        minority_interest=payload.minority_interest,
        preferred_equity=payload.preferred_equity,
        wacc_step=payload.wacc_step,
        growth_step=payload.growth_step,
        wacc_points=payload.wacc_points,
        growth_points=payload.growth_points,
    )
    return s.DcfSensitivityResult.model_validate(result, from_attributes=True)


@router.post(
    "/reverse-dcf",
    response_model=s.ReverseDcfResult,
    summary="رشد پایانی تلویحی قیمت بازار با DCF معکوس",
)
def reverse_dcf(payload: s.ReverseDcfRequest) -> s.ReverseDcfResult:
    """یافتن نرخ رشد پایانی که ارزش هر سهم را برابر قیمت بازار می‌کند."""
    result = dcf_analysis.reverse_dcf_implied_growth(
        _to_projections(payload.projections),
        payload.wacc,
        payload.shares_outstanding,
        payload.tax_rate,
        payload.market_price,
        cash=payload.cash,
        debt=payload.debt,
        minority_interest=payload.minority_interest,
        preferred_equity=payload.preferred_equity,
        reference_terminal_growth=payload.terminal_growth,
    )
    return s.ReverseDcfResult.model_validate(result, from_attributes=True)
