"""قراردادهای Pydantic مدل‌های سهام عادی و سود تقسیمی."""

from typing import List, Optional

from pydantic import Field

from .common import _Base, _RequestBase


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
