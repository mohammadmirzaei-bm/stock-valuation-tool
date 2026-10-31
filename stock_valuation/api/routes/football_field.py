"""نقطه پایانی خلاصه زمین فوتبال از بازه‌های ارزش روش‌های مختلف."""

from fastapi import APIRouter

from ...domain.football_field import ValuationRange, football_field_summary
from .. import schemas as s

router = APIRouter()


@router.post(
    "/football-field",
    response_model=s.FootballFieldResult,
    summary="خلاصه زمین فوتبال: دامنه کل، همپوشانی و موقعیت قیمت بازار",
)
def football_field(payload: s.FootballFieldRequest) -> s.FootballFieldResult:
    """خلاصه بازه‌های ارزش روش‌ها به ترتیب ورودی."""
    result = football_field_summary(
        [
            ValuationRange(
                method=item.method,
                low=item.low,
                mid=item.mid,
                high=item.high,
            )
            for item in payload.ranges
        ],
        market_price=payload.market_price,
    )
    return s.FootballFieldResult.model_validate(result, from_attributes=True)
