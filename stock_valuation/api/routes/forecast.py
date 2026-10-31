"""نقطه پایانی پیش‌بینی سالانه از محرک‌های درآمد و حاشیه."""

from fastapi import APIRouter

from ...domain.forecast import ForecastDrivers, build_projections
from .. import schemas as s

router = APIRouter()


@router.post(
    "/forecast",
    response_model=s.ForecastResult,
    summary="پیش‌بینی سالانه از محرک‌های درآمد، حاشیه و سرمایه‌گذاری",
)
def forecast(payload: s.ForecastRequest) -> s.ForecastResult:
    """ساخت جدول پیش‌بینی و سطرهای آماده DCF از محرک‌ها."""
    result = build_projections(
        payload.base_revenue,
        ForecastDrivers(
            revenue_growth=payload.revenue_growth,
            ebitda_margin=payload.ebitda_margin,
            da_pct_revenue=payload.da_pct_revenue,
            capex_pct_revenue=payload.capex_pct_revenue,
            nwc_pct_incremental_revenue=payload.nwc_pct_incremental_revenue,
        ),
        payload.years,
        terminal_growth=payload.terminal_growth,
        normalize_terminal_year=payload.normalize_terminal_year,
    )
    return s.ForecastResult.model_validate(result, from_attributes=True)
