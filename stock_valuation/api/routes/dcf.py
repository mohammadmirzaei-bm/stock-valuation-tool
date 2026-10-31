"""نقطه پایانی ارزش‌گذاری جریان نقدی تنزیل‌شده (DCF بر پایه FCFF)."""

from fastapi import APIRouter

from ...domain.dcf import dcf_valuation
from .. import schemas as s
from ._common import _to_projections

router = APIRouter()


@router.post(
    "/dcf",
    response_model=s.DcfResult,
    summary="ارزش‌گذاری با جریان نقدی تنزیل‌شده (DCF / FCFF)",
)
def dcf(payload: s.DcfRequest) -> s.DcfResult:
    """تنزیل FCFF و ارزش انتهای دوره گوردون؛ پل EV به ارزش هر سهم."""
    breakdown = dcf_valuation(
        _to_projections(payload.projections),
        payload.wacc,
        payload.terminal_growth,
        payload.shares_outstanding,
        payload.tax_rate,
        cash=payload.cash,
        debt=payload.debt,
        minority_interest=payload.minority_interest,
        preferred_equity=payload.preferred_equity,
    )
    return s.DcfResult.model_validate(breakdown, from_attributes=True)
