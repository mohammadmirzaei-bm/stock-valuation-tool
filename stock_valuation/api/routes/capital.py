"""نقطه پایانی میانگین موزون هزینه سرمایه (WACC)."""

from fastapi import APIRouter

from ...domain import cost_of_capital
from .. import schemas as s

router = APIRouter()


@router.post(
    "/wacc",
    response_model=s.WaccResult,
    summary="میانگین موزون هزینه سرمایه (WACC)",
)
def weighted_average_cost_of_capital(payload: s.WaccRequest) -> s.WaccResult:
    """محاسبه WACC: `(E/V)×rₑ + (D/V)×r_d×(1 − t)`."""
    breakdown = cost_of_capital.wacc_breakdown(
        payload.equity,
        payload.debt,
        payload.cost_of_equity,
        payload.cost_of_debt,
        payload.tax_rate,
    )
    return s.WaccResult.model_validate(breakdown, from_attributes=True)
