"""نقطه ورود برنامه Streamlit — فقط چیدمان صفحه و مسیریابی.

اجرا:
    streamlit run stock_cla_developed.py

منطق محاسباتی در `stock_valuation/domain/` و مؤلفه‌های نمایشی
در `stock_valuation/ui/` قرار دارند.
"""

import logging

import streamlit as st

from stock_valuation.domain.self_tests import run_self_tests
from stock_valuation.ui import theme, views

# تنظیم لاگ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# تنظیم صفحه
st.set_page_config(
    page_title="ابزار ارزیابی سهام",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# اعمال چیدمان راست‌به‌چپ و تنظیمات ظاهری
theme.apply_rtl_layout()

# عنوان اصلی و منوی کناری
st.title("📈 ابزار پیشرفته ارزیابی سهام")
st.caption("مدل‌های تنزیل سود تقسیمی، سهام ممتاز، فرصت‌های رشد و نسبت PEG")

# نوار کناری
with st.sidebar:
    st.title("🔧 پنل کنترل")

    main_model = st.radio(
        "نوع ارزیابی را انتخاب کنید:",
        [
            "ارزیابی سهام عادی",
            "ارزیابی سهام ممتاز",
            "ارزیابی با فرصت‌های رشد",
            "محاسبه نسبت PEG"
        ]
    )

    # گزینه‌های اضافی
    show_history = st.checkbox("نمایش تاریخچه محاسبات")
    run_tests = st.button("🧪 اجرای تست‌های سیستم")
    st.caption("نسخه 3")

# اجرای تست‌ها
if run_tests:
    with st.expander("نتایج تست‌های سیستم", expanded=True):
        for result in run_self_tests():
            st.write(result)

# بخش اصلی برنامه
if main_model == "ارزیابی سهام عادی":
    views.render_common_stock()
elif main_model == "ارزیابی سهام ممتاز":
    views.render_preferred_stock()
elif main_model == "ارزیابی با فرصت‌های رشد":
    views.render_growth_opportunities()
elif main_model == "محاسبه نسبت PEG":
    views.render_peg_ratio()

# نمایش تاریخچه محاسبات
if show_history:
    views.display_calculation_history()

# پاورقی
st.caption("ابزار پیشرفته ارزیابی سهام · نسخه ۲.۰ · با مدیریت خطا و قابلیت‌های پیشرفته")
