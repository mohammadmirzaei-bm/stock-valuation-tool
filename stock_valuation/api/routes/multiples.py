"""نقطه پایانی ارزش‌گذاری نسبی با ضریب همتایان."""

from fastapi import APIRouter

from ...domain.multiples import PeerMultiple, implied_valuation
from .. import schemas as s

router = APIRouter()


@router.post(
    "/multiples",
    response_model=s.ImpliedValuationResult,
    summary="ارزش تلویحی با ضریب همتایان (P/E، P/B، P/S، EV/EBITDA، EV/Sales)",
)
def multiples(payload: s.MultiplesRequest) -> s.ImpliedValuationResult:
    """آماره‌های همتایان و ارزش تلویحی در چارک‌ها، میانه و میانگین."""
    result = implied_valuation(
        payload.kind,
        payload.metric,
        payload.shares_outstanding,
        [PeerMultiple(name=peer.name, value=peer.value) for peer in payload.peers],
        cash=payload.cash,
        debt=payload.debt,
        minority_interest=payload.minority_interest,
        preferred_equity=payload.preferred_equity,
    )
    return s.ImpliedValuationResult.model_validate(result, from_attributes=True)
