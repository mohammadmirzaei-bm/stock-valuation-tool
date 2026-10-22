"""تست‌های دودی (smoke tests) قابل اجرا از داخل برنامه.

این ماژول خالص است و هیچ وابستگی‌ای به Streamlit ندارد؛ خروجی آن فهرستی از
پیام‌های متنی است که لایه نمایش فقط آن را رندر می‌کند.

برای تست‌های کامل‌تر از `tests/test_valuation_models.py` استفاده کنید.
"""

from typing import List

from .valuation_models import (
    constant_growth_model,
    single_period_model,
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

    return test_results
