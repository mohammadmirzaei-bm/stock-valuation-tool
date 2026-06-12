import streamlit as st
import math
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import json
from typing import Optional, List, Tuple, Dict, Any
import logging

# تنظیم لاگ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# تنظیم صفحه
st.set_page_config(
    page_title="ابزار ارزیابی سهام",
    page_icon="📈",
    layout="wide"
)

# کلاس مدیریت خطا
class ValidationError(Exception):
    """خطای اعتبارسنجی ورودی"""
    pass

class CalculationError(Exception):
    """خطای محاسباتی"""
    pass

# توابع کمکی برای اعتبارسنجی

def validate_positive_number(value: float, field_name: str) -> None:
    """
    اعتبارسنجی اعداد مثبت
    
    Args:
        value (float): مقدار ورودی
        field_name (str): نام فیلد برای نمایش خطا
        
    Raises:
        ValidationError: اگر مقدار منفی یا صفر باشد
    """
    if value <= 0:
        raise ValidationError(f"❌ {field_name} باید مثبت باشد!")

def validate_percentage(value: float, field_name: str) -> None:
    """
    اعتبارسنجی درصدها (بین 0 و 1)
    
    Args:
        value (float): مقدار درصد (اعشاری)
        field_name (str): نام فیلد
        
    Raises:
        ValidationError: اگر مقدار خارج از بازه معقول باشد
    """
    if not 0 <= value <= 2:  # حداکثر 200% رشد
        raise ValidationError(f"❌ {field_name} باید بین 0 و 2 باشد!")

def validate_growth_rate_vs_return(growth_rate: float, return_rate: float) -> None:
    """
    اعتبارسنجی نرخ رشد در مقایسه با نرخ بازده
    
    Args:
        growth_rate (float): نرخ رشد
        return_rate (float): نرخ بازده
        
    Raises:
        ValidationError: اگر نرخ رشد بیشتر از نرخ بازده باشد
    """
    if growth_rate >= return_rate:
        raise ValidationError(f"❌ نرخ بازده ({return_rate*100:.1f}%) باید بیشتر از نرخ رشد ({growth_rate*100:.1f}%) باشد!")

# توابع محاسباتی با مدیریت خطا و docstring کامل

def single_period_model(d1: float, p1: float, r: float) -> float:
    """
    محاسبه قیمت سهام با مدل تک‌دوره‌ای
    
    فرمول: P₀ = (D₁ + P₁) / (1 + r)
    
    Args:
        d1 (float): سود تقسیمی مورد انتظار در پایان سال
        p1 (float): قیمت مورد انتظار در پایان سال
        r (float): نرخ بازده مورد انتظار (اعشاری)
        
    Returns:
        float: قیمت فعلی سهام
        
    Raises:
        ValidationError: در صورت ورودی نامعتبر
        CalculationError: در صورت خطای محاسباتی
    """
    try:
        validate_positive_number(d1, "سود تقسیمی")
        validate_positive_number(p1, "قیمت مورد انتظار")
        validate_positive_number(r, "نرخ بازده")
        
        result = (d1 + p1) / (1 + r)
        
        if not math.isfinite(result):
            raise CalculationError("نتیجه محاسبه نامعتبر است")
            
        return result
        
    except (ZeroDivisionError, ValueError) as e:
        logger.error(f"خطا در محاسبه مدل تک‌دوره‌ای: {e}")
        raise CalculationError(f"خطا در محاسبه: {str(e)}")

def zero_growth_model(d: float, r: float) -> float:
    """
    محاسبه قیمت سهام با مدل رشد صفر (برای سهام ممتاز یا سهام با سود ثابت)
    
    فرمول: P = D / r
    
    Args:
        d (float): سود تقسیمی ثابت
        r (float): نرخ بازده مورد انتظار (اعشاری)
        
    Returns:
        float: قیمت سهام
        
    Raises:
        ValidationError: در صورت ورودی نامعتبر
        CalculationError: در صورت خطای محاسباتی
    """
    try:
        validate_positive_number(d, "سود تقسیمی")
        validate_positive_number(r, "نرخ بازده")
        
        result = d / r
        
        if not math.isfinite(result):
            raise CalculationError("نتیجه محاسبه نامعتبر است")
            
        return result
        
    except (ZeroDivisionError, ValueError) as e:
        logger.error(f"خطا در محاسبه مدل رشد صفر: {e}")
        raise CalculationError(f"خطا در محاسبه: {str(e)}")

def constant_growth_model(d0: float, g: float, r: float) -> float:
    """
    محاسبه قیمت سهام با مدل رشد ثابت گوردون
    
    فرمول: P = D₁ / (r - g) = D₀(1+g) / (r - g)
    
    Args:
        d0 (float): سود تقسیمی فعلی
        g (float): نرخ رشد ثابت (اعشاری)
        r (float): نرخ بازده مورد انتظار (اعشاری)
        
    Returns:
        float: قیمت سهام
        
    Raises:
        ValidationError: در صورت ورودی نامعتبر
        CalculationError: در صورت خطای محاسباتی
    """
    try:
        validate_positive_number(d0, "سود تقسیمی فعلی")
        validate_percentage(g, "نرخ رشد")
        validate_positive_number(r, "نرخ بازده")
        validate_growth_rate_vs_return(g, r)
        
        d1 = d0 * (1 + g)
        result = d1 / (r - g)
        
        if not math.isfinite(result):
            raise CalculationError("نتیجه محاسبه نامعتبر است")
            
        return result
        
    except (ZeroDivisionError, ValueError) as e:
        logger.error(f"خطا در محاسبه مدل گوردون: {e}")
        raise CalculationError(f"خطا در محاسبه: {str(e)}")

def supernormal_growth_model(d0: float, growth_rates: List[float], years: int, 
                           g_constant: float, r: float) -> Tuple[float, List[float], float]:
    """
    محاسبه قیمت سهام با مدل رشد غیرعادی (دو مرحله‌ای یا چند مرحله‌ای)
    
    فرمول: P₀ = Σ[Dₜ/(1+r)ᵗ] + Pₙ/(1+r)ⁿ
    که Pₙ = Dₙ₊₁ / (r - g_constant)
    
    Args:
        d0 (float): سود تقسیمی فعلی
        growth_rates (List[float]): فهرست نرخ‌های رشد برای دوره غیرعادی
        years (int): تعداد سال‌های دوره غیرعادی
        g_constant (float): نرخ رشد ثابت پس از دوره غیرعادی
        r (float): نرخ بازده مورد انتظار
        
    Returns:
        Tuple[float, List[float], float]: قیمت فعلی، فهرست سودهای تقسیمی، قیمت انتهای دوره
        
    Raises:
        ValidationError: در صورت ورودی نامعتبر
        CalculationError: در صورت خطای محاسباتی
    """
    try:
        validate_positive_number(d0, "سود تقسیمی فعلی")
        validate_positive_number(r, "نرخ بازده")
        validate_percentage(g_constant, "نرخ رشد ثابت")
        validate_growth_rate_vs_return(g_constant, r)
        
        if len(growth_rates) != years:
            raise ValidationError("تعداد نرخ‌های رشد باید با تعداد سال‌ها برابر باشد")
        
        for i, g in enumerate(growth_rates):
            validate_percentage(g, f"نرخ رشد سال {i+1}")
        
        dividends = []
        pv_dividends = []
        current_d = d0
        
        # محاسبه سودهای تقسیمی و ارزش فعلی آنها برای دوره غیرعادی
        for i, g in enumerate(growth_rates):
            current_d = current_d * (1 + g)
            dividends.append(current_d)
            
            # استفاده از math.pow برای قدرت‌گیری
            pv_dividend = current_d / math.pow(1 + r, i + 1)
            pv_dividends.append(pv_dividend)
        
        # محاسبه ارزش انتهای دوره (Terminal Value)
        d_terminal = dividends[-1] * (1 + g_constant)  # سود سال بعد از پایان دوره غیرعادی
        p_terminal = d_terminal / (r - g_constant)  # قیمت انتهای دوره
        
        # ارزش فعلی قیمت انتهای دوره
        pv_p_terminal = p_terminal / math.pow(1 + r, years)
        
        # قیمت فعلی کل
        p0 = sum(pv_dividends) + pv_p_terminal
        
        if not math.isfinite(p0):
            raise CalculationError("نتیجه محاسبه نامعتبر است")
        
        return p0, dividends, p_terminal
        
    except (ZeroDivisionError, ValueError) as e:
        logger.error(f"خطا در محاسبه مدل رشد غیرعادی: {e}")
        raise CalculationError(f"خطا در محاسبه: {str(e)}")

def expected_return(d1: float, p0: float, g: float) -> float:
    """
    محاسبه بازده مورد انتظار سهام
    
    فرمول: r = (D₁/P₀) + g
    
    Args:
        d1 (float): سود تقسیمی مورد انتظار سال آینده
        p0 (float): قیمت فعلی سهام
        g (float): نرخ رشد سود تقسیمی (اعشاری)
        
    Returns:
        float: نرخ بازده مورد انتظار (اعشاری)
        
    Raises:
        ValidationError: در صورت ورودی نامعتبر
        CalculationError: در صورت خطای محاسباتی
    """
    try:
        validate_positive_number(d1, "سود تقسیمی مورد انتظار")
        validate_positive_number(p0, "قیمت فعلی سهام")
        validate_percentage(g, "نرخ رشد")
        
        dividend_yield = d1 / p0
        result = dividend_yield + g
        
        if not math.isfinite(result):
            raise CalculationError("نتیجه محاسبه نامعتبر است")
        
        return result
        
    except (ZeroDivisionError, ValueError) as e:
        logger.error(f"خطا در محاسبه بازده مورد انتظار: {e}")
        raise CalculationError(f"خطا در محاسبه: {str(e)}")

def preferred_stock_valuation(d: float, r: float) -> float:
    """
    محاسبه قیمت سهام ممتاز
    
    فرمول: P = D / r
    سهام ممتاز معمولاً سود تقسیمی ثابت و بی‌نهایت دارند
    
    Args:
        d (float): سود تقسیمی ثابت سالانه
        r (float): نرخ بازده مورد انتظار (اعشاری)
        
    Returns:
        float: قیمت سهام ممتاز
        
    Raises:
        ValidationError: در صورت ورودی نامعتبر
        CalculationError: در صورت خطای محاسباتی
    """
    return zero_growth_model(d, r)  # منطق یکسان با مدل رشد صفر

def growth_opportunities_valuation(eps: float, r: float, npvgo: float) -> Tuple[float, float]:
    """
    محاسبه قیمت سهام با در نظر گیری فرصت‌های رشد
    
    فرمول: P = (EPS/r) + NPVGO
    
    Args:
        eps (float): سود هر سهم
        r (float): نرخ بازده مورد انتظار (اعشاری)
        npvgo (float): ارزش فعلی خالص فرصت‌های رشد
        
    Returns:
        Tuple[float, float]: قیمت کل سهام، ارزش بدون رشد
        
    Raises:
        ValidationError: در صورت ورودی نامعتبر
        CalculationError: در صورت خطای محاسباتی
    """
    try:
        validate_positive_number(eps, "سود هر سهم")
        validate_positive_number(r, "نرخ بازده")
        # NPVGO می‌تواند منفی باشد (فرصت‌های بد)
        
        no_growth_value = eps / r
        total_value = no_growth_value + npvgo
        
        if not math.isfinite(total_value):
            raise CalculationError("نتیجه محاسبه نامعتبر است")
        
        return total_value, no_growth_value
        
    except (ZeroDivisionError, ValueError) as e:
        logger.error(f"خطا در محاسبه ارزیابی با فرصت‌های رشد: {e}")
        raise CalculationError(f"خطا در محاسبه: {str(e)}")

def peg_ratio(pe_ratio: float, growth_rate: float) -> float:
    """
    محاسبه نسبت PEG (Price/Earnings to Growth)
    
    فرمول: PEG = (P/E) / نرخ رشد سالانه سود
    
    Args:
        pe_ratio (float): نسبت P/E
        growth_rate (float): نرخ رشد سالانه سود (درصد)
        
    Returns:
        float: نسبت PEG
        
    Raises:
        ValidationError: در صورت ورودی نامعتبر
        CalculationError: در صورت خطای محاسباتی
    """
    try:
        validate_positive_number(pe_ratio, "نسبت P/E")
        validate_positive_number(growth_rate, "نرخ رشد سود")
        
        if growth_rate > 100:
            raise ValidationError("نرخ رشد بیش از 100% غیرمنطقی است!")
        
        result = pe_ratio / growth_rate
        
        if not math.isfinite(result):
            raise CalculationError("نتیجه محاسبه نامعتبر است")
        
        return result
        
    except (ZeroDivisionError, ValueError) as e:
        logger.error(f"خطا در محاسبه نسبت PEG: {e}")
        raise CalculationError(f"خطا در محاسبه: {str(e)}")

# توابع کمکی برای UI

def save_calculation_results(model_name: str, inputs: Dict[str, Any], results: Dict[str, Any]) -> None:
    """
    ذخیره‌سازی نتایج محاسبات برای دانلود
    
    Args:
        model_name (str): نام مدل
        inputs (Dict[str, Any]): پارامترهای ورودی
        results (Dict[str, Any]): نتایج محاسبه
    """
    try:
        if 'calculation_history' not in st.session_state:
            st.session_state.calculation_history = []
        
        calculation_record = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'model': model_name,
            'inputs': inputs,
            'results': results
        }
        
        st.session_state.calculation_history.append(calculation_record)
        
    except Exception as e:
        logger.error(f"خطا در ذخیره‌سازی نتایج: {e}")

def create_comparison_chart(values: List[float], labels: List[str], title: str) -> go.Figure:
    """
    ایجاد نمودار مقایسه‌ای
    
    Args:
        values (List[float]): مقادیر
        labels (List[str]): برچسب‌ها
        title (str): عنوان نمودار
        
    Returns:
        go.Figure: نمودار plotly
    """
    fig = go.Figure(data=[
        go.Bar(
            x=labels,
            y=values,
            marker_color='rgba(55, 128, 191, 0.7)',
            marker_line_color='rgba(55, 128, 191, 1)',
            marker_line_width=2
        )
    ])
    
    fig.update_layout(
        title=title,
        xaxis_title="اجزاء",
        yaxis_title="مقدار ($)",
        font=dict(family="Arial", size=12),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

def display_calculation_history():
    """نمایش تاریخچه محاسبات"""
    if 'calculation_history' in st.session_state and st.session_state.calculation_history:
        st.subheader("📋 تاریخچه محاسبات")
        
        df_history = pd.DataFrame(st.session_state.calculation_history)
        st.dataframe(df_history[['timestamp', 'model']], use_container_width=True)
        
        # دانلود تاریخچه
        json_history = json.dumps(st.session_state.calculation_history, 
                                indent=2, ensure_ascii=False)
        st.download_button(
            label="📥 دانلود تاریخچه محاسبات",
            data=json_history,
            file_name=f"stock_valuation_history_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )

# تست‌های Unit (برای اعتبارسنجی)
def run_unit_tests():
    """اجرای تست‌های unit برای توابع محاسباتی"""
    test_results = []
    
    try:
        # تست مدل تک‌دوره‌ای
        result = single_period_model(1.0, 50.0, 0.1)
        expected = 46.36  # تقریبی
        if abs(result - expected) < 0.1:
            test_results.append("✅ مدل تک‌دوره‌ای")
        else:
            test_results.append("❌ مدل تک‌دوره‌ای")
    except Exception:
        test_results.append("❌ مدل تک‌دوره‌ای (خطا)")
    
    try:
        # تست مدل رشد صفر
        result = zero_growth_model(2.0, 0.08)
        expected = 25.0
        if abs(result - expected) < 0.1:
            test_results.append("✅ مدل رشد صفر")
        else:
            test_results.append("❌ مدل رشد صفر")
    except Exception:
        test_results.append("❌ مدل رشد صفر (خطا)")
    
    try:
        # تست مدل گوردون
        result = constant_growth_model(1.5, 0.05, 0.12)
        expected = 22.5  # تقریبی
        if abs(result - expected) < 0.1:
            test_results.append("✅ مدل گوردون")
        else:
            test_results.append("❌ مدل گوردون")
    except Exception:
        test_results.append("❌ مدل گوردون (خطا)")
    
    return test_results

# عنوان اصلی و منوی کناری
st.title("📈 ابزار پیشرفته ارزیابی سهام")
st.markdown("---")

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
    
    st.markdown("---")
    
    # گزینه‌های اضافی
    show_history = st.checkbox("نمایش تاریخچه محاسبات")
    run_tests = st.button("🧪 اجرای تست‌های سیستم")

# اجرای تست‌ها
if run_tests:
    with st.expander("نتایج تست‌های سیستم", expanded=True):
        test_results = run_unit_tests()
        for result in test_results:
            st.write(result)

# بخش اصلی برنامه
if main_model == "ارزیابی سهام عادی":
    st.header("📊 ارزیابی سهام عادی")
    
    sub_model = st.radio(
        "مدل محاسبه را انتخاب کنید:",
        [
            "مدل تک‌دوره‌ای",
            "مدل رشد صفر",
            "مدل رشد ثابت (گوردون)",
            "مدل رشد غیرعادی",
            "محاسبه بازده مورد انتظار"
        ]
    )
    
    if sub_model == "مدل تک‌دوره‌ای":
        st.subheader("🔹 مدل تک‌دوره‌ای")
        st.latex(r"P_0 = \frac{D_1 + P_1}{1 + r}")
        
        col1, col2 = st.columns(2)
        with col1:
            d1 = st.number_input("سود تقسیمی مورد انتظار در پایان سال ($):", 
                               value=1.0, min_value=0.01, step=0.01)
            p1 = st.number_input("قیمت مورد انتظار در پایان سال ($):", 
                               value=50.0, min_value=0.01, step=0.01)
            r = st.number_input("نرخ بازده مورد انتظار (اعشار):", 
                              value=0.10, min_value=0.001, max_value=0.99, 
                              step=0.001, format="%.4f")
        
        with col2:
            if st.button("محاسبه", key="single"):
                try:
                    p0 = single_period_model(d1, p1, r)
                    st.success(f"**قیمت فعلی سهام:** ${p0:.2f}")
                    
                    # ذخیره‌سازی نتایج
                    save_calculation_results(
                        "مدل تک‌دوره‌ای",
                        {"D1": d1, "P1": p1, "r": r},
                        {"P0": p0}
                    )
                    
                    # نمودار تجزیه ارزش
                    fig = create_comparison_chart(
                        [d1, p1/(1+r), p0],
                        ["سود تقسیمی", "ارزش فعلی قیمت آینده", "کل ارزش"],
                        "تجزیه ارزش سهام"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.info("این مدل برای سرمایه‌گذاران کوتاه‌مدت (یک سال) مناسب است.")
                    
                except (ValidationError, CalculationError) as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"خطای غیرمنتظره: {str(e)}")
                    logger.error(f"خطای غیرمنتظره در مدل تک‌دوره‌ای: {e}")
    
    elif sub_model == "مدل رشد صفر":
        st.subheader("🔹 مدل رشد صفر")
        st.latex(r"P = \frac{D}{r}")
        
        col1, col2 = st.columns(2)
        with col1:
            d = st.number_input("سود تقسیمی ثابت در هر دوره ($):", 
                              value=2.0, min_value=0.01, step=0.01)
            r = st.number_input("نرخ بازده مورد انتظار (اعشار):", 
                              value=0.08, min_value=0.001, max_value=0.99, 
                              step=0.001, format="%.4f")
        
        with col2:
            if st.button("محاسبه", key="zero"):
                try:
                    p = zero_growth_model(d, r)
                    st.success(f"**قیمت سهام:** ${p:.2f}")
                    
                    # ذخیره‌سازی نتایج
                    save_calculation_results(
                        "مدل رشد صفر",
                        {"D": d, "r": r},
                        {"P": p}
                    )
                    
                    # نمایش اطلاعات تکمیلی
                    annual_yield = (d / p) * 100
                    st.info(f"بازده سالانه: {annual_yield:.2f}%")
                    st.info("این مدل فرض می‌کند سود تقسیمی تا ابد ثابت باقی می‌ماند.")
                    
                except (ValidationError, CalculationError) as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"خطای غیرمنتظره: {str(e)}")
                    logger.error(f"خطای غیرمنتظره در مدل رشد صفر: {e}")
    
    elif sub_model == "مدل رشد ثابت (گوردون)":
        st.subheader("🔹 مدل رشد ثابت گوردون")
        st.latex(r"P = \frac{D_1}{r - g} = \frac{D_0(1+g)}{r - g}")
        
        col1, col2 = st.columns(2)
        with col1:
            d0 = st.number_input("سود تقسیمی فعلی ($):", 
                               value=1.5, min_value=0.01, step=0.01)
            g = st.number_input("نرخ رشد ثابت (اعشار):", 
                              value=0.05, min_value=0.0, max_value=0.95, 
                              step=0.001, format="%.4f")
            r = st.number_input("نرخ بازده مورد انتظار (اعشار):", 
                              value=0.12, min_value=0.001, max_value=0.99, 
                              step=0.001, format="%.4f")
        
        with col2:
            if st.button("محاسبه", key="gordon"):
                try:
                    p = constant_growth_model(d0, g, r)
                    d1 = d0 * (1 + g)
                    
                    st.success(f"**قیمت سهام:** ${p:.2f}")
                    
                    # ذخیره‌سازی نتایج
                    save_calculation_results(
                        "مدل گوردون",
                        {"D0": d0, "g": g, "r": r},
                        {"P": p, "D1": d1}
                    )
                    
                    # اطلاعات تکمیلی
                    st.info(f"سود تقسیمی سال آینده: ${d1:.2f}")
                    st.info(f"بازده سود تقسیمی: {(d1/p)*100:.2f}%")
                    st.info(f"بازده رشد سرمایه: {g*100:.2f}%")
                    
                    # نمودار پیش‌بینی سود تقسیمی
                    years = list(range(1, 11))
                    future_dividends = [d0 * math.pow(1 + g, year) for year in years]
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=years, y=future_dividends,
                        mode='lines+markers',
                        name='سود تقسیمی پیش‌بینی شده',
                        line=dict(color='blue', width=2)
                    ))
                    fig.update_layout(
                        title="پیش‌بینی سود تقسیمی ۱۰ سال آینده",
                        xaxis_title="سال",
                        yaxis_title="سود تقسیمی ($)"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                except (ValidationError, CalculationError) as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"خطای غیرمنتظره: {str(e)}")
                    logger.error(f"خطای غیرمنتظره در مدل گوردون: {e}")
    
    elif sub_model == "مدل رشد غیرعادی":
        st.subheader("🔹 مدل رشد غیرعادی")
        st.latex(r"P_0 = \sum_{t=1}^{n} \frac{D_t}{(1+r)^t} + \frac{P_n}{(1+r)^n}")
        
        col1, col2 = st.columns(2)
        with col1:
            d0 = st.number_input("سود تقسیمی فعلی ($):", 
                               value=1.0, min_value=0.01, step=0.01)
            years = st.number_input("تعداد سال‌های رشد غیرعادی:", 
                                  value=3, min_value=1, max_value=10)
            
            # ورودی‌های پویا برای نرخ‌های رشد
            growth_rates = []
            st.write("**نرخ‌های رشد سالانه:**")
            for i in range(int(years)):
                g_year = st.number_input(
                    f"سال {i+1} (اعشار):",
                    value=max(0.05, 0.25 - (i * 0.05)),
                    min_value=0.0,
                    max_value=2.0,
                    step=0.001,
                    format="%.4f",
                    key=f"g_{i}"
                )
                growth_rates.append(g_year)
            
            g_constant = st.number_input("نرخ رشد ثابت پس از دوره غیرعادی (اعشار):", 
                                       value=0.05, min_value=0.0, max_value=0.95, 
                                       step=0.001, format="%.4f")
            r = st.number_input("نرخ بازده مورد انتظار (اعشار):", 
                              value=0.12, min_value=0.001, max_value=0.99, 
                              step=0.001, format="%.4f")
        
        with col2:
            if st.button("محاسبه", key="supernormal"):
                try:
                    p0, dividends, p_terminal = supernormal_growth_model(
                        d0, growth_rates, int(years), g_constant, r
                    )
                    
                    st.success(f"**قیمت فعلی سهام:** ${p0:.2f}")
                    
                    # ذخیره‌سازی نتایج
                    save_calculation_results(
                        "مدل رشد غیرعادی",
                        {"D0": d0, "growth_rates": growth_rates, "years": years, 
                         "g_constant": g_constant, "r": r},
                        {"P0": p0, "dividends": dividends, "P_terminal": p_terminal}
                    )
                    
                    # نمایش جزئیات
                    st.write("**📋 جزئیات محاسبه:**")
                    
                    details_data = []
                    current_d = d0
                    total_pv_dividends = 0
                    
                    for i, (g, div) in enumerate(zip(growth_rates, dividends)):
                        pv_div = div / math.pow(1 + r, i + 1)
                        total_pv_dividends += pv_div
                        details_data.append({
                            'سال': f"{i+1}",
                            'نرخ رشد': f"{g*100:.1f}%",
                            'سود تقسیمی': f"${div:.2f}",
                            'ارزش فعلی': f"${pv_div:.2f}"
                        })
                    
                    # اضافه کردن ارزش انتهای دوره
                    pv_terminal = p_terminal / math.pow(1 + r, years)
                    details_data.append({
                        'سال': 'انتهای دوره',
                        'نرخ رشد': f"{g_constant*100:.1f}%",
                        'سود تقسیمی': f"${p_terminal:.2f}",
                        'ارزش فعلی': f"${pv_terminal:.2f}"
                    })
                    
                    df_details = pd.DataFrame(details_data)
                    st.dataframe(df_details, use_container_width=True)
                    
                    # نمودار تجزیه ارزش
                    values = [total_pv_dividends, pv_terminal]
                    labels = ['ارزش فعلی سودهای دوره غیرعادی', 'ارزش فعلی قیمت انتهای دوره']
                    
                    fig = create_comparison_chart(values, labels, "تجزیه ارزش سهام")
                    st.plotly_chart(fig, use_container_width=True)
                    
                except (ValidationError, CalculationError) as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"خطای غیرمنتظره: {str(e)}")
                    logger.error(f"خطای غیرمنتظره در مدل رشد غیرعادی: {e}")
    
    elif sub_model == "محاسبه بازده مورد انتظار":
        st.subheader("🔹 محاسبه بازده مورد انتظار")
        st.latex(r"r = \frac{D_1}{P_0} + g")
        
        col1, col2 = st.columns(2)
        with col1:
            d1 = st.number_input("سود تقسیمی مورد انتظار سال آینده ($):", 
                               value=1.0, min_value=0.01, step=0.01)
            p0 = st.number_input("قیمت فعلی سهام ($):", 
                               value=20.0, min_value=0.01, step=0.01)
            g = st.number_input("نرخ رشد سود تقسیمی (اعشار):", 
                              value=0.10, min_value=0.0, max_value=2.0, 
                              step=0.001, format="%.4f")
        
        with col2:
            if st.button("محاسبه", key="expected_return"):
                try:
                    r = expected_return(d1, p0, g)
                    dividend_yield = d1 / p0
                    
                    st.success(f"**بازده مورد انتظار:** {r*100:.2f}%")
                    
                    # ذخیره‌سازی نتایج
                    save_calculation_results(
                        "بازده مورد انتظار",
                        {"D1": d1, "P0": p0, "g": g},
                        {"r": r, "dividend_yield": dividend_yield}
                    )
                    
                    # تجزیه بازده
                    st.info(f"• بازده سود تقسیمی: {dividend_yield*100:.2f}%")
                    st.info(f"• بازده رشد سرمایه: {g*100:.2f}%")
                    
                    # نمودار تجزیه بازده
                    fig = create_comparison_chart(
                        [dividend_yield*100, g*100, r*100],
                        ['بازده سود تقسیمی', 'بازده رشد سرمایه', 'کل بازده مورد انتظار'],
                        "تجزیه بازده مورد انتظار (%)"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                except (ValidationError, CalculationError) as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"خطای غیرمنتظره: {str(e)}")
                    logger.error(f"خطای غیرمنتظره در محاسبه بازده مورد انتظار: {e}")

elif main_model == "ارزیابی سهام ممتاز":
    st.header("💎 ارزیابی سهام ممتاز")
    st.latex(r"P = \frac{D}{r}")
    
    col1, col2 = st.columns(2)
    with col1:
        d = st.number_input("سود تقسیمی ثابت سالانه ($):", 
                          value=2.25, min_value=0.01, step=0.01)
        r = st.number_input("نرخ بازده مورد انتظار (اعشار):", 
                          value=0.09, min_value=0.001, max_value=0.99, 
                          step=0.001, format="%.4f")
    
    with col2:
        if st.button("محاسبه", key="preferred"):
            try:
                p = preferred_stock_valuation(d, r)
                
                st.success(f"**قیمت سهام ممتاز:** ${p:.2f}")
                
                # ذخیره‌سازی نتایج
                save_calculation_results(
                    "ارزیابی سهام ممتاز",
                    {"D": d, "r": r},
                    {"P": p}
                )
                
                # اطلاعات تکمیلی
                annual_yield = (d / p) * 100
                st.info(f"بازده سالانه: {annual_yield:.2f}%")
                st.info("سهام ممتاز معمولاً سود تقسیمی ثابت و اولویت در پرداخت دارند.")
                
                # مقایسه با سایر سرمایه‌گذاری‌ها
                bond_equivalent = st.slider("نرخ اوراق قرضه مشابه برای مقایسه (%):", 
                                           1.0, 15.0, 8.0, 0.1)
                bond_equiv_decimal = bond_equivalent / 100
                
                if r > bond_equiv_decimal:
                    risk_premium = (r - bond_equiv_decimal) * 100
                    st.info(f"حق‌الریسک در مقایسه با اوراق قرضه: {risk_premium:.2f}%")
                
            except (ValidationError, CalculationError) as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"خطای غیرمنتظره: {str(e)}")
                logger.error(f"خطای غیرمنتظره در ارزیابی سهام ممتاز: {e}")

elif main_model == "ارزیابی با فرصت‌های رشد":
    st.header("🚀 ارزیابی با فرصت‌های رشد")
    st.latex(r"P = \frac{EPS}{r} + NPVGO")
    
    col1, col2 = st.columns(2)
    with col1:
        eps = st.number_input("سود هر سهم ($):", 
                            value=3.0, min_value=0.01, step=0.01)
        r = st.number_input("نرخ بازده مورد انتظار (اعشار):", 
                          value=0.10, min_value=0.001, max_value=0.99, 
                          step=0.001, format="%.4f")
        npvgo = st.number_input("ارزش فعلی فرصت‌های رشد ($):", 
                              value=5.0, step=0.01)
    
    with col2:
        if st.button("محاسبه", key="growth_opp"):
            try:
                p, no_growth_value = growth_opportunities_valuation(eps, r, npvgo)
                
                st.success(f"**قیمت کل سهام:** ${p:.2f}")
                
                # ذخیره‌سازی نتایج
                save_calculation_results(
                    "ارزیابی با فرصت‌های رشد",
                    {"EPS": eps, "r": r, "NPVGO": npvgo},
                    {"P": p, "no_growth_value": no_growth_value}
                )
                
                # تجزیه ارزش
                st.info(f"• ارزش بدون رشد: ${no_growth_value:.2f}")
                st.info(f"• ارزش فرصت‌های رشد: ${npvgo:.2f}")
                
                growth_contribution = (npvgo / p) * 100 if p != 0 else 0
                st.info(f"• سهم فرصت‌های رشد از کل ارزش: {growth_contribution:.1f}%")
                
                # نمودار تجزیه ارزش
                values = [no_growth_value, npvgo]
                labels = ['ارزش بدون رشد', 'فرصت‌های رشد']
                colors = ['rgba(55, 128, 191, 0.7)', 'rgba(255, 193, 7, 0.7)']
                
                fig = go.Figure(data=[
                    go.Bar(x=labels, y=values, marker_color=colors)
                ])
                fig.update_layout(
                    title="تجزیه ارزش سهام",
                    xaxis_title="اجزاء ارزش",
                    yaxis_title="مقدار ($)"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # نمودار دایره‌ای
                fig_pie = go.Figure(data=[
                    go.Pie(labels=labels, values=[abs(v) for v in values], hole=.3)
                ])
                fig_pie.update_layout(title="توزیع ارزش سهام")
                st.plotly_chart(fig_pie, use_container_width=True)
                
            except (ValidationError, CalculationError) as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"خطای غیرمنتظره: {str(e)}")
                logger.error(f"خطای غیرمنتظره در ارزیابی با فرصت‌های رشد: {e}")

elif main_model == "محاسبه نسبت PEG":
    st.header("📊 محاسبه نسبت PEG")
    st.latex(r"PEG = \frac{P/E}{\text{نرخ رشد سالانه سود}}")
    
    col1, col2 = st.columns(2)
    with col1:
        pe_ratio = st.number_input("نسبت P/E:", 
                                 value=15.0, min_value=0.1, step=0.1)
        growth_rate = st.number_input("نرخ رشد سالانه سود (درصد):", 
                                    value=10.0, min_value=0.1, max_value=100.0, step=0.1)
    
    with col2:
        if st.button("محاسبه", key="peg"):
            try:
                peg = peg_ratio(pe_ratio, growth_rate)
                
                st.success(f"**نسبت PEG:** {peg:.2f}")
                
                # ذخیره‌سازی نتایج
                save_calculation_results(
                    "نسبت PEG",
                    {"PE_ratio": pe_ratio, "growth_rate": growth_rate},
                    {"PEG": peg}
                )
                
                # تفسیر نسبت PEG
                if peg < 0.5:
                    st.success("🟢 نسبت PEG خیلی کم: احتمالاً سهم بسیار کم‌ارزش است")
                elif peg < 1:
                    st.info("🟡 نسبت PEG کمتر از 1: احتمالاً سهم کم‌ارزش است")
                elif peg == 1:
                    st.info("⚖️ نسبت PEG برابر 1: سهم منصفانه قیمت‌گذاری شده")
                elif peg < 1.5:
                    st.warning("🟠 نسبت PEG بین 1-1.5: قیمت‌گذاری نزدیک به منصفانه")
                else:
                    st.error("🔴 نسبت PEG بیشتر از 1.5: احتمالاً سهم بیش‌ارزش است")
                
                # نمودار مقایسه‌ای
                benchmark_pegs = [0.5, 1.0, 1.5, 2.0]
                benchmark_labels = ['کم‌ارزش قوی', 'منصفانه', 'نزدیک به بیش‌ارزش', 'بیش‌ارزش قوی']
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=benchmark_pegs, y=[1]*len(benchmark_pegs),
                    mode='markers', name='معیارهای مرجع',
                    marker=dict(size=10, color='lightblue')
                ))
                fig.add_trace(go.Scatter(
                    x=[peg], y=[1], mode='markers', name='نسبت محاسبه شده',
                    marker=dict(size=15, color='red', symbol='diamond')
                ))
                
                for i, (peg_val, label) in enumerate(zip(benchmark_pegs, benchmark_labels)):
                    fig.add_annotation(
                        x=peg_val, y=1.05, text=label,
                        showarrow=False, textangle=-45
                    )
                
                fig.update_layout(
                    title="موقعیت نسبت PEG محاسبه شده",
                    xaxis_title="نسبت PEG",
                    yaxis=dict(showticklabels=False, range=[0.8, 1.2]),
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # راهنمای تفسیر
                with st.expander("📖 راهنمای تفسیر نسبت PEG"):
                    st.markdown("""
                    **راهنمای کامل تفسیر نسبت PEG:**
                    
                    - **کمتر از 0.5:** سهم احتمالاً بسیار کم‌ارزش است
                    - **0.5 تا 1:** سهم ممکن است کم‌ارزش باشد  
                    - **برابر 1:** قیمت‌گذاری منصفانه و متعادل
                    - **1 تا 1.5:** قیمت‌گذاری نسبتاً منصفانه اما نزدیک به بالا
                    - **بیشتر از 1.5:** سهم احتمالاً بیش‌ارزش است
                    - **بیشتر از 2:** سهم احتمالاً بسیار بیش‌ارزش است
                    
                    **نکات مهم:**
                    - این نسبت برای مقایسه شرکت‌هایی با رشد مشابه مفید است
                    - برای شرکت‌های با رشد منفی قابل اعتماد نیست
                    - باید در کنار سایر نسبت‌های مالی بررسی شود
                    - صنعت و شرایط بازار نیز تأثیرگذار است
                    """)
                
            except (ValidationError, CalculationError) as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"خطای غیرمنتظره: {str(e)}")
                logger.error(f"خطای غیرمنتظره در محاسبه نسبت PEG: {e}")

# نمایش تاریخچه محاسبات
if show_history:
    st.markdown("---")
    display_calculation_history()

# پاورقی
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666666; font-size: 0.8em;'>
        🔧 ابزار پیشرفته ارزیابی سهام | نسخه 2.0 | با مدیریت خطا و قابلیت‌های پیشرفته
    </div>
    """, 
    unsafe_allow_html=True
)
