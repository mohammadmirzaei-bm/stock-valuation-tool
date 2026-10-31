"""کمک‌کننده‌های مشترک نقاط پایانی API."""

from typing import List

from ...domain.dcf import CashFlowProjection
from .. import schemas as s


def _to_projections(rows: List[s.CashFlowProjectionInput]) -> List[CashFlowProjection]:
    """تبدیل سطرهای پیش‌بینی درخواست به نمونه‌های دامنه."""
    return [
        CashFlowProjection(
            ebit=row.ebit,
            depreciation=row.depreciation,
            capex=row.capex,
            delta_nwc=row.delta_nwc,
        )
        for row in rows
    ]
