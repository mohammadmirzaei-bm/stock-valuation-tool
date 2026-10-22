"""تنظیمات ظاهری مشترک — چیدمان راست‌به‌چپ (RTL) برای رابط فارسی.

این ماژول فقط به لایه نمایش تعلق دارد و هیچ منطق کسب‌وکاری ندارد. رنگ‌ها،
فونت و شعاع گوشه‌ها از `.streamlit/config.toml` تأمین می‌شوند و این ماژول
تنها جهت‌دهی سراسری عناصر را اعمال می‌کند.
"""

import streamlit as st

RTL_STYLES = """
<style>
/* جهت سراسری راست‌به‌چپ برای بدنه اصلی، نوار کناری و سربرگ */
[data-testid="stAppViewContainer"],
[data-testid="stSidebar"],
[data-testid="stHeader"] {
    direction: rtl;
}

/* تراز راست متن‌ها، برچسب ویجت‌ها و کارت‌های شاخص */
[data-testid="stMarkdownContainer"],
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stWidgetLabel"] p,
[data-testid="stCaptionContainer"],
[data-testid="stMetricLabel"] p,
[data-testid="stMetricValue"] {
    text-align: right;
}

/* ورودی‌های متنی و عددی */
[data-testid="stNumberInput"],
[data-testid="stTextInput"],
[data-testid="stTextArea"] {
    direction: rtl;
}

[data-testid="stNumberInput"] input,
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
    text-align: right;
}

/* گزینه‌های رادیو و چک‌باکس از سمت راست شروع شوند */
[data-testid="stRadio"] [role="radiogroup"] {
    align-items: flex-start;
}

[data-testid="stRadio"] label,
[data-testid="stCheckbox"] label {
    direction: rtl;
}

/* کارت‌های شاخص (KPI) */
[data-testid="stMetric"] {
    direction: rtl;
    text-align: right;
}

[data-testid="stMetricDelta"] {
    flex-direction: row-reverse;
    justify-content: flex-end;
}

/* پیام‌ها، دکمه‌ها و بازشوها */
[data-testid="stAlert"],
[data-testid="stBaseButton-primary"],
[data-testid="stBaseButton-secondary"],
[data-testid="stBaseButton-tertiary"],
[data-testid="stDownloadButton"] button,
[data-testid="stExpander"] summary {
    direction: rtl;
}

/* فرمول‌های ریاضی و جدول داده در جهت طبیعی خود بمانند */
.katex,
[data-testid="stDataFrame"] {
    direction: ltr;
}

/* اسلایدر با محور چپ‌به‌راست طبیعی بماند */
[data-testid="stSlider"] {
    direction: ltr;
}

/* نوار کناری جمع‌شده در چیدمان راست‌به‌چپ
   Streamlit نوار کناری را با translateX برای چیدمان چپ‌به‌راست بیرون می‌برد؛
   وقتی نوار در سمت راست است، این جابه‌جایی آن را داخل کادر دید رها می‌کند و
   نوار باریک متن به‌هم‌ریخته و دستگیره تغییر اندازه وسط صفحه می‌مانند.
   به‌جای visibility از opacity استفاده می‌شود، چون برخی ویجت‌های داخلی
   Streamlit دوباره visibility: visible می‌گیرند. */
[data-testid="stSidebar"][data-collapsed="true"] {
    opacity: 0;
    pointer-events: none;
}

/* فلش‌های باز و بستن نوار کناری در چیدمان راست‌به‌چپ آینه شوند */
[data-testid="stSidebarCollapseButton"] [data-testid="stIconMaterial"],
[data-testid="stExpandSidebarButton"] [data-testid="stIconMaterial"] {
    transform: scaleX(-1);
}
</style>
"""


def apply_rtl_layout() -> None:
    """اعمال چیدمان راست‌به‌چپ روی همه اجزای برنامه"""
    st.html(RTL_STYLES)
