"""سازنده‌های نمودار — لایه نمایش، بدون وابستگی به Streamlit.

این توابع فقط داده‌های آماده را به Figure تبدیل می‌کنند و هیچ محاسبه دامنه‌ای
انجام نمی‌دهند؛ بنابراین در آزمون‌های واحد نیز بدون Streamlit قابل استفاده‌اند.
"""

from typing import List

import plotly.graph_objects as go

# فونت مشترک نمودارها برای هماهنگی با رابط فارسی
_FONT_FAMILY = "Vazirmatn, Tahoma, sans-serif"

# معیارهای مرجع تفسیر نسبت PEG (فقط برای نمایش)
PEG_BENCHMARKS = [0.5, 1.0, 1.5, 2.0]
PEG_BENCHMARK_LABELS = [
    "کم‌ارزش قوی",
    "منصفانه",
    "نزدیک به بیش‌ارزش",
    "بیش‌ارزش قوی",
]


def create_comparison_chart(values: List[float], labels: List[str], title: str,
                            y_title: str = "مقدار ($)") -> go.Figure:
    """
    ایجاد نمودار مقایسه‌ای

    Args:
        values (List[float]): مقادیر
        labels (List[str]): برچسب‌ها
        title (str): عنوان نمودار
        y_title (str): عنوان محور عمودی (پیش‌فرض: مقدار دلاری)

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
        yaxis_title=y_title,
        font=dict(family=_FONT_FAMILY, size=12),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )

    return fig


def create_value_split_bar_chart(values: List[float], labels: List[str],
                                 title: str) -> go.Figure:
    """
    نمودار ستونی دو بخشی برای تجزیه ارزش (با رنگ‌بندی متمایز)

    Args:
        values (List[float]): مقادیر هر بخش
        labels (List[str]): برچسب بخش‌ها
        title (str): عنوان نمودار

    Returns:
        go.Figure: نمودار plotly
    """
    colors = ['rgba(55, 128, 191, 0.7)', 'rgba(255, 193, 7, 0.7)']

    fig = go.Figure(data=[
        go.Bar(x=labels, y=values, marker_color=colors)
    ])
    fig.update_layout(
        title=title,
        xaxis_title="اجزاء ارزش",
        yaxis_title="مقدار ($)",
        font=dict(family=_FONT_FAMILY, size=12)
    )

    return fig


def create_value_split_pie_chart(labels: List[str], values: List[float],
                                 title: str) -> go.Figure:
    """
    نمودار دایره‌ای توزیع ارزش

    Args:
        labels (List[str]): برچسب بخش‌ها
        values (List[float]): مقادیر هر بخش
        title (str): عنوان نمودار

    Returns:
        go.Figure: نمودار plotly
    """
    fig = go.Figure(data=[
        go.Pie(labels=labels, values=[abs(v) for v in values], hole=.3)
    ])
    fig.update_layout(title=title, font=dict(family=_FONT_FAMILY, size=12))

    return fig


def create_dividend_forecast_chart(dividends: List[float]) -> go.Figure:
    """
    نمودار خطی پیش‌بینی سود تقسیمی

    Args:
        dividends (List[float]): سودهای تقسیمی پیش‌بینی‌شده از سال ۱

    Returns:
        go.Figure: نمودار plotly
    """
    years = list(range(1, len(dividends) + 1))

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=years, y=dividends,
        mode='lines+markers',
        name='سود تقسیمی پیش‌بینی شده',
        line=dict(color='blue', width=2)
    ))
    fig.update_layout(
        title="پیش‌بینی سود تقسیمی ۱۰ سال آینده",
        xaxis_title="سال",
        yaxis_title="سود تقسیمی ($)",
        font=dict(family=_FONT_FAMILY, size=12)
    )

    return fig


def create_peg_position_chart(peg: float) -> go.Figure:
    """
    نمودار موقعیت نسبت PEG نسبت به معیارهای مرجع

    Args:
        peg (float): نسبت PEG محاسبه‌شده

    Returns:
        go.Figure: نمودار plotly
    """
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=PEG_BENCHMARKS, y=[1] * len(PEG_BENCHMARKS),
        mode='markers', name='معیارهای مرجع',
        marker=dict(size=10, color='lightblue')
    ))
    fig.add_trace(go.Scatter(
        x=[peg], y=[1], mode='markers', name='نسبت محاسبه شده',
        marker=dict(size=15, color='red', symbol='diamond')
    ))

    for peg_val, label in zip(PEG_BENCHMARKS, PEG_BENCHMARK_LABELS):
        fig.add_annotation(
            x=peg_val, y=1.05, text=label,
            showarrow=False, textangle=-45
        )

    fig.update_layout(
        title="موقعیت نسبت PEG محاسبه شده",
        xaxis_title="نسبت PEG",
        yaxis=dict(showticklabels=False, range=[0.8, 1.2]),
        showlegend=False,
        font=dict(family=_FONT_FAMILY, size=12)
    )

    return fig
