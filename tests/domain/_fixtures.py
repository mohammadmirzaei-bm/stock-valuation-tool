"""فیکسچرهای مشترک تست‌های لایه دامنه."""

from stock_valuation.domain.dcf import CashFlowProjection


def _reference_dcf_projections():
    """پیش‌بینی پنج‌ساله مرجع برای آزمون‌های DCF، حساسیت و DCF معکوس"""
    return [
        CashFlowProjection(ebit=1000.0, depreciation=200.0, capex=250.0, delta_nwc=50.0),
        CashFlowProjection(ebit=1100.0, depreciation=210.0, capex=260.0, delta_nwc=55.0),
        CashFlowProjection(ebit=1200.0, depreciation=220.0, capex=270.0, delta_nwc=60.0),
        CashFlowProjection(ebit=1300.0, depreciation=230.0, capex=280.0, delta_nwc=65.0),
        CashFlowProjection(ebit=1400.0, depreciation=240.0, capex=290.0, delta_nwc=70.0),
    ]
