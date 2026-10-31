"""تست‌های دودی (smoke tests) قابل اجرا از داخل برنامه.

این ماژول خالص است و هیچ وابستگی‌ای به Streamlit ندارد؛ خروجی آن فهرستی از
پیام‌های متنی است که لایه نمایش فقط آن را رندر می‌کند.

برای تست‌های کامل‌تر از `tests/test_valuation_models.py` استفاده کنید.
"""

from typing import List

from .valuation_models import (
    CashFlowProjection,
    DcfScenario,
    constant_growth_model,
    dcf_scenario_valuation,
    dcf_sensitivity,
    dcf_valuation,
    reverse_dcf_implied_growth,
    single_period_model,
    sustainable_growth_valuation,
    wacc,
    zero_growth_model,
)


def run_self_tests() -> List[str]:
    """
    اجرای تست‌های ساده برای توابع محاسباتی

    Returns:
        List[str]: پیام نتیجه هر تست
    """
    test_results = []

    # تست مدل تک‌دوره‌ای
    try:
        result = single_period_model(1.0, 50.0, 0.1)
        expected = 46.36  # تقریبی
        if abs(result - expected) < 0.1:
            test_results.append("✅ مدل تک‌دوره‌ای")
        else:
            test_results.append("❌ مدل تک‌دوره‌ای")
    except Exception:
        test_results.append("❌ مدل تک‌دوره‌ای (خطا)")

    # تست مدل رشد صفر
    try:
        result = zero_growth_model(2.0, 0.08)
        expected = 25.0
        if abs(result - expected) < 0.1:
            test_results.append("✅ مدل رشد صفر")
        else:
            test_results.append("❌ مدل رشد صفر")
    except Exception:
        test_results.append("❌ مدل رشد صفر (خطا)")

    # تست مدل گوردون
    try:
        result = constant_growth_model(1.5, 0.05, 0.12)
        expected = 22.5  # تقریبی
        if abs(result - expected) < 0.1:
            test_results.append("✅ مدل گوردون")
        else:
            test_results.append("❌ مدل گوردون")
    except Exception:
        test_results.append("❌ مدل گوردون (خطا)")

    # تست WACC و یک سال DCF ساده
    try:
        wacc_ok = abs(wacc(600.0, 400.0, 0.12, 0.06, 0.25) - 0.09) < 0.001
        dcf = dcf_valuation(
            [CashFlowProjection(ebit=100.0, depreciation=0.0, capex=0.0, delta_nwc=0.0)],
            0.10,
            0.0,
            1.0,
            0.0,
        )
        dcf_ok = abs(dcf.enterprise_value - 1000.0) < 0.1
        if wacc_ok and dcf_ok:
            test_results.append("✅ مدل WACC و DCF")
        else:
            test_results.append("❌ مدل WACC و DCF")
    except Exception:
        test_results.append("❌ مدل WACC و DCF (خطا)")

    # تست ماتریس حساسیت DCF: سلول مرکز باید برابر حالت پایه باشد
    try:
        projections = [
            CashFlowProjection(ebit=100.0, depreciation=0.0, capex=0.0, delta_nwc=0.0)
            for _ in range(3)
        ]
        base = dcf_valuation(projections, 0.10, 0.02, 10.0, 0.0)
        sensitivity = dcf_sensitivity(projections, 0.10, 0.02, 10.0, 0.0)
        center = sensitivity.value_per_share[sensitivity.base_row][sensitivity.base_col]
        if center == base.value_per_share:
            test_results.append("✅ ماتریس حساسیت DCF")
        else:
            test_results.append("❌ ماتریس حساسیت DCF")
    except Exception:
        test_results.append("❌ ماتریس حساسیت DCF (خطا)")

    # تست DCF معکوس: رفت‌وبرگشت نرخ رشد پایانی
    try:
        projections = [
            CashFlowProjection(ebit=100.0, depreciation=0.0, capex=0.0, delta_nwc=0.0)
            for _ in range(3)
        ]
        market_price = dcf_valuation(projections, 0.10, 0.03, 10.0, 0.0).value_per_share
        reverse = reverse_dcf_implied_growth(projections, 0.10, 10.0, 0.0, market_price)
        if (
            reverse.status == "solved"
            and reverse.implied_growth is not None
            and abs(reverse.implied_growth - 0.03) < 1e-6
        ):
            test_results.append("✅ DCF معکوس")
        else:
            test_results.append("❌ DCF معکوس")
    except Exception:
        test_results.append("❌ DCF معکوس (خطا)")

    # تست میانگین دو سناریوی ساده با ارزش‌های ۱۰۰ و ۲۰۰ برای هر سهم
    try:
        scenarios = [
            DcfScenario("پایه", 0.5, [CashFlowProjection(100.0, 0.0, 0.0, 0.0)], 0.1, 0.0),
            DcfScenario("رشد", 0.5, [CashFlowProjection(200.0, 0.0, 0.0, 0.0)], 0.1, 0.0),
        ]
        result = dcf_scenario_valuation(scenarios, 10.0, 0.0)
        if abs(result.expected_value_per_share - 150.0) < 1e-9:
            test_results.append("✅ سناریوهای وزنی DCF")
        else:
            test_results.append("❌ سناریوهای وزنی DCF")
    except Exception:
        test_results.append("❌ سناریوهای وزنی DCF (خطا)")

    # تست مرجع رشد پایدار و NPVGO
    try:
        result = sustainable_growth_valuation(5.0, 0.12, 0.15, 0.4)
        if abs(result.price - 50.0) < 1e-9:
            test_results.append("✅ رشد پایدار و NPVGO")
        else:
            test_results.append("❌ رشد پایدار و NPVGO")
    except Exception:
        test_results.append("❌ رشد پایدار و NPVGO (خطا)")

    return test_results
