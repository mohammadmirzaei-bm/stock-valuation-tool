"""لایه نمایش — ویجت‌های Streamlit، رندر نتایج و مدیریت وضعیت نمایش.

هیچ فرمول یا قاعده کسب‌وکاری در این ماژول وجود ندارد؛ همه محاسبات از
ماژول‌های `stock_valuation.domain` تأمین می‌شوند.

وضعیت نگهداری‌شده در این لایه فقط شامل تاریخچه محاسبات (session state) و
ورودی‌های ویجت‌هاست.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Tuple

import pandas as pd
import streamlit as st

from ..domain.errors import CalculationError, ValidationError
from ..domain.valuation_models import (
    annual_dividend_yield_percent,
    capm_breakdown,
    expected_return_breakdown,
    gordon_breakdown,
    growth_opportunities_breakdown,
    interpret_peg,
    peg_ratio,
    preferred_stock_valuation,
    project_dividends,
    risk_premium_percent,
    single_period_decomposition,
    supernormal_growth_model,
    supernormal_schedule,
    zero_growth_model,
)
from . import charts

logger = logging.getLogger(__name__)

# نگاشت سطح پیام دامنه به ویجت نمایشی
_PEG_LEVEL_RENDERERS = {
    "success": st.success,
    "info": st.info,
    "warning": st.warning,
    "error": st.error,
}


def render_metrics_row(metrics: List[Tuple[str, str]]) -> None:
    """
    نمایش نتایج کلیدی به صورت ردیف کارت‌های شاخص (KPI)

    Args:
        metrics (List[Tuple[str, str]]): زوج‌های (برچسب، مقدار) برای نمایش
    """
    columns = st.columns(len(metrics))
    for column, (label, value) in zip(columns, metrics):
        with column:
            st.metric(label, value)


def save_calculation_results(model_name: str, inputs: Dict[str, Any],
                             results: Dict[str, Any]) -> None:
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


def display_calculation_history() -> None:
    """نمایش تاریخچه محاسبات"""
    if 'calculation_history' in st.session_state and st.session_state.calculation_history:
        st.subheader("📋 تاریخچه محاسبات")

        df_history = pd.DataFrame(st.session_state.calculation_history)
        st.dataframe(df_history[['timestamp', 'model']], hide_index=True)

        # دانلود تاریخچه
        json_history = json.dumps(st.session_state.calculation_history,
                                  indent=2, ensure_ascii=False)
        st.download_button(
            label="📥 دانلود تاریخچه محاسبات",
            data=json_history,
            file_name=f"stock_valuation_history_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )


# ---------------------------------------------------------------------------
# مدل‌های سهام عادی
# ---------------------------------------------------------------------------

def render_single_period() -> None:
    """رندر مدل تک‌دوره‌ای"""
    st.subheader("🔹 مدل تک‌دوره‌ای")
    st.latex(r"P_0 = \frac{D_1 + P_1}{1 + r}")

    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            d1 = st.number_input("سود تقسیمی مورد انتظار در پایان سال ($):",
                                 value=1.0, min_value=0.01, step=0.01)
            p1 = st.number_input("قیمت مورد انتظار در پایان سال ($):",
                                 value=50.0, min_value=0.01, step=0.01)
        with col2:
            r = st.number_input("نرخ بازده مورد انتظار (اعشار):",
                                value=0.10, min_value=0.001, max_value=0.99,
                                step=0.001, format="%.4f")

        calculate = st.button("محاسبه", key="single", type="primary")

    if calculate:
        try:
            decomposition = single_period_decomposition(d1, p1, r)

            # ذخیره‌سازی نتایج
            save_calculation_results(
                "مدل تک‌دوره‌ای",
                {"D1": d1, "P1": p1, "r": r},
                {"P0": decomposition.p0}
            )

            with st.container(border=True):
                render_metrics_row([
                    ("قیمت فعلی سهام", f"${decomposition.p0:,.2f}"),
                    ("ارزش فعلی سود تقسیمی", f"${decomposition.pv_dividend:,.2f}"),
                    ("ارزش فعلی قیمت آینده", f"${decomposition.pv_terminal_price:,.2f}"),
                ])

                # نمودار تجزیه ارزش (هر دو جزء تنزیل می‌شوند تا جمعشان برابر P₀ باشد)
                fig = charts.create_comparison_chart(
                    [decomposition.pv_dividend, decomposition.pv_terminal_price,
                     decomposition.p0],
                    ["ارزش فعلی سود تقسیمی", "ارزش فعلی قیمت آینده", "کل ارزش"],
                    "تجزیه ارزش سهام"
                )
                st.plotly_chart(fig)

            st.caption("این مدل برای سرمایه‌گذاران کوتاه‌مدت (یک سال) مناسب است.")

        except (ValidationError, CalculationError) as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"خطای غیرمنتظره: {str(e)}")
            logger.error(f"خطای غیرمنتظره در مدل تک‌دوره‌ای: {e}")


def render_zero_growth() -> None:
    """رندر مدل رشد صفر"""
    st.subheader("🔹 مدل رشد صفر")
    st.latex(r"P = \frac{D}{r}")

    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            d = st.number_input("سود تقسیمی ثابت در هر دوره ($):",
                                value=2.0, min_value=0.01, step=0.01)
        with col2:
            r = st.number_input("نرخ بازده مورد انتظار (اعشار):",
                                value=0.08, min_value=0.001, max_value=0.99,
                                step=0.001, format="%.4f")

        calculate = st.button("محاسبه", key="zero", type="primary")

    if calculate:
        try:
            p = zero_growth_model(d, r)

            # ذخیره‌سازی نتایج
            save_calculation_results(
                "مدل رشد صفر",
                {"D": d, "r": r},
                {"P": p}
            )

            with st.container(border=True):
                annual_yield = annual_dividend_yield_percent(d, p)
                render_metrics_row([
                    ("قیمت سهام", f"${p:,.2f}"),
                    ("بازده سالانه سود تقسیمی", f"{annual_yield:.2f}%"),
                ])

            st.caption("این مدل فرض می‌کند سود تقسیمی تا ابد ثابت باقی می‌ماند.")

        except (ValidationError, CalculationError) as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"خطای غیرمنتظره: {str(e)}")
            logger.error(f"خطای غیرمنتظره در مدل رشد صفر: {e}")


def render_constant_growth() -> None:
    """رندر مدل رشد ثابت گوردون"""
    st.subheader("🔹 مدل رشد ثابت گوردون")
    st.latex(r"P = \frac{D_1}{r - g} = \frac{D_0(1+g)}{r - g}")

    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            d0 = st.number_input("سود تقسیمی فعلی ($):",
                                 value=1.5, min_value=0.01, step=0.01)
            g = st.number_input("نرخ رشد ثابت (اعشار):",
                                value=0.05, min_value=0.0, max_value=0.95,
                                step=0.001, format="%.4f")
        with col2:
            r = st.number_input("نرخ بازده مورد انتظار (اعشار):",
                                value=0.12, min_value=0.001, max_value=0.99,
                                step=0.001, format="%.4f")

        calculate = st.button("محاسبه", key="gordon", type="primary")

    if calculate:
        try:
            breakdown = gordon_breakdown(d0, g, r)

            # ذخیره‌سازی نتایج
            save_calculation_results(
                "مدل گوردون",
                {"D0": d0, "g": g, "r": r},
                {"P": breakdown.price, "D1": breakdown.d1}
            )

            with st.container(border=True):
                render_metrics_row([
                    ("قیمت سهام", f"${breakdown.price:,.2f}"),
                    ("سود تقسیمی سال آینده", f"${breakdown.d1:,.2f}"),
                    ("بازده سود تقسیمی", f"{breakdown.dividend_yield_percent:.2f}%"),
                    ("بازده رشد سرمایه", f"{breakdown.capital_gains_yield_percent:.2f}%"),
                ])

                # نمودار پیش‌بینی سود تقسیمی
                future_dividends = project_dividends(d0, g, periods=10)
                fig = charts.create_dividend_forecast_chart(future_dividends)
                st.plotly_chart(fig)

        except (ValidationError, CalculationError) as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"خطای غیرمنتظره: {str(e)}")
            logger.error(f"خطای غیرمنتظره در مدل گوردون: {e}")


def render_supernormal_growth() -> None:
    """رندر مدل رشد غیرعادی"""
    st.subheader("🔹 مدل رشد غیرعادی")
    st.latex(r"P_0 = \sum_{t=1}^{n} \frac{D_t}{(1+r)^t} + \frac{P_n}{(1+r)^n}")

    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            d0 = st.number_input("سود تقسیمی فعلی ($):",
                                 value=1.0, min_value=0.01, step=0.01)
            years = st.number_input("تعداد سال‌های رشد غیرعادی:",
                                    value=3, min_value=1, max_value=10)
        with col2:
            g_constant = st.number_input("نرخ رشد ثابت پس از دوره غیرعادی (اعشار):",
                                         value=0.05, min_value=0.0, max_value=0.95,
                                         step=0.001, format="%.4f")
            r = st.number_input("نرخ بازده مورد انتظار (اعشار):",
                                value=0.12, min_value=0.001, max_value=0.99,
                                step=0.001, format="%.4f")

        # ورودی‌های پویا برای نرخ‌های رشد
        st.markdown("**نرخ‌های رشد سالانه:**")
        growth_rates = []
        rate_columns = st.columns(3)
        for i in range(int(years)):
            with rate_columns[i % 3]:
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

        calculate = st.button("محاسبه", key="supernormal", type="primary")

    if calculate:
        try:
            result = supernormal_growth_model(
                d0, growth_rates, int(years), g_constant, r
            )

            # ذخیره‌سازی نتایج
            save_calculation_results(
                "مدل رشد غیرعادی",
                {"D0": d0, "growth_rates": growth_rates, "years": years,
                 "g_constant": g_constant, "r": r},
                {"P0": result.p0, "dividends": result.dividends,
                 "P_terminal": result.p_terminal}
            )

            with st.container(border=True):
                render_metrics_row([
                    ("قیمت فعلی سهام", f"${result.p0:,.2f}"),
                    ("قیمت انتهای دوره (Pₙ)", f"${result.p_terminal:,.2f}"),
                    ("ارزش فعلی سودهای تقسیمی", f"${result.pv_dividends_total:,.2f}"),
                    ("ارزش فعلی قیمت انتهای دوره", f"${result.pv_p_terminal:,.2f}"),
                ])

                # ارزش فعلی‌ها مستقیماً از مدل می‌آید تا محاسبه دوباره انجام نشود
                st.markdown("**جزئیات محاسبه:**")
                schedule = supernormal_schedule(growth_rates, result, g_constant)
                details_data = [
                    {
                        'سال': 'انتهای دوره' if row.is_terminal else f"{row.period}",
                        'نرخ رشد': f"{row.growth_rate_percent:.1f}%",
                        'سود تقسیمی': f"${row.dividend:.2f}",
                        'ارزش فعلی': f"${row.present_value:.2f}"
                    }
                    for row in schedule
                ]

                df_details = pd.DataFrame(details_data)
                st.dataframe(df_details, hide_index=True)

                # نمودار تجزیه ارزش
                fig = charts.create_comparison_chart(
                    [result.pv_dividends_total, result.pv_p_terminal],
                    ['ارزش فعلی سودهای دوره غیرعادی', 'ارزش فعلی قیمت انتهای دوره'],
                    "تجزیه ارزش سهام"
                )
                st.plotly_chart(fig)

        except (ValidationError, CalculationError) as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"خطای غیرمنتظره: {str(e)}")
            logger.error(f"خطای غیرمنتظره در مدل رشد غیرعادی: {e}")


def render_expected_return() -> None:
    """رندر محاسبه بازده مورد انتظار"""
    st.subheader("🔹 محاسبه بازده مورد انتظار")
    st.latex(r"r = \frac{D_1}{P_0} + g")

    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            d1 = st.number_input("سود تقسیمی مورد انتظار سال آینده ($):",
                                 value=1.0, min_value=0.01, step=0.01)
        with col2:
            p0 = st.number_input("قیمت فعلی سهام ($):",
                                 value=20.0, min_value=0.01, step=0.01)
            g = st.number_input("نرخ رشد سود تقسیمی (اعشار):",
                                value=0.10, min_value=0.0, max_value=2.0,
                                step=0.001, format="%.4f")

        calculate = st.button("محاسبه", key="expected_return", type="primary")

    if calculate:
        try:
            breakdown = expected_return_breakdown(d1, p0, g)

            # ذخیره‌سازی نتایج
            save_calculation_results(
                "بازده مورد انتظار",
                {"D1": d1, "P0": p0, "g": g},
                {"r": breakdown.r, "dividend_yield": breakdown.dividend_yield}
            )

            with st.container(border=True):
                render_metrics_row([
                    ("بازده مورد انتظار", f"{breakdown.total_percent:.2f}%"),
                    ("بازده سود تقسیمی", f"{breakdown.dividend_yield_percent:.2f}%"),
                    ("بازده رشد سرمایه", f"{breakdown.capital_gains_yield_percent:.2f}%"),
                ])

                # نمودار تجزیه بازده
                fig = charts.create_comparison_chart(
                    [breakdown.dividend_yield_percent,
                     breakdown.capital_gains_yield_percent,
                     breakdown.total_percent],
                    ['بازده سود تقسیمی', 'بازده رشد سرمایه', 'کل بازده مورد انتظار'],
                    "تجزیه بازده مورد انتظار (%)",
                    y_title="درصد (%)"
                )
                st.plotly_chart(fig)

        except (ValidationError, CalculationError) as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"خطای غیرمنتظره: {str(e)}")
            logger.error(f"خطای غیرمنتظره در محاسبه بازده مورد انتظار: {e}")


def render_capm() -> None:
    """رندر محاسبه بازده مورد انتظار با مدل CAPM"""
    st.subheader("🔹 محاسبه بازده مورد انتظار با CAPM")
    st.latex(r"r = r_f + \beta (r_m - r_f)")

    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            risk_free_rate = st.number_input("نرخ بدون ریسک (اعشار):",
                                             value=0.04, min_value=0.001, max_value=0.30,
                                             step=0.001, format="%.4f")
            beta = st.number_input("ضریب بتای سهام:",
                                   value=1.20, min_value=0.01, max_value=5.0,
                                   step=0.01)
        with col2:
            market_return = st.number_input("بازده مورد انتظار بازار (اعشار):",
                                            value=0.10, min_value=0.001, max_value=0.99,
                                            step=0.001, format="%.4f")

        calculate = st.button("محاسبه", key="capm", type="primary")

    if calculate:
        try:
            breakdown = capm_breakdown(risk_free_rate, beta, market_return)

            # ذخیره‌سازی نتایج
            save_calculation_results(
                "بازده مورد انتظار (CAPM)",
                {"rf": risk_free_rate, "beta": beta, "rm": market_return},
                {"r": breakdown.required_return,
                 "market_risk_premium": breakdown.market_risk_premium}
            )

            with st.container(border=True):
                render_metrics_row([
                    ("بازده مورد انتظار سهام", f"{breakdown.required_return_percent:.2f}%"),
                    ("نرخ بدون ریسک", f"{breakdown.risk_free_rate_percent:.2f}%"),
                    ("صرف ریسک بازار", f"{breakdown.market_risk_premium_percent:.2f}%"),
                    ("صرف ریسک سهام", f"{breakdown.risk_premium_percent:.2f}%"),
                ])

                # نمودار تجزیه بازده
                fig = charts.create_comparison_chart(
                    [breakdown.risk_free_rate_percent,
                     breakdown.risk_premium_percent,
                     breakdown.required_return_percent],
                    ['نرخ بدون ریسک', 'صرف ریسک سهام', 'بازده مورد انتظار'],
                    "تجزیه بازده مورد انتظار (%)",
                    y_title="درصد (%)"
                )
                st.plotly_chart(fig)

            st.caption("این نرخ می‌تواند به عنوان نرخ بازده مورد انتظار (r) در مدل‌های تنزیل سود تقسیمی استفاده شود.")

        except (ValidationError, CalculationError) as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"خطای غیرمنتظره: {str(e)}")
            logger.error(f"خطای غیرمنتظره در محاسبه CAPM: {e}")


# ---------------------------------------------------------------------------
# سهام ممتاز، فرصت‌های رشد و PEG
# ---------------------------------------------------------------------------

def render_preferred_stock() -> None:
    """رندر ارزیابی سهام ممتاز"""
    st.header("💎 ارزیابی سهام ممتاز")
    st.latex(r"P = \frac{D}{r}")

    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            d = st.number_input("سود تقسیمی ثابت سالانه ($):",
                                value=2.25, min_value=0.01, step=0.01)
            r = st.number_input("نرخ بازده مورد انتظار (اعشار):",
                                value=0.09, min_value=0.001, max_value=0.99,
                                step=0.001, format="%.4f")
        with col2:
            bond_equivalent = st.slider("نرخ اوراق قرضه مشابه برای مقایسه (%):",
                                        1.0, 15.0, 8.0, 0.1, key="preferred_bond_rate")

        calculate = st.button("محاسبه", key="preferred", type="primary")

    if calculate:
        try:
            p = preferred_stock_valuation(d, r)

            # ذخیره‌سازی نتایج
            save_calculation_results(
                "ارزیابی سهام ممتاز",
                {"D": d, "r": r},
                {"P": p}
            )

            with st.container(border=True):
                annual_yield = annual_dividend_yield_percent(d, p)
                risk_premium = risk_premium_percent(r, bond_equivalent)

                render_metrics_row([
                    ("قیمت سهام ممتاز", f"${p:,.2f}"),
                    ("بازده سالانه", f"{annual_yield:.2f}%"),
                    ("حق‌الریسک نسبت به اوراق", f"{risk_premium:.2f}%"),
                ])

                # مقایسه با سایر سرمایه‌گذاری‌ها
                if risk_premium > 0:
                    st.info(f"حق‌الریسک در مقایسه با اوراق قرضه: {risk_premium:.2f}%")
                else:
                    st.warning(f"بازده مورد انتظار کمتر از اوراق قرضه است: {risk_premium:.2f}%")

            st.caption("سهام ممتاز معمولاً سود تقسیمی ثابت و اولویت در پرداخت دارند.")

        except (ValidationError, CalculationError) as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"خطای غیرمنتظره: {str(e)}")
            logger.error(f"خطای غیرمنتظره در ارزیابی سهام ممتاز: {e}")


def render_growth_opportunities() -> None:
    """رندر ارزیابی با فرصت‌های رشد"""
    st.header("🚀 ارزیابی با فرصت‌های رشد")
    st.latex(r"P = \frac{EPS}{r} + NPVGO")

    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            eps = st.number_input("سود هر سهم ($):",
                                  value=3.0, min_value=0.01, step=0.01)
            r = st.number_input("نرخ بازده مورد انتظار (اعشار):",
                                value=0.10, min_value=0.001, max_value=0.99,
                                step=0.001, format="%.4f")
        with col2:
            npvgo = st.number_input("ارزش فعلی فرصت‌های رشد ($):",
                                    value=5.0, step=0.01)

        calculate = st.button("محاسبه", key="growth_opp", type="primary")

    if calculate:
        try:
            breakdown = growth_opportunities_breakdown(eps, r, npvgo)

            # ذخیره‌سازی نتایج
            save_calculation_results(
                "ارزیابی با فرصت‌های رشد",
                {"EPS": eps, "r": r, "NPVGO": npvgo},
                {"P": breakdown.total_value,
                 "no_growth_value": breakdown.no_growth_value}
            )

            with st.container(border=True):
                render_metrics_row([
                    ("قیمت کل سهام", f"${breakdown.total_value:,.2f}"),
                    ("ارزش بدون رشد", f"${breakdown.no_growth_value:,.2f}"),
                    ("ارزش فرصت‌های رشد", f"${breakdown.npvgo:,.2f}"),
                    ("سهم فرصت‌های رشد", f"{breakdown.growth_share_percent:.1f}%"),
                ])

                # نمودار تجزیه ارزش
                values = [breakdown.no_growth_value, breakdown.npvgo]
                labels = ['ارزش بدون رشد', 'فرصت‌های رشد']

                fig = charts.create_value_split_bar_chart(
                    values, labels, "تجزیه ارزش سهام"
                )
                st.plotly_chart(fig)

                # نمودار دایره‌ای
                fig_pie = charts.create_value_split_pie_chart(
                    labels, values, "توزیع ارزش سهام"
                )
                st.plotly_chart(fig_pie)

        except (ValidationError, CalculationError) as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"خطای غیرمنتظره: {str(e)}")
            logger.error(f"خطای غیرمنتظره در ارزیابی با فرصت‌های رشد: {e}")


def render_peg_ratio() -> None:
    """رندر محاسبه نسبت PEG"""
    st.header("📊 محاسبه نسبت PEG")
    st.latex(r"PEG = \frac{P/E}{\text{نرخ رشد سالانه سود}}")

    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            pe_ratio = st.number_input("نسبت P/E:",
                                       value=15.0, min_value=0.1, step=0.1)
        with col2:
            growth_rate = st.number_input("نرخ رشد سالانه سود (درصد):",
                                          value=10.0, min_value=0.1, max_value=100.0, step=0.1)

        calculate = st.button("محاسبه", key="peg", type="primary")

    if calculate:
        try:
            peg = peg_ratio(pe_ratio, growth_rate)

            # ذخیره‌سازی نتایج
            save_calculation_results(
                "نسبت PEG",
                {"PE_ratio": pe_ratio, "growth_rate": growth_rate},
                {"PEG": peg}
            )

            with st.container(border=True):
                render_metrics_row([("نسبت PEG", f"{peg:.2f}")])

                # تفسیر نسبت PEG
                interpretation = interpret_peg(peg)
                _PEG_LEVEL_RENDERERS[interpretation.level](interpretation.message)

                # نمودار مقایسه‌ای
                fig = charts.create_peg_position_chart(peg)
                st.plotly_chart(fig)

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


# ---------------------------------------------------------------------------
# مسیریابی سهام عادی
# ---------------------------------------------------------------------------

def render_common_stock() -> None:
    """رندر بخش ارزیابی سهام عادی و انتخاب مدل"""
    st.header("📊 ارزیابی سهام عادی")

    sub_model = st.radio(
        "مدل محاسبه را انتخاب کنید:",
        [
            "مدل تک‌دوره‌ای",
            "مدل رشد صفر",
            "مدل رشد ثابت (گوردون)",
            "مدل رشد غیرعادی",
            "محاسبه بازده مورد انتظار",
            "محاسبه بازده مورد انتظار با CAPM"
        ]
    )

    if sub_model == "مدل تک‌دوره‌ای":
        render_single_period()
    elif sub_model == "مدل رشد صفر":
        render_zero_growth()
    elif sub_model == "مدل رشد ثابت (گوردون)":
        render_constant_growth()
    elif sub_model == "مدل رشد غیرعادی":
        render_supernormal_growth()
    elif sub_model == "محاسبه بازده مورد انتظار":
        render_expected_return()
    elif sub_model == "محاسبه بازده مورد انتظار با CAPM":
        render_capm()
