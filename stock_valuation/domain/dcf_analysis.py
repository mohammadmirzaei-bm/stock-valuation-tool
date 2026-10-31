"""تحلیل‌های تکمیلی DCF — سناریوهای وزنی، ماتریس حساسیت و DCF معکوس.

این ماژول فقط به ``domain.dcf`` وابسته است و هر محاسبه ارزش را با فراخوانی
``dcf_valuation`` انجام می‌دهد؛ هیچ فرمول تنزیل یا ارزش انتهای دوره‌ای اینجا
تکرار نمی‌شود. جهت وابستگی یک‌طرفه است: ``dcf`` هرگز از این ماژول import
نمی‌کند.

قرارداد خطا:
    ValidationError: ورودی نامعتبر، از جمله شکست یک سناریو
    CalculationError: خطای عددی یا شکست همگرایی جستجوی DCF معکوس
"""

import logging
import math
from dataclasses import dataclass
from typing import List, Optional

from .dcf import CashFlowProjection, DcfBreakdown, dcf_valuation
from .errors import CalculationError, ValidationError
from .validators import (
    DEFAULT_GROWTH_STEP,
    DEFAULT_SENSITIVITY_POINTS,
    DEFAULT_WACC_STEP,
    MIN_SPREAD,
    require_finite_number,
    validate_positive_number,
    validate_scenario_set,
    validate_sensitivity_grid,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DcfScenario:
    """ورودی یک سناریوی نام‌گذاری‌شده با احتمال و پیش‌بینی مستقل DCF."""

    name: str
    probability: float
    projections: List[CashFlowProjection]
    wacc_rate: float
    terminal_growth: float


@dataclass(frozen=True)
class ScenarioRow:
    """ارزش و سهم وزنی یک سناریو؛ بازده بدون قیمت بازار برابر None است."""

    name: str
    probability: float
    wacc: float
    terminal_growth: float
    enterprise_value: float
    equity_value: float
    value_per_share: float
    terminal_value_share_percent: float
    weighted_value_per_share: float
    upside: Optional[float]

    @property
    def probability_percent(self) -> float:
        """احتمال سناریو به درصد"""
        return self.probability * 100

    @property
    def wacc_percent(self) -> float:
        """نرخ WACC به درصد"""
        return self.wacc * 100

    @property
    def terminal_growth_percent(self) -> float:
        """نرخ رشد پایانی به درصد"""
        return self.terminal_growth * 100

    @property
    def upside_percent(self) -> Optional[float]:
        """بازده بالقوه به درصد؛ بدون قیمت بازار None"""
        return None if self.upside is None else self.upside * 100


@dataclass(frozen=True)
class ScenarioValuationResult:
    """ارزش مورد انتظار و ریسک سناریوهای DCF با حفظ ترتیب ورودی."""

    scenarios: List[ScenarioRow]
    expected_value_per_share: float
    expected_enterprise_value: float
    expected_equity_value: float
    std_dev_value_per_share: float
    min_value_per_share: float
    max_value_per_share: float
    worst_scenario: str
    best_scenario: str
    market_price: Optional[float]
    expected_upside: Optional[float]
    probability_of_upside: Optional[float]

    @property
    def expected_upside_percent(self) -> Optional[float]:
        """بازده بالقوه مورد انتظار به درصد؛ بدون قیمت بازار None"""
        return None if self.expected_upside is None else self.expected_upside * 100

    @property
    def probability_of_upside_percent(self) -> Optional[float]:
        """احتمال ارزش بالاتر از بازار به درصد؛ بدون قیمت بازار None"""
        return None if self.probability_of_upside is None else self.probability_of_upside * 100


@dataclass(frozen=True)
class DcfSensitivityResult:
    """ماتریس حساسیت ارزش DCF نسبت به WACC و نرخ رشد پایانی

    سطرها محور WACC و ستون‌ها محور رشد پایانی هستند؛ سلول نامعتبر
    (مثلاً نقض حداقل اختلاف WACC و رشد) مقدار ``None`` می‌گیرد.

    Attributes:
        wacc_values: محور سطرها (اعشاری)، صعودی و مرکزچین روی WACC پایه
        growth_values: محور ستون‌ها (اعشاری)، صعودی و مرکزچین روی رشد پایه
        value_per_share: ماتریس ارزش هر سهم؛ [i][j] ↔ wacc_values[i] × growth_values[j]
        enterprise_value: ماتریس ارزش بنگاه با همان شکل
        base_wacc: WACC حالت پایه (اعشاری)
        base_terminal_growth: نرخ رشد پایانی حالت پایه (اعشاری)
        base_row: اندیس WACC پایه در wacc_values
        base_col: اندیس رشد پایه در growth_values
        base_value_per_share: ارزش هر سهم در حالت پایه
        base_enterprise_value: ارزش بنگاه در حالت پایه
        valid_cells: تعداد سلول‌های معتبر
        total_cells: تعداد کل سلول‌ها
    """

    wacc_values: List[float]
    growth_values: List[float]
    value_per_share: List[List[Optional[float]]]
    enterprise_value: List[List[Optional[float]]]
    base_wacc: float
    base_terminal_growth: float
    base_row: int
    base_col: int
    base_value_per_share: float
    base_enterprise_value: float
    valid_cells: int
    total_cells: int

    @property
    def wacc_values_percent(self) -> List[float]:
        """محور WACC به درصد"""
        return [value * 100 for value in self.wacc_values]

    @property
    def growth_values_percent(self) -> List[float]:
        """محور رشد پایانی به درصد"""
        return [value * 100 for value in self.growth_values]


@dataclass(frozen=True)
class ReverseDcfResult:
    """نتیجه DCF معکوس: رشد پایانی تلویحی قیمت بازار

    Attributes:
        status: وضعیت حل؛ یکی از ``solved``، ``market_price_below_range``
            یا ``market_price_above_range``
        market_price: قیمت بازار سهام (ورودی)
        implied_growth: نرخ رشد پایانی تلویحی (اعشاری)؛ فقط در وضعیت solved
        wacc: نرخ WACC استفاده‌شده (اعشاری)
        search_min_growth: کرانه پایین بازه جستجو (اعشاری)
        search_max_growth: کرانه بالای بازه جستجو (اعشاری)
        value_per_share_at_min_growth: ارزش هر سهم در کرانه پایین جستجو
        value_per_share_at_max_growth: ارزش هر سهم در کرانه بالای جستجو
        enterprise_value: ارزش بنگاه در رشد تلویحی؛ در غیر solved برابر None
        equity_value: ارزش حقوق صاحبان سهام در رشد تلویحی؛ در غیر solved None
        terminal_value_share_percent: سهم ارزش فعلی انتهای دوره از EV (درصد)
        reference_terminal_growth: نرخ رشد پایانی تحلیل‌گر (اختیاری)
        growth_gap: اختلاف رشد تلویحی و رشد مرجع (اعشاری)
        message: پیام فارسی برای نمایش به کاربر
    """

    status: str
    market_price: float
    implied_growth: Optional[float]
    wacc: float
    search_min_growth: float
    search_max_growth: float
    value_per_share_at_min_growth: float
    value_per_share_at_max_growth: float
    enterprise_value: Optional[float]
    equity_value: Optional[float]
    terminal_value_share_percent: Optional[float]
    reference_terminal_growth: Optional[float]
    growth_gap: Optional[float]
    message: str

    @property
    def implied_growth_percent(self) -> Optional[float]:
        """رشد پایانی تلویحی به درصد؛ اگر حل نشده باشد None"""
        if self.implied_growth is None:
            return None
        return self.implied_growth * 100

    @property
    def growth_gap_percent(self) -> Optional[float]:
        """اختلاف رشد تلویحی و رشد مرجع به درصد؛ در صورت نبود مقدار None"""
        if self.growth_gap is None:
            return None
        return self.growth_gap * 100

    @property
    def wacc_percent(self) -> float:
        """نرخ WACC به درصد"""
        return self.wacc * 100


# ---------------------------------------------------------------------------
# WACC و DCF (بر پایه FCFF)
# ---------------------------------------------------------------------------

# کرانه پایین جستجوی نرخ رشد پایانی در DCF معکوس
# (بازار ممکن است کاهش را قیمت‌گذاری کند)
REVERSE_DCF_MIN_GROWTH = -0.20


def dcf_scenario_valuation(
    scenarios: List[DcfScenario],
    shares_outstanding: float,
    tax_rate: float,
    cash: float = 0.0,
    debt: float = 0.0,
    minority_interest: float = 0.0,
    preferred_equity: float = 0.0,
    market_price: Optional[float] = None,
) -> ScenarioValuationResult:
    """ارزش‌گذاری سناریوهای DCF و آمار وزنی بدون تغییر احتمال‌ها یا ورودی‌ها.

    Args:
        scenarios: دو تا پنج سناریوی نام‌گذاری‌شده؛ مجموع احتمال‌ها برابر یک
        shares_outstanding: تعداد سهام مشترک؛ مثبت
        tax_rate: نرخ مالیات مشترک؛ اعشاری
        cash: موجودی نقد مشترک
        debt: بدهی بهره‌دار مشترک
        minority_interest: منافع اقلیت مشترک
        preferred_equity: سهام ممتاز مشترک
        market_price: قیمت بازار اختیاری؛ متناهی و مثبت

    Returns:
        ScenarioValuationResult: سطرها به ترتیب ورودی و آمار ارزش و ریسک

    Raises:
        ValidationError: ورودی نامعتبر؛ شکست یک سناریو کل درخواست را رد می‌کند
        CalculationError: خطای عددی؛ خطای سناریو نام آن را نیز دارد
    """
    if not isinstance(scenarios, list) or any(not isinstance(item, DcfScenario) for item in scenarios):
        raise ValidationError("❌ سناریوها باید فهرستی از DcfScenario باشند!")
    validate_scenario_set(
        [scenario.name for scenario in scenarios],
        [scenario.probability for scenario in scenarios],
    )
    if market_price is not None:
        require_finite_number(market_price, "قیمت بازار")
        validate_positive_number(market_price, "قیمت بازار")

    try:
        rows: List[ScenarioRow] = []
        for scenario in scenarios:
            try:
                breakdown = dcf_valuation(
                    scenario.projections, scenario.wacc_rate, scenario.terminal_growth,
                    shares_outstanding, tax_rate, cash=cash, debt=debt,
                    minority_interest=minority_interest, preferred_equity=preferred_equity,
                )
            except (ValidationError, CalculationError) as exc:
                raise type(exc)(f"سناریو «{scenario.name}» — {exc}") from exc
            row = ScenarioRow(
                name=scenario.name, probability=scenario.probability,
                wacc=breakdown.wacc, terminal_growth=breakdown.terminal_growth,
                enterprise_value=breakdown.enterprise_value, equity_value=breakdown.equity_value,
                value_per_share=breakdown.value_per_share,
                terminal_value_share_percent=breakdown.terminal_value_share_percent,
                weighted_value_per_share=scenario.probability * breakdown.value_per_share,
                upside=None if market_price is None else breakdown.value_per_share / market_price - 1,
            )
            if not all(value is None or math.isfinite(value) for value in (
                row.probability, row.wacc, row.terminal_growth, row.enterprise_value,
                row.equity_value, row.value_per_share, row.terminal_value_share_percent,
                row.weighted_value_per_share, row.upside, row.probability_percent,
                row.wacc_percent, row.terminal_growth_percent, row.upside_percent,
            )):
                raise CalculationError("نتیجه محاسبه نامعتبر است")
            rows.append(row)

        expected = sum(row.weighted_value_per_share for row in rows)
        variance = sum(row.probability * (row.value_per_share - expected) ** 2 for row in rows)
        worst = min(rows, key=lambda row: row.value_per_share)
        best = max(rows, key=lambda row: row.value_per_share)
        result = ScenarioValuationResult(
            scenarios=rows, expected_value_per_share=expected,
            expected_enterprise_value=sum(row.probability * row.enterprise_value for row in rows),
            expected_equity_value=sum(row.probability * row.equity_value for row in rows),
            std_dev_value_per_share=math.sqrt(variance),
            min_value_per_share=worst.value_per_share, max_value_per_share=best.value_per_share,
            worst_scenario=worst.name, best_scenario=best.name, market_price=market_price,
            expected_upside=None if market_price is None else expected / market_price - 1,
            probability_of_upside=None if market_price is None else sum(
                row.probability for row in rows if row.value_per_share > market_price
            ),
        )
        if not all(value is None or math.isfinite(value) for value in (
            result.expected_value_per_share, result.expected_enterprise_value,
            result.expected_equity_value, result.std_dev_value_per_share,
            result.min_value_per_share, result.max_value_per_share, result.market_price,
            result.expected_upside, result.probability_of_upside,
            result.expected_upside_percent, result.probability_of_upside_percent,
        )):
            raise CalculationError("نتیجه محاسبه نامعتبر است")
        return result
    except (ZeroDivisionError, ValueError, OverflowError) as exc:
        raise CalculationError("نتیجه محاسبه نامعتبر است") from exc


def dcf_sensitivity(
    projections: List[CashFlowProjection],
    wacc_rate: float,
    terminal_growth: float,
    shares_outstanding: float,
    tax_rate: float,
    cash: float = 0.0,
    debt: float = 0.0,
    minority_interest: float = 0.0,
    preferred_equity: float = 0.0,
    wacc_step: float = DEFAULT_WACC_STEP,
    growth_step: float = DEFAULT_GROWTH_STEP,
    wacc_points: int = DEFAULT_SENSITIVITY_POINTS,
    growth_points: int = DEFAULT_SENSITIVITY_POINTS,
) -> DcfSensitivityResult:
    """
    ماتریس حساسیت ارزش DCF نسبت به WACC و نرخ رشد پایانی

    هر سلول با فراخوانی ``dcf_valuation`` برای همان ترکیب محاسبه می‌شود؛
    هیچ فرمول تنزیل یا ارزش انتهای دوره‌ای در این تابع تکرار نمی‌شود.
    سلولی که ``dcf_valuation`` آن را نامعتبر بداند (مثلاً WACC نامثبت یا
    نقض حداقل اختلاف) به‌جای شکست کل ماتریس، ``None`` می‌شود. محورها صعودی
    و مرکزچین روی حالت پایه‌اند؛ بنابراین سلول مرکزی دقیقاً همان نتیجه
    حالت پایه است.

    Args:
        projections (List[CashFlowProjection]): پیش‌بینی سالانه اجزای FCFF
        wacc_rate (float): WACC حالت پایه (اعشاری؛ مثبت)
        terminal_growth (float): نرخ رشد پایانی حالت پایه (اعشاری)
        shares_outstanding (float): تعداد سهام (مثبت)
        tax_rate (float): نرخ مالیات سراسری (اعشاری؛ ۰ ≤ t < ۱)
        cash (float): موجودی نقد (نامنفی)
        debt (float): بدهی بهره‌دار (نامنفی)
        minority_interest (float): منافع اقلیت (نامنفی)
        preferred_equity (float): سهام ممتاز (نامنفی)
        wacc_step (float): فاصله نقاط محور WACC (اعشاری؛ مثبت)
        growth_step (float): فاصله نقاط محور رشد پایانی (اعشاری؛ مثبت)
        wacc_points (int): تعداد نقاط محور WACC (فرد؛ ۳ تا ۱۱)
        growth_points (int): تعداد نقاط محور رشد پایانی (فرد؛ ۳ تا ۱۱)

    Returns:
        DcfSensitivityResult: محورها، ماتریس‌ها و اطلاعات حالت پایه

    Raises:
        ValidationError: در صورت نامعتبر بودن پارامترهای شبکه یا حالت پایه
        CalculationError: در صورت خطای محاسباتی در حالت پایه
    """
    validate_sensitivity_grid(wacc_step, growth_step, wacc_points, growth_points)

    # حالت پایه؛ خطای آن کل درخواست را نامعتبر می‌کند و باید بالا برود.
    base = dcf_valuation(
        projections,
        wacc_rate,
        terminal_growth,
        shares_outstanding,
        tax_rate,
        cash=cash,
        debt=debt,
        minority_interest=minority_interest,
        preferred_equity=preferred_equity,
    )

    base_row = wacc_points // 2
    base_col = growth_points // 2

    # round(..., 10) نویز ممیز شناور (مثل 0.09999999999) را حذف می‌کند.
    wacc_values = [
        round(wacc_rate + (index - base_row) * wacc_step, 10)
        for index in range(wacc_points)
    ]
    growth_values = [
        round(terminal_growth + (index - base_col) * growth_step, 10)
        for index in range(growth_points)
    ]

    value_per_share: List[List[Optional[float]]] = []
    enterprise_value: List[List[Optional[float]]] = []
    valid_cells = 0

    for row_index, wacc_value in enumerate(wacc_values):
        value_row: List[Optional[float]] = []
        enterprise_row: List[Optional[float]] = []
        for col_index, growth_value in enumerate(growth_values):
            if row_index == base_row and col_index == base_col:
                # سلول مرکزی عیناً نتیجه حالت پایه است.
                value_row.append(base.value_per_share)
                enterprise_row.append(base.enterprise_value)
                valid_cells += 1
                continue

            try:
                cell = dcf_valuation(
                    projections,
                    wacc_value,
                    growth_value,
                    shares_outstanding,
                    tax_rate,
                    cash=cash,
                    debt=debt,
                    minority_interest=minority_interest,
                    preferred_equity=preferred_equity,
                )
            except (ValidationError, CalculationError):
                # ترکیب نامعتبر فقط همان سلول را None می‌کند.
                value_row.append(None)
                enterprise_row.append(None)
                continue

            value_row.append(cell.value_per_share)
            enterprise_row.append(cell.enterprise_value)
            valid_cells += 1

        value_per_share.append(value_row)
        enterprise_value.append(enterprise_row)

    return DcfSensitivityResult(
        wacc_values=wacc_values,
        growth_values=growth_values,
        value_per_share=value_per_share,
        enterprise_value=enterprise_value,
        base_wacc=wacc_rate,
        base_terminal_growth=terminal_growth,
        base_row=base_row,
        base_col=base_col,
        base_value_per_share=base.value_per_share,
        base_enterprise_value=base.enterprise_value,
        valid_cells=valid_cells,
        total_cells=wacc_points * growth_points,
    )


def reverse_dcf_implied_growth(
    projections: List[CashFlowProjection],
    wacc_rate: float,
    shares_outstanding: float,
    tax_rate: float,
    market_price: float,
    cash: float = 0.0,
    debt: float = 0.0,
    minority_interest: float = 0.0,
    preferred_equity: float = 0.0,
    reference_terminal_growth: Optional[float] = None,
) -> ReverseDcfResult:
    """
    نرخ رشد پایانی تلویحی قیمت بازار با DCF معکوس

    ارزش هر سهم نسبت به نرخ رشد پایانی (با FCFF پایانی مثبت) اکیداً صعودی
    است؛ بنابراین رشد تلویحی با نصف‌سازی بازه ``[REVERSE_DCF_MIN_GROWTH,
    WACC − MIN_SPREAD]`` روی خروجی ``dcf_valuation`` پیدا می‌شود. اگر قیمت
    بازار بیرون این بازه باشد، پاسخ به‌جای خطا وضعیت ``market_price_below_range``
    یا ``market_price_above_range`` می‌گیرد.

    Args:
        projections (List[CashFlowProjection]): پیش‌بینی سالانه اجزای FCFF
        wacc_rate (float): نرخ تنزیل / WACC (اعشاری؛ مثبت)
        shares_outstanding (float): تعداد سهام (مثبت)
        tax_rate (float): نرخ مالیات سراسری (اعشاری؛ ۰ ≤ t < ۱)
        market_price (float): قیمت بازار سهام (مثبت)
        cash (float): موجودی نقد (نامنفی)
        debt (float): بدهی بهره‌دار (نامنفی)
        minority_interest (float): منافع اقلیت (نامنفی)
        preferred_equity (float): سهام ممتاز (نامنفی)
        reference_terminal_growth (Optional[float]): نرخ رشد پایانی تحلیل‌گر؛
            فقط برای محاسبه ``growth_gap`` و صرفاً از نظر متناهی‌بودن بررسی می‌شود

    Returns:
        ReverseDcfResult: رشد تلویحی، تفکیک ارزش در آن نرخ و وضعیت حل

    Raises:
        ValidationError: در صورت ورودی نامعتبر (از جمله FCFF پایانی غیرمثبت)
        CalculationError: در صورت شکست همگرایی جستجوی نصف‌سازی
    """
    require_finite_number(market_price, "قیمت بازار")
    validate_positive_number(market_price, "قیمت بازار")
    if reference_terminal_growth is not None:
        require_finite_number(reference_terminal_growth, "نرخ رشد پایانی مرجع")

    def value_at(growth_rate: float) -> DcfBreakdown:
        """ارزش‌گذاری DCF در یک نرخ رشد پایانی مشخص"""
        return dcf_valuation(
            projections,
            wacc_rate,
            growth_rate,
            shares_outstanding,
            tax_rate,
            cash=cash,
            debt=debt,
            minority_interest=minority_interest,
            preferred_equity=preferred_equity,
        )

    search_min_growth = REVERSE_DCF_MIN_GROWTH
    search_max_growth = wacc_rate - MIN_SPREAD

    # خطای ورودی در کرانه‌ها بالا می‌رود؛ فقط ترکیب‌های نامعتبر سلول نیستند.
    value_at_min = value_at(search_min_growth).value_per_share
    value_at_max = value_at(search_max_growth).value_per_share

    tolerance = 1e-9 * max(1.0, market_price)
    implied_growth: Optional[float] = None
    status = "solved"

    if abs(value_at_min - market_price) <= tolerance:
        implied_growth = search_min_growth
    elif abs(value_at_max - market_price) <= tolerance:
        implied_growth = search_max_growth
    elif value_at_min > market_price:
        status = "market_price_below_range"
    elif value_at_max < market_price:
        status = "market_price_above_range"
    else:
        low = search_min_growth
        high = search_max_growth
        for _ in range(200):
            middle = (low + high) / 2
            value = value_at(middle).value_per_share
            if abs(value - market_price) <= tolerance:
                implied_growth = middle
                break
            if value < market_price:
                low = middle
            else:
                high = middle
            if high - low < 1e-12:
                implied_growth = (low + high) / 2
                break
        if implied_growth is None:
            raise CalculationError(
                "❌ همگرایی جستجوی رشد تلویحی در DCF معکوس ممکن نشد!"
            )

    enterprise_value: Optional[float] = None
    equity_value: Optional[float] = None
    terminal_value_share_percent: Optional[float] = None
    if implied_growth is not None:
        breakdown = value_at(implied_growth)
        enterprise_value = breakdown.enterprise_value
        equity_value = breakdown.equity_value
        terminal_value_share_percent = breakdown.terminal_value_share_percent

    growth_gap: Optional[float] = None
    if implied_growth is not None and reference_terminal_growth is not None:
        growth_gap = implied_growth - reference_terminal_growth

    if status == "market_price_below_range":
        message = (
            f"قیمت بازار حتی از ارزش با کمترین نرخ رشد قابل جستجو "
            f"({search_min_growth * 100:.2f}%) هم کمتر است؛ "
            f"بازه جستجو: {search_min_growth * 100:.2f}% تا "
            f"{search_max_growth * 100:.2f}%"
        )
    elif status == "market_price_above_range":
        message = (
            f"قیمت بازار حتی از ارزش با بیشترین نرخ رشد مجاز "
            f"({search_max_growth * 100:.2f}%) هم بیشتر است؛ "
            f"بازه جستجو: {search_min_growth * 100:.2f}% تا "
            f"{search_max_growth * 100:.2f}%"
        )
    else:
        message = (
            f"بازار با این قیمت، رشد پایانی حدود {implied_growth * 100:.2f}% "
            f"را فرض کرده است"
        )

    return ReverseDcfResult(
        status=status,
        market_price=market_price,
        implied_growth=implied_growth,
        wacc=wacc_rate,
        search_min_growth=search_min_growth,
        search_max_growth=search_max_growth,
        value_per_share_at_min_growth=value_at_min,
        value_per_share_at_max_growth=value_at_max,
        enterprise_value=enterprise_value,
        equity_value=equity_value,
        terminal_value_share_percent=terminal_value_share_percent,
        reference_terminal_growth=reference_terminal_growth,
        growth_gap=growth_gap,
        message=message,
    )
