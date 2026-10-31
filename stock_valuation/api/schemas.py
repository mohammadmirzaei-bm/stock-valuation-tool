"""قراردادهای داده لایه API (Pydantic) برای سرویس ارزیابی سهام.

این ماژول پل میان توابع خالص دامنه در `stock_valuation.domain.valuation_models`
 و JSON مبادله‌شده با فرانت‌اند React است.

نکات طراحی:
    1. کلاس‌های پاسخ، آینه مدل‌های دامنه (NamedTuple / dataclass منجمد) هستند
       و نام فیلدهایشان دقیقاً یکی است؛ پس `Model.model_domain(obj)` بدون
       نگاشت دستی کار می‌کند.
    2. فیلدهای درصدی که در دامنه property هستند (مانند
       `dividend_yield_percent`) با `from_attributes` به‌صورت خودکار پر می‌شوند.
       فیلدهایی که دامنه نمی‌دهد (نمایش مجدد ورودی، یا مقدار برگشتی ساده تابع)
       `Optional` هستند و لایه endpoint مقدارشان را پر می‌کند؛ نامپرشان `None`
       می‌ماند تا در JSON قابل تشخیص باشد.
    3. کرانه‌های `Field` فقط آینه اعتبارسنج‌های دامنه هستند و هیچ قانون
       جدیدی اضافه نمی‌کنند؛ منبع حقیقت اعتبارسنجی همان `domain.validators`
       و خود توابع دامنه است (خطاها به شکل ValidationError / CalculationError
       در لایه HTTP ترجمه می‌شوند).
    4. نرخ‌ها (گوردون، رشد غیرعادی، بازده مورد انتظار، CAPM) بر حسب اعشار
       وارد می‌شوند؛ همان قرارداد دامنه. مثلاً ۱۲٪ === 0.12
       استثنای آن دو مدل دامنه‌ای است که ذاتاً درصدی کار می‌کنند:
       نرخ رشد در `risk_premium_percent` و نرخ رشد در `peg_ratio`.
"""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from ..domain.validators import (
    DEFAULT_GROWTH_STEP,
    DEFAULT_SENSITIVITY_POINTS,
    DEFAULT_WACC_STEP,
    MAX_SCENARIOS,
    MIN_SCENARIOS,
)


class _Base(BaseModel):
    """پایه مشترک همه مدل‌های این ماژول."""

    model_config = ConfigDict(
        # ساخت از نمونه‌های دامنه (NamedTuple / dataclass منجمد) بدون نگاشت دستی
        from_attributes=True,
        # ثبت نام فیلدها به‌صورت keyword؛ برای خواندن ساده از نمونه دامنه
        populate_by_name=True,
    )


class _RequestBase(_Base):
    """پایه بدنه درخواست‌ها؛ فیلد ناشناخته مجاز نیست."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        extra="forbid",
    )


# ---------------------------------------------------------------------------
# مدل‌های پاسخ — معادل Pydantic خروجی‌های دامنه
# ---------------------------------------------------------------------------

class SinglePeriodResult(_Base):
    """پاسخ مدل تک‌دوره‌ای؛ معادل `SinglePeriodDecomposition`.

    Attributes:
        p0: قیمت فعلی سهام
        pv_dividend: ارزش فعلی سود تقسیمی پایان سال
        pv_terminal_price: ارزش فعلی قیمت پایان سال
    """

    p0: float = Field(description="قیمت فعلی سهام (P₀)")
    pv_dividend: float = Field(description="ارزش فعلی سود تقسیمی پایان سال")
    pv_terminal_price: float = Field(description="ارزش فعلی قیمت پایان سال")


class GordonResult(_Base):
    """پاسخ مدل رشد ثابت گوردون؛ معادل `GordonBreakdown`.

    Attributes:
        price: قیمت سهام
        d1: سود تقسیمی سال آینده
        dividend_yield: بازده سود تقسیمی (اعشاری)
        dividend_yield_percent: بازده سود تقسیمی (درصد)
        capital_gains_yield: بازده رشد سرمایه (اعشاری)
        capital_gains_yield_percent: بازده رشد سرمایه (درصد)
        required_return: نرخ بازده ورودی، نمایش مجدد (اعشاری)
        required_return_percent: نرخ بازده ورودی (درصد)
        growth_rate: نرخ رشد ورودی، نمایش مجدد (اعشاری)
        growth_rate_percent: نرخ رشد ورودی (درصد)
    """

    price: float = Field(description="قیمت سهام")
    d1: float = Field(description="سود تقسیمی سال آینده (D₁)")
    dividend_yield: float = Field(description="بازده سود تقسیمی (اعشاری)")
    dividend_yield_percent: float = Field(description="بازده سود تقسیمی (درصد)")
    capital_gains_yield: float = Field(description="بازده رشد سرمایه (اعشاری)")
    capital_gains_yield_percent: float = Field(description="بازده رشد سرمایه (درصد)")
    required_return: Optional[float] = Field(default=None, description="نرخ بازده ورودی (اعشاری)")
    required_return_percent: Optional[float] = Field(default=None, description="نرخ بازده ورودی (درصد)")
    growth_rate: Optional[float] = Field(default=None, description="نرخ رشد ورودی (اعشاری)")
    growth_rate_percent: Optional[float] = Field(default=None, description="نرخ رشد ورودی (درصد)")


class ZeroGrowthResult(_Base):
    """پاسخ مدل رشد صفر؛ معادل `zero_growth_model`.

    Attributes:
        price: قیمت سهام
        dividend: سود تقسیمی ورودی، نمایش مجدد
        required_return: نرخ بازده ورودی (اعشاری)
        required_return_percent: نرخ بازده ورودی (درصد)
        dividend_yield_percent: بازده سود تقسیمی به درصد
    """

    price: float = Field(description="قیمت سهام")
    dividend: float = Field(description="سود تقسیمی ثابت (D)")
    required_return: float = Field(description="نرخ بازده مورد انتظار (اعشاری)")
    required_return_percent: float = Field(description="نرخ بازده مورد انتظار (درصد)")
    dividend_yield_percent: float = Field(description="بازده سود تقسیمی (درصد)")


class PreferredStockResult(_Base):
    """پاسخ ارزش‌گذاری سهام ممتاز؛ منطق یکسان با مدل رشد صفر.

    Attributes:
        price: قیمت سهام ممتاز
        dividend: سود تقسیمی ثابت سالانه، نمایش مجدد
        required_return: نرخ بازده ورودی (اعشاری)
        required_return_percent: نرخ بازده ورودی (درصد)
        dividend_yield_percent: بازده سود تقسیمی به درصد
    """

    price: float = Field(description="قیمت سهام ممتاز")
    dividend: float = Field(description="سود تقسیمی ثابت سالانه")
    required_return: float = Field(description="نرخ بازده مورد انتظار (اعشاری)")
    required_return_percent: float = Field(description="نرخ بازده مورد انتظار (درصد)")
    dividend_yield_percent: float = Field(description="بازده سود تقسیمی (درصد)")


class AnnualDividendYieldResult(_Base):
    """پاسخ بازده سالانه سود تقسیمی؛ معادل `annual_dividend_yield_percent`.

    Attributes:
        dividend_yield_percent: بازده سالانه به درصد
        dividend: سود تقسیمی ورودی، نمایش مجدد
        price: قیمت ورودی، نمایش مجدد
    """

    dividend_yield_percent: float = Field(description="بازده سالانه سود تقسیمی (درصد)")
    dividend: float = Field(description="سود تقسیمی سالانه")
    price: float = Field(description="قیمت سهام")


class ExpectedReturnResult(_Base):
    """پاسخ بازده مورد انتظار؛ معادل `ExpectedReturnBreakdown`.

    Attributes:
        r: کل بازده مورد انتظار (اعشاری)
        total_percent: کل بازده مورد انتظار (درصد)؛ نام فیلد معادل property دامنه
        dividend_yield: بازده سود تقسیمی (اعشاری)
        dividend_yield_percent: بازده سود تقسیمی (درصد)
        capital_gains_yield: بازده رشد سرمایه (اعشاری)
        capital_gains_yield_percent: بازده رشد سرمایه (درصد)
    """

    r: float = Field(description="کل بازده مورد انتظار (اعشاری)")
    total_percent: float = Field(description="کل بازده مورد انتظار (درصد)")
    dividend_yield: float = Field(description="بازده سود تقسیمی (اعشاری)")
    dividend_yield_percent: float = Field(description="بازده سود تقسیمی (درصد)")
    capital_gains_yield: float = Field(description="بازده رشد سرمایه (اعشاری)")
    capital_gains_yield_percent: float = Field(description="بازده رشد سرمایه (درصد)")


class CapmResult(_Base):
    """پاسخ مدل CAPM؛ معادل `CapmBreakdown`.

    Attributes:
        required_return: نرخ بازده مورد انتظار سهام (اعشاری)
        required_return_percent: نرخ بازده مورد انتظار سهام (درصد)
        risk_free_rate: نرخ بدون ریسک (اعشاری)
        risk_free_rate_percent: نرخ بدون ریسک (درصد)
        beta: ضریب بتای سهام
        market_return: بازده مورد انتظار بازار (اعشاری)
        market_return_percent: بازده مورد انتظار بازار (درصد)، نمایش دامنه ندارد
        market_risk_premium: صرف ریسک بازار rₘ − r_f (اعشاری)
        market_risk_premium_percent: صرف ریسک بازار (درصد)
        risk_premium: صرف ریسک سهام β × (rₘ − r_f) (اعشاری)
        risk_premium_percent: صرف ریسک سهام (درصد)
    """

    required_return: float = Field(description="نرخ بازده مورد انتظار سهام (اعشاری)")
    required_return_percent: float = Field(description="نرخ بازده مورد انتظار سهام (درصد)")
    risk_free_rate: float = Field(description="نرخ بدون ریسک (اعشاری)")
    risk_free_rate_percent: float = Field(description="نرخ بدون ریسک (درصد)")
    beta: float = Field(description="ضریب بتای سهام")
    market_return: float = Field(description="بازده مورد انتظار بازار (اعشاری)")
    market_return_percent: Optional[float] = Field(
        default=None, description="بازده مورد انتظار بازار (درصد)"
    )
    market_risk_premium: float = Field(description="صرف ریسک بازار (اعشاری)")
    market_risk_premium_percent: float = Field(description="صرف ریسک بازار (درصد)")
    risk_premium: float = Field(description="صرف ریسک سهام (اعشاری)")
    risk_premium_percent: float = Field(description="صرف ریسک سهام (درصد)")


class SupernormalScheduleRow(_Base):
    """یک سطر زمان‌بندی سود تقسیمی رشد غیرعادی؛ معادل دامنه.

    Attributes:
        period: شماره سال دوره غیرعادی؛ برای سطر انتهای دوره صفر
        growth_rate: نرخ رشد سال (اعشاری)
        growth_rate_percent: نرخ رشد سال (درصد)
        dividend: سود تقسیمی سال
        present_value: ارزش فعلی سود تقسیمی سال
        is_terminal: آیا سطر مربوط به ارزش انتهای دوره است
    """

    period: int = Field(description="شماره سال دوره غیرعادی؛ صفر برای سطر انتهای دوره")
    growth_rate: float = Field(description="نرخ رشد سال (اعشاری)")
    growth_rate_percent: float = Field(description="نرخ رشد سال (درصد)")
    dividend: float = Field(description="سود تقسیمی سال")
    present_value: float = Field(description="ارزش فعلی سود تقسیمی سال")
    is_terminal: bool = Field(description="آیا سطر مربوط به ارزش انتهای دوره است")


class SupernormalResult(_Base):
    """پاسخ مدل رشد غیرعادی؛ معادل `SupernormalResult` دامنه.

    Attributes:
        p0: قیمت فعلی سهام
        dividends: سودهای تقسیمی دوره غیرعادی (D₁ تا Dₙ)
        d_terminal: سود تقسیمی سال نخست پس از دوره غیرعادی (Dₙ₊₁)
        p_terminal: قیمت انتهای دوره غیرعادی (Pₙ)
        pv_dividends: ارزش فعلی سودهای تقسیمی دوره غیرعادی
        pv_dividends_total: مجموع ارزش فعلی سودهای تقسیمی دوره غیرعادی
        pv_p_terminal: ارزش فعلی قیمت انتهای دوره
        schedule: زمان‌بندی سطرهای دوره غیرعادی به‌همراه سطر انتهای دوره؛
            در نمونه دامنه نیست و لایه endpoint آن را از `supernormal_schedule` می‌سازد
    """

    p0: float = Field(description="قیمت فعلی سهام (P₀)")
    dividends: List[float] = Field(description="سودهای تقسیمی دوره غیرعادی")
    d_terminal: float = Field(description="سود تقسیمی سال نخست پس از دوره غیرعادی")
    p_terminal: float = Field(description="قیمت انتهای دوره غیرعادی (Pₙ)")
    pv_dividends: List[float] = Field(description="ارزش فعلی سودهای تقسیمی دوره غیرعادی")
    pv_dividends_total: float = Field(description="مجموع ارزش فعلی سودهای دوره غیرعادی")
    pv_p_terminal: float = Field(description="ارزش فعلی قیمت انتهای دوره")
    schedule: Optional[List[SupernormalScheduleRow]] = Field(
        default=None, description="زمان‌بندی سودهای تقسیمی"
    )


class GrowthOpportunitiesResult(_Base):
    """پاسخ مدل فرصت‌های رشد؛ معادل `GrowthOpportunitiesBreakdown`.

    Attributes:
        total_value: قیمت کل سهام
        no_growth_value: ارزش سهام بدون رشد (EPS / r)
        npvgo: ارزش فعلی خالص فرصت‌های رشد
        growth_share_percent: سهم فرصت‌های رشد از کل ارزش (درصد)
    """

    total_value: float = Field(description="قیمت کل سهام")
    no_growth_value: float = Field(description="ارزش سهام بدون رشد (EPS / r)")
    npvgo: float = Field(description="ارزش فعلی خالص فرصت‌های رشد")
    growth_share_percent: float = Field(description="سهم فرصت‌های رشد از کل ارزش (درصد)")


class RetentionCurvePointResult(_Base):
    """نقطهٔ منحنی نگهداری سود؛ معادل `RetentionCurvePoint` دامنه."""

    retention_ratio: float = Field(description="نسبت نگهداری سود (اعشاری)")
    retention_ratio_percent: float = Field(description="نسبت نگهداری سود (درصد)")
    sustainable_growth: float = Field(description="نرخ رشد پایدار (اعشاری)")
    sustainable_growth_percent: float = Field(description="نرخ رشد پایدار (درصد)")
    price: Optional[float] = Field(description="قیمت؛ null برای اختلاف نامعتبر رشد و بازده")
    npvgo: Optional[float] = Field(description="ارزش فرصت‌های رشد؛ null برای نقطهٔ نامعتبر")


class SustainableGrowthResult(_Base):
    """پاسخ رشد پایدار؛ آینهٔ `SustainableGrowthBreakdown` دامنه."""

    eps: float = Field(description="سود هر سهم سال آینده")
    required_return: float = Field(description="نرخ بازده مورد انتظار (اعشاری)")
    required_return_percent: float = Field(description="نرخ بازده مورد انتظار (درصد)")
    roe: float = Field(description="بازده حقوق صاحبان سهام (اعشاری)")
    roe_percent: float = Field(description="بازده حقوق صاحبان سهام (درصد)")
    retention_ratio: float = Field(description="نسبت نگهداری سود (اعشاری)")
    retention_ratio_percent: float = Field(description="نسبت نگهداری سود (درصد)")
    payout_ratio: float = Field(description="نسبت تقسیم سود (اعشاری)")
    payout_ratio_percent: float = Field(description="نسبت تقسیم سود (درصد)")
    sustainable_growth: float = Field(description="نرخ رشد پایدار (اعشاری)")
    sustainable_growth_percent: float = Field(description="نرخ رشد پایدار (درصد)")
    next_dividend: float = Field(description="سود تقسیمی سال آینده (D₁)")
    price: float = Field(description="قیمت سهام")
    no_growth_value: float = Field(description="ارزش سهام بدون رشد")
    npvgo: float = Field(description="ارزش فعلی خالص فرصت‌های رشد")
    growth_share_percent: float = Field(description="سهم فرصت‌های رشد از ارزش (درصد)")
    justified_pe: float = Field(description="نسبت قیمت به سود توجیه‌شده")
    growth_creates_value: bool = Field(description="آیا ROE از بازده مورد انتظار بیشتر است")
    retention_curve: List[RetentionCurvePointResult] = Field(description="منحنی نگهداری سود؛ ده نقطه")


class PegInterpretation(_Base):
    """پاسخ تفسیر نسبت PEG؛ معادل `PegInterpretation` دامنه.

    Attributes:
        category: دسته معنایی (very_undervalued، undervalued، fair، near_fair، overvalued)
        level: شدت پیام (success، info، warning، error)
        message: متن پیام کاربر
    """

    category: str = Field(description="دسته معنایی تفسیر")
    level: str = Field(description="شدت پیام برای انتخاب نوع نمایش")
    message: str = Field(description="متن پیام کاربر")


class PegResult(_Base):
    """پاسخ نسبت PEG همراه تفسیر آن.

    Attributes:
        peg: نسبت PEG محاسبه‌شده
        pe_ratio: نسبت P/E ورودی
        growth_rate_percent: نرخ رشد سالانه سود ورودی (درصد)
        interpretation: تفسیر نسبت بر اساس آستانه‌های استاندارد
    """

    peg: float = Field(description="نسبت PEG")
    pe_ratio: float = Field(description="نسبت P/E ورودی")
    growth_rate_percent: float = Field(description="نرخ رشد سالانه سود ورودی (درصد)")
    interpretation: PegInterpretation = Field(description="تفسیر نسبت PEG")


class RiskPremiumResult(_Base):
    """پاسخ حق‌الریسک سهام در مقایسه با اوراق قرضه.

    Attributes:
        risk_premium_percent: حق‌الریسک بر حسب واحد درصد
        required_return: نرخ بازده ورودی (اعشاری)
        required_return_percent: نرخ بازده ورودی (درصد)
        bond_rate_percent: نرخ اوراق قرضه ورودی (درصد)
    """

    risk_premium_percent: float = Field(description="حق‌الریسک (واحد درصد)")
    required_return: float = Field(description="نرخ بازده مورد انتظار سهام (اعشاری)")
    required_return_percent: float = Field(description="نرخ بازده مورد انتظار سهام (درصد)")
    bond_rate_percent: float = Field(description="نرخ اوراق قرضه مشابه (درصد)")


# ---------------------------------------------------------------------------
# مدل‌های درخواست — بدنه JSON ورودی endpointها
# ---------------------------------------------------------------------------

class SinglePeriodRequest(_RequestBase):
    """ورودی مدل تک‌دوره‌ای؛ `P₀ = (D₁ + P₁) / (1 + r)`."""

    d1: float = Field(gt=0, description="سود تقسیمی مورد انتظار پایان سال")
    p1: float = Field(gt=0, description="قیمت مورد انتظار پایان سال")
    r: float = Field(gt=0, description="نرخ بازده مورد انتظار (اعشاری)")


class GordonRequest(_RequestBase):
    """ورودی مدل رشد ثابت گوردون؛ `P = D₀(1+g) / (r − g)`."""

    d0: float = Field(gt=0, description="سود تقسیمی فعلی")
    g: float = Field(description="نرخ رشد ثابت (اعشاری)، بازه دامنه: ۰ تا ۲")
    r: float = Field(gt=0, description="نرخ بازده مورد انتظار (اعشاری)")


class ZeroGrowthRequest(_RequestBase):
    """ورودی مدل رشد صفر؛ `P = D / r`."""

    d: float = Field(gt=0, description="سود تقسیمی ثابت")
    r: float = Field(gt=0, description="نرخ بازده مورد انتظار (اعشاری)")


class PreferredStockRequest(_RequestBase):
    """ورودی ارزش‌گذاری سهام ممتاز؛ `P = D / r`."""

    d: float = Field(gt=0, description="سود تقسیمی ثابت سالانه")
    r: float = Field(gt=0, description="نرخ بازده مورد انتظار (اعشاری)")


class AnnualDividendYieldRequest(_RequestBase):
    """ورودی بازده سالانه سود تقسیمی؛ `(D / P) × 100`."""

    dividend: float = Field(gt=0, description="سود تقسیمی سالانه")
    price: float = Field(gt=0, description="قیمت سهام")


class ExpectedReturnRequest(_RequestBase):
    """ورودی بازده مورد انتظار؛ `r = (D₁ / P₀) + g`."""

    d1: float = Field(gt=0, description="سود تقسیمی مورد انتظار سال آینده")
    p0: float = Field(gt=0, description="قیمت فعلی سهام")
    g: float = Field(description="نرخ رشد سود تقسیمی (اعشاری)، بازه دامنه: ۰ تا ۲")


class CapmRequest(_RequestBase):
    """ورودی مدل CAPM؛ `r = r_f + β × (r_m − r_f)`."""

    risk_free_rate: float = Field(gt=0, description="نرخ بدون ریسک (اعشاری)")
    beta: float = Field(gt=0, description="ضریب بتای سهام")
    market_return: float = Field(gt=0, description="بازده مورد انتظار بازار (اعشاری)")


class SupernormalRequest(_RequestBase):
    """ورودی مدل رشد غیرعادی چندمرحله‌ای."""

    d0: float = Field(gt=0, description="سود تقسیمی فعلی")
    growth_rates: List[float] = Field(
        description="نرخ‌های رشد هر سال دوره غیرعادی (اعشاری)؛ طول باید با years برابر باشد"
    )
    years: int = Field(ge=1, description="تعداد سال‌های دوره غیرعادی")
    g_constant: float = Field(description="نرخ رشد ثابت پس از دوره غیرعادی (اعشاری)")
    r: float = Field(gt=0, description="نرخ بازده مورد انتظار (اعشاری)")


class DividendProjectionRequest(_RequestBase):
    """ورودی پیش‌بینی سود تقسیمی؛ `Dₜ = D₀(1+g)ᵗ`."""

    d0: float = Field(gt=0, description="سود تقسیمی فعلی")
    g: float = Field(description="نرخ رشد ثابت (اعشاری)، بازه دامنه: ۰ تا ۲")
    periods: int = Field(ge=1, description="تعداد دوره‌های پیش‌بینی")


class DividendProjectionResult(_Base):
    """پاسخ پیش‌بینی سود تقسیمی.

    Attributes:
        dividends: سودهای تقسیمی پیش‌بینی‌شده از دوره ۱ تا periods
        periods: تعداد دوره‌های پیش‌بینی
    """

    dividends: List[float] = Field(description="سودهای تقسیمی پیش‌بینی‌شده")
    periods: int = Field(description="تعداد دوره‌های پیش‌بینی")


class GrowthOpportunitiesRequest(_RequestBase):
    """ورودی مدل فرصت‌های رشد؛ `P = (EPS / r) + NPVGO`."""

    eps: float = Field(gt=0, description="سود هر سهم")
    r: float = Field(gt=0, description="نرخ بازده مورد انتظار (اعشاری)")
    npvgo: float = Field(description="ارزش فعلی خالص فرصت‌های رشد؛ می‌تواند منفی باشد")


class SustainableGrowthRequest(_RequestBase):
    """ورودی رشد پایدار؛ NPVGO از ROE و نسبت نگهداری سود استخراج می‌شود."""

    eps: float = Field(gt=0, description="سود هر سهم سال آینده")
    r: float = Field(gt=0, description="نرخ بازده مورد انتظار (اعشاری)")
    roe: float = Field(gt=0, description="بازده حقوق صاحبان سهام (اعشاری)؛ حداکثر ۲ در دامنه")
    retention_ratio: float = Field(ge=0, lt=1, description="نسبت نگهداری سود (اعشاری)")


class PegRequest(_RequestBase):
    """ورودی نسبت PEG؛ `PEG = (P/E) / نرخ رشد سالانه`."""

    pe_ratio: float = Field(gt=0, description="نسبت P/E")
    growth_rate_percent: float = Field(
        gt=0, le=100, description="نرخ رشد سالانه سود (درصد)؛ دامنه آن را بالای ۱۰۰ غیرمنطقی می‌داند"
    )


class RiskPremiumRequest(_RequestBase):
    """ورودی حق‌الریسک سهام نسبت به اوراق قرضه."""

    required_return: float = Field(gt=0, description="نرخ بازده مورد انتظار سهام (اعشاری)")
    bond_rate_percent: float = Field(gt=0, description="نرخ اوراق قرضه مشابه (درصد)")


class WaccRequest(_RequestBase):
    """ورودی میانگین موزون هزینه سرمایه؛ کرانه‌های عددی در دامنه اعمال می‌شوند."""

    equity: float = Field(description="ارزش بازار حقوق صاحبان سهام")
    debt: float = Field(description="ارزش بازار بدهی؛ صفر برای بنگاه تمام‌سهامی مجاز است")
    cost_of_equity: float = Field(description="هزینه حقوق صاحبان سهام (اعشاری)")
    cost_of_debt: float = Field(description="هزینه بدهی قبل از مالیات (اعشاری)")
    tax_rate: float = Field(description="نرخ مالیات (اعشاری)")


class WaccResult(_Base):
    """پاسخ WACC؛ معادل `WaccBreakdown` دامنه."""

    wacc: float = Field(description="نرخ WACC (اعشاری)")
    wacc_percent: float = Field(description="نرخ WACC (درصد)")
    equity: float = Field(description="ارزش بازار حقوق صاحبان سهام")
    debt: float = Field(description="ارزش بازار بدهی")
    total_capital: float = Field(description="مجموع سرمایه (E + D)")
    equity_weight: float = Field(description="وزن حقوق صاحبان سهام (اعشاری)")
    debt_weight: float = Field(description="وزن بدهی (اعشاری)")
    equity_weight_percent: float = Field(description="وزن حقوق صاحبان سهام (درصد)")
    debt_weight_percent: float = Field(description="وزن بدهی (درصد)")
    cost_of_equity: float = Field(description="هزینه حقوق صاحبان سهام (اعشاری)")
    cost_of_equity_percent: float = Field(description="هزینه حقوق صاحبان سهام (درصد)")
    cost_of_debt: float = Field(description="هزینه بدهی قبل از مالیات (اعشاری)")
    cost_of_debt_percent: float = Field(description="هزینه بدهی قبل از مالیات (درصد)")
    after_tax_cost_of_debt: float = Field(description="هزینه بدهی بعد از مالیات (اعشاری)")
    after_tax_cost_of_debt_percent: float = Field(description="هزینه بدهی بعد از مالیات (درصد)")
    tax_rate: float = Field(description="نرخ مالیات (اعشاری)")
    tax_rate_percent: float = Field(description="نرخ مالیات (درصد)")


class CashFlowProjectionInput(_RequestBase):
    """یک سال اجزای FCFF؛ سال = اندیس در فهرست درخواست."""

    ebit: float = Field(description="سود عملیاتی قبل از بهره و مالیات")
    depreciation: float = Field(description="استهلاک و هزینه‌های غیرنقدی")
    capex: float = Field(description="مخارج سرمایه‌ای؛ مثبت = خروج نقد")
    delta_nwc: float = Field(description="تغییر سرمایه در گردش؛ مثبت = افزایش NWC")


class FcffYearRowResult(_Base):
    """یک سطر جدول سالانه DCF؛ معادل `FcffYearRow` دامنه."""

    year: int = Field(description="شماره سال (۱ تا n)")
    ebit: float = Field(description="سود عملیاتی سال")
    nopat: float = Field(description="سود عملیاتی بعد از مالیات")
    depreciation: float = Field(description="استهلاک")
    capex: float = Field(description="مخارج سرمایه‌ای")
    delta_nwc: float = Field(description="تغییر سرمایه در گردش")
    fcff: float = Field(description="جریان نقدی آزاد بنگاه")
    discount_factor: float = Field(description="ضریب تنزیل")
    present_value: float = Field(description="ارزش فعلی FCFF سال")


class DcfRequest(_RequestBase):
    """ورودی ارزش‌گذاری DCF؛ کرانه‌های عددی در دامنه اعمال می‌شوند."""

    projections: List[CashFlowProjectionInput] = Field(
        min_length=1,
        max_length=50,
        description="پیش‌بینی سالانه اجزای FCFF؛ سال = اندیس از ۱",
    )
    wacc: float = Field(description="نرخ WACC / تنزیل (اعشاری)")
    terminal_growth: float = Field(description="نرخ رشد پایانی (اعشاری)")
    shares_outstanding: float = Field(description="تعداد سهام")
    tax_rate: float = Field(description="نرخ مالیات سراسری (اعشاری)")
    cash: float = Field(default=0.0, description="موجودی نقد و معادل")
    debt: float = Field(default=0.0, description="بدهی بهره‌دار")
    minority_interest: float = Field(default=0.0, description="منافع اقلیت")
    preferred_equity: float = Field(default=0.0, description="سهام ممتاز")


class DcfResult(_Base):
    """پاسخ DCF؛ معادل `DcfBreakdown` دامنه."""

    enterprise_value: float = Field(description="ارزش بنگاه (EV)")
    equity_value: float = Field(description="ارزش حقوق صاحبان سهام")
    value_per_share: float = Field(description="ارزش هر سهم")
    wacc: float = Field(description="نرخ WACC (اعشاری)")
    wacc_percent: float = Field(description="نرخ WACC (درصد)")
    terminal_growth: float = Field(description="نرخ رشد پایانی (اعشاری)")
    terminal_growth_percent: float = Field(description="نرخ رشد پایانی (درصد)")
    terminal_value: float = Field(description="ارزش انتهای دوره (تنزیل‌نشده)")
    pv_terminal_value: float = Field(description="ارزش فعلی ارزش انتهای دوره")
    pv_fcff_total: float = Field(description="مجموع ارزش فعلی FCFFهای دوره صریح")
    cash: float = Field(description="موجودی نقد")
    debt: float = Field(description="بدهی")
    minority_interest: float = Field(description="منافع اقلیت")
    preferred_equity: float = Field(description="سهام ممتاز")
    shares_outstanding: float = Field(description="تعداد سهام")
    terminal_value_share_percent: float = Field(
        description="سهم ارزش فعلی انتهای دوره از EV (درصد)"
    )
    years: List[FcffYearRowResult] = Field(description="جدول سالانه پیش‌بینی")


class ScenarioRowResult(_Base):
    """سطر نتیجهٔ سناریو؛ آینهٔ `ScenarioRow` دامنه."""

    name: str = Field(description="نام سناریو")
    probability: float = Field(description="احتمال سناریو (اعشاری)")
    probability_percent: float = Field(description="احتمال سناریو (درصد)")
    wacc: float = Field(description="نرخ WACC (اعشاری)")
    wacc_percent: float = Field(description="نرخ WACC (درصد)")
    terminal_growth: float = Field(description="نرخ رشد پایانی (اعشاری)")
    terminal_growth_percent: float = Field(description="نرخ رشد پایانی (درصد)")
    enterprise_value: float = Field(description="ارزش بنگاه")
    equity_value: float = Field(description="ارزش حقوق صاحبان سهام")
    value_per_share: float = Field(description="ارزش هر سهم")
    terminal_value_share_percent: float = Field(description="سهم ارزش پایانی از EV (درصد)")
    weighted_value_per_share: float = Field(description="سهم وزنی ارزش هر سهم")
    upside: Optional[float] = Field(description="بازده بالقوه (اعشاری)؛ بدون قیمت بازار null")
    upside_percent: Optional[float] = Field(description="بازده بالقوه (درصد)؛ بدون قیمت بازار null")


class DcfScenarioResult(_Base):
    """پاسخ سناریوهای وزنی DCF؛ آینهٔ `ScenarioValuationResult` دامنه."""

    scenarios: List[ScenarioRowResult] = Field(description="نتایج سناریوها به ترتیب ورودی")
    expected_value_per_share: float = Field(description="ارزش مورد انتظار هر سهم")
    expected_enterprise_value: float = Field(description="ارزش مورد انتظار بنگاه")
    expected_equity_value: float = Field(description="ارزش مورد انتظار حقوق صاحبان سهام")
    std_dev_value_per_share: float = Field(description="انحراف معیار وزنی ارزش هر سهم")
    min_value_per_share: float = Field(description="کمترین ارزش هر سهم")
    max_value_per_share: float = Field(description="بیشترین ارزش هر سهم")
    worst_scenario: str = Field(description="نام نخستین سناریو با کمترین ارزش")
    best_scenario: str = Field(description="نام نخستین سناریو با بیشترین ارزش")
    market_price: Optional[float] = Field(description="قیمت بازار اختیاری")
    expected_upside: Optional[float] = Field(description="بازده بالقوه مورد انتظار (اعشاری)")
    expected_upside_percent: Optional[float] = Field(description="بازده بالقوه مورد انتظار (درصد)")
    probability_of_upside: Optional[float] = Field(description="احتمال ارزش بالاتر از بازار (اعشاری)")
    probability_of_upside_percent: Optional[float] = Field(description="احتمال ارزش بالاتر از بازار (درصد)")


class DcfScenarioInput(_RequestBase):
    """ورودی یک سناریوی نام‌گذاری‌شدهٔ DCF."""

    name: str = Field(min_length=1, description="نام یکتای سناریو")
    probability: float = Field(description="احتمال سناریو؛ بین صفر و یک")
    projections: List[CashFlowProjectionInput] = Field(
        min_length=1, max_length=50, description="پیش‌بینی سالانه اجزای FCFF",
    )
    wacc: float = Field(description="نرخ WACC سناریو (اعشاری)")
    terminal_growth: float = Field(description="نرخ رشد پایانی سناریو (اعشاری)")


class DcfScenarioRequest(_RequestBase):
    """ورودی سناریوهای DCF؛ احتمال‌ها در دامنه بدون نرمال‌سازی بررسی می‌شوند."""

    scenarios: List[DcfScenarioInput] = Field(
        min_length=MIN_SCENARIOS, max_length=MAX_SCENARIOS,
        description="سناریوهای نام‌گذاری‌شده؛ مجموع احتمال‌ها برابر یک",
    )
    shares_outstanding: float = Field(description="تعداد سهام مشترک")
    tax_rate: float = Field(description="نرخ مالیات مشترک (اعشاری)")
    cash: float = Field(default=0.0, description="موجودی نقد و معادل")
    debt: float = Field(default=0.0, description="بدهی بهره‌دار")
    minority_interest: float = Field(default=0.0, description="منافع اقلیت")
    preferred_equity: float = Field(default=0.0, description="سهام ممتاز")
    market_price: Optional[float] = Field(default=None, description="قیمت بازار اختیاری")


class DcfSensitivityRequest(DcfRequest):
    """ورودی ماتریس حساسیت DCF؛ فیلدهای DCF را به ارث می‌برد و فقط
    پارامترهای شبکه (گام‌ها و تعداد نقاط محورها) را اضافه می‌کند.

    پیش‌فرض‌ها از ثابت‌های دامنه می‌آیند تا عددها دو جا تکرار نشوند؛
    اعتبارسنجی گام‌ها و تعداد نقاط در دامنه انجام می‌شود.
    """

    wacc_step: float = Field(
        default=DEFAULT_WACC_STEP, description="فاصله نقاط محور WACC (اعشاری)"
    )
    growth_step: float = Field(
        default=DEFAULT_GROWTH_STEP, description="فاصله نقاط محور رشد پایانی (اعشاری)"
    )
    wacc_points: int = Field(
        default=DEFAULT_SENSITIVITY_POINTS,
        description="تعداد نقاط محور WACC (فرد؛ ۳ تا ۱۱)",
    )
    growth_points: int = Field(
        default=DEFAULT_SENSITIVITY_POINTS,
        description="تعداد نقاط محور رشد پایانی (فرد؛ ۳ تا ۱۱)",
    )


class DcfSensitivityResult(_Base):
    """پاسخ ماتریس حساسیت DCF؛ معادل `DcfSensitivityResult` دامنه.

    سطرها محور WACC و ستون‌ها محور رشد پایانی هستند؛ `null` یعنی ترکیب
    نامعتبر (مثلاً نقض حداقل اختلاف WACC و رشد).

    Attributes:
        wacc_values: محور سطرها (اعشاری)، صعودی و مرکزچین روی WACC پایه
        growth_values: محور ستون‌ها (اعشاری)، صعودی و مرکزچین روی رشد پایه
        wacc_values_percent: محور WACC (درصد)
        growth_values_percent: محور رشد پایانی (درصد)
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

    wacc_values: List[float] = Field(description="محور سطرها: مقادیر WACC (اعشاری)")
    growth_values: List[float] = Field(
        description="محور ستون‌ها: مقادیر رشد پایانی (اعشاری)"
    )
    wacc_values_percent: List[float] = Field(description="محور WACC (درصد)")
    growth_values_percent: List[float] = Field(description="محور رشد پایانی (درصد)")
    value_per_share: List[List[Optional[float]]] = Field(
        description="ماتریس ارزش هر سهم؛ null برای ترکیب نامعتبر"
    )
    enterprise_value: List[List[Optional[float]]] = Field(
        description="ماتریس ارزش بنگاه؛ null برای ترکیب نامعتبر"
    )
    base_wacc: float = Field(description="نرخ WACC حالت پایه (اعشاری)")
    base_terminal_growth: float = Field(description="نرخ رشد پایانی حالت پایه (اعشاری)")
    base_row: int = Field(description="اندیس WACC پایه در محور سطرها")
    base_col: int = Field(description="اندیس رشد پایه در محور ستون‌ها")
    base_value_per_share: float = Field(description="ارزش هر سهم در حالت پایه")
    base_enterprise_value: float = Field(description="ارزش بنگاه در حالت پایه")
    valid_cells: int = Field(description="تعداد سلول‌های معتبر ماتریس")
    total_cells: int = Field(description="تعداد کل سلول‌های ماتریس")


class ReverseDcfRequest(_RequestBase):
    """ورودی DCF معکوس؛ قیمت بازار برای یافتن رشد پایانی تلویحی.

    `terminal_growth` اختیاری، نرخ رشد پایانی خود تحلیل‌گر است و فقط برای
    محاسبه `growth_gap` استفاده می‌شود (به `reference_terminal_growth` دامنه نگاشت می‌شود).
    """

    projections: List[CashFlowProjectionInput] = Field(
        min_length=1,
        max_length=50,
        description="پیش‌بینی سالانه اجزای FCFF؛ سال = اندیس از ۱",
    )
    wacc: float = Field(description="نرخ WACC / تنزیل (اعشاری)")
    shares_outstanding: float = Field(description="تعداد سهام")
    tax_rate: float = Field(description="نرخ مالیات سراسری (اعشاری)")
    market_price: float = Field(description="قیمت بازار سهام")
    cash: float = Field(default=0.0, description="موجودی نقد و معادل")
    debt: float = Field(default=0.0, description="بدهی بهره‌دار")
    minority_interest: float = Field(default=0.0, description="منافع اقلیت")
    preferred_equity: float = Field(default=0.0, description="سهام ممتاز")
    terminal_growth: Optional[float] = Field(
        default=None,
        description="نرخ رشد پایانی تحلیل‌گر برای مقایسه (اعشاری)؛ اختیاری",
    )


class ReverseDcfResult(_Base):
    """پاسخ DCF معکوس؛ معادل `ReverseDcfResult` دامنه.

    Attributes:
        status: وضعیت حل (`solved` | `market_price_below_range` | `market_price_above_range`)
        market_price: قیمت بازار ورودی
        implied_growth: رشد پایانی تلویحی (اعشاری)؛ فقط در وضعیت solved
        implied_growth_percent: رشد پایانی تلویحی (درصد)؛ در غیر solved برابر null
        wacc: نرخ WACC (اعشاری)
        wacc_percent: نرخ WACC (درصد)
        search_min_growth: کرانه پایین بازه جستجو (اعشاری)
        search_max_growth: کرانه بالای بازه جستجو (اعشاری)
        value_per_share_at_min_growth: ارزش هر سهم در کرانه پایین
        value_per_share_at_max_growth: ارزش هر سهم در کرانه بالا
        enterprise_value: ارزش بنگاه در رشد تلویحی؛ در غیر solved برابر null
        equity_value: ارزش حقوق صاحبان سهام در رشد تلویحی؛ در غیر solved برابر null
        terminal_value_share_percent: سهم ارزش فعلی انتهای دوره از EV (درصد)
        reference_terminal_growth: نرخ رشد پایانی تحلیل‌گر (اعشاری)
        growth_gap: اختلاف رشد تلویحی و رشد مرجع (اعشاری)
        growth_gap_percent: اختلاف رشد تلویحی و رشد مرجع (درصد)
        message: پیام فارسی برای نمایش به کاربر
    """

    status: str = Field(description="وضعیت حل: solved یا خارج از بازه قیمت")
    market_price: float = Field(description="قیمت بازار سهام (ورودی)")
    implied_growth: Optional[float] = Field(
        default=None, description="رشد پایانی تلویحی (اعشاری)؛ فقط در وضعیت solved"
    )
    implied_growth_percent: Optional[float] = Field(
        default=None, description="رشد پایانی تلویحی (درصد)؛ در غیر solved برابر null"
    )
    wacc: float = Field(description="نرخ WACC (اعشاری)")
    wacc_percent: float = Field(description="نرخ WACC (درصد)")
    search_min_growth: float = Field(description="کرانه پایین بازه جستجوی رشد (اعشاری)")
    search_max_growth: float = Field(description="کرانه بالای بازه جستجوی رشد (اعشاری)")
    value_per_share_at_min_growth: float = Field(
        description="ارزش هر سهم در کرانه پایین بازه جستجو"
    )
    value_per_share_at_max_growth: float = Field(
        description="ارزش هر سهم در کرانه بالای بازه جستجو"
    )
    enterprise_value: Optional[float] = Field(
        default=None, description="ارزش بنگاه در رشد تلویحی؛ در غیر solved برابر null"
    )
    equity_value: Optional[float] = Field(
        default=None, description="ارزش حقوق صاحبان سهام در رشد تلویحی؛ در غیر solved برابر null"
    )
    terminal_value_share_percent: Optional[float] = Field(
        default=None, description="سهم ارزش فعلی انتهای دوره از EV (درصد)"
    )
    reference_terminal_growth: Optional[float] = Field(
        default=None, description="نرخ رشد پایانی تحلیل‌گر (اعشاری)"
    )
    growth_gap: Optional[float] = Field(
        default=None, description="اختلاف رشد تلویحی و رشد مرجع (اعشاری)"
    )
    growth_gap_percent: Optional[float] = Field(
        default=None, description="اختلاف رشد تلویحی و رشد مرجع (درصد)"
    )
    message: str = Field(description="پیام فارسی برای نمایش به کاربر")


# ---------------------------------------------------------------------------
# پاسخ خطا
# ---------------------------------------------------------------------------

class ErrorResponse(_Base):
    """بدنه ثابت پاسخ 400 برای خطاهای دامنه.

    ساختار سه‌فیلدی برای همه خطاهای `ValidationError` و `CalculationError`
    یکسان است تا فرانت‌اند بتواند با یک شروط واحد خطا را نمایش دهد.

    Attributes:
        error_code: کد نوع خطا (VALIDATION_ERROR یا CALCULATION_ERROR)
        message: متن خطای دامنه (فارسی)
        details: جزئیات تکمیلی؛ فعلاً همیشه null است
    """

    error_code: str = Field(description="کد نوع خطا")
    message: str = Field(description="متن خطای دامنه")
    details: Optional[dict] = Field(default=None, description="جزئیات تکمیلی؛ فعلاً null")
