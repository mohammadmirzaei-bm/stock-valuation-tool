"""مدل‌های ارزیابی سهام — نمای سازگاری عقب‌رو برای ماژول‌های تفکیک‌شده دامنه.

این ماژول دیگر منطق ندارد و صرفاً نام‌های عمومی ماژول‌های تخصصی زیر را
دوباره صادر می‌کند تا importهای موجود بدون تغییر کار کنند:

    equity: ارزش‌گذاری سهام عادی (DDM، CAPM، NPVGO، رشد پایدار، PEG)
    cost_of_capital: میانگین موزون هزینه سرمایه (WACC)
    dcf: ارزش‌گذاری جریان نقدی تنزیل‌شده بر پایه FCFF
    dcf_analysis: سناریوها، ماتریس حساسیت و DCF معکوس

کد جدید باید مستقیماً از ماژول تخصصی موضوع خود import کند.

قرارداد خطا:
    ValidationError: ورودی نامعتبر یا ترکیب نامعتبر پارامترها
    CalculationError: نتیجه غیرعددی یا خطای عددی در محاسبه
"""

from .cost_of_capital import WaccBreakdown, wacc, wacc_breakdown
from .dcf import (
    CashFlowProjection,
    DcfBreakdown,
    FcffYearRow,
    calculate_fcff,
    dcf_valuation,
)
from .dcf_analysis import (
    REVERSE_DCF_MIN_GROWTH,
    DcfScenario,
    DcfSensitivityResult,
    ReverseDcfResult,
    ScenarioRow,
    ScenarioValuationResult,
    dcf_scenario_valuation,
    dcf_sensitivity,
    reverse_dcf_implied_growth,
)
from .equity import (
    CapmBreakdown,
    ExpectedReturnBreakdown,
    GordonBreakdown,
    GrowthOpportunitiesBreakdown,
    PegInterpretation,
    RetentionCurvePoint,
    SinglePeriodDecomposition,
    SupernormalResult,
    SupernormalScheduleRow,
    SustainableGrowthBreakdown,
    annual_dividend_yield_percent,
    capm_breakdown,
    capm_required_return,
    constant_growth_model,
    expected_return,
    expected_return_breakdown,
    gordon_breakdown,
    growth_opportunities_breakdown,
    growth_opportunities_valuation,
    interpret_peg,
    peg_ratio,
    preferred_stock_valuation,
    project_dividends,
    risk_premium_percent,
    single_period_decomposition,
    single_period_model,
    supernormal_growth_model,
    supernormal_schedule,
    sustainable_growth_valuation,
    zero_growth_model,
)
from .errors import CalculationError, ValidationError

__all__ = [
    "CalculationError",
    "ValidationError",
    "CapmBreakdown",
    "ExpectedReturnBreakdown",
    "GordonBreakdown",
    "GrowthOpportunitiesBreakdown",
    "PegInterpretation",
    "RetentionCurvePoint",
    "SinglePeriodDecomposition",
    "SupernormalResult",
    "SupernormalScheduleRow",
    "SustainableGrowthBreakdown",
    "annual_dividend_yield_percent",
    "capm_breakdown",
    "capm_required_return",
    "constant_growth_model",
    "expected_return",
    "expected_return_breakdown",
    "gordon_breakdown",
    "growth_opportunities_breakdown",
    "growth_opportunities_valuation",
    "interpret_peg",
    "peg_ratio",
    "preferred_stock_valuation",
    "project_dividends",
    "risk_premium_percent",
    "single_period_decomposition",
    "single_period_model",
    "supernormal_growth_model",
    "supernormal_schedule",
    "sustainable_growth_valuation",
    "zero_growth_model",
    "WaccBreakdown",
    "wacc",
    "wacc_breakdown",
    "CashFlowProjection",
    "DcfBreakdown",
    "FcffYearRow",
    "calculate_fcff",
    "dcf_valuation",
    "REVERSE_DCF_MIN_GROWTH",
    "DcfScenario",
    "DcfSensitivityResult",
    "ReverseDcfResult",
    "ScenarioRow",
    "ScenarioValuationResult",
    "dcf_scenario_valuation",
    "dcf_sensitivity",
    "reverse_dcf_implied_growth",
]
