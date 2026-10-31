"""ارزش‌گذاری نسبی با ضریب‌های همتایان — منطق خالص دامنه.

این ماژول آماره‌های ضریب همتایان را محاسبه می‌کند و ارزش تلویحی هدف را
بر پایه چارک اول، میانه، چارک سوم و میانگین می‌سازد. برای ضریب‌های بنگاهی
(EV/EBITDA و EV/Sales) پل ارزش بنگاه به حقوق صاحبان سهام عیناً از
``domain.bridge`` گرفته می‌شود تا با ``dcf_valuation`` یکسان بماند.

قرارداد خطا:
    ValidationError: ورودی نامعتبر
    CalculationError: نتیجه غیرعددی یا خطای عددی در محاسبه
"""

import logging
import math
import statistics
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Union

from .bridge import enterprise_to_equity
from .errors import CalculationError, ValidationError
from .validators import (
    require_finite_number,
    validate_peer_count,
    validate_positive_number,
    validate_valuation_metric,
)

logger = logging.getLogger(__name__)


class MultipleKind(str, Enum):
    """نوع ضریب نسبی: سه ضریب حقوق صاحبان سهام و دو ضریب بنگاهی"""

    PE = "pe"
    PB = "pb"
    PS = "ps"
    EV_EBITDA = "ev_ebitda"
    EV_SALES = "ev_sales"


# ضریب‌هایی که ابتدا ارزش بنگاه را می‌سازند و سپس با پل EV به حقوق
# صاحبان سهام تبدیل می‌شوند؛ بقیه مستقیماً ارزش حقوق صاحبان سهام می‌دهند.
ENTERPRISE_MULTIPLE_KINDS = frozenset(
    {MultipleKind.EV_EBITDA, MultipleKind.EV_SALES}
)


@dataclass(frozen=True)
class PeerMultiple:
    """ضریب یک شرکت همتا؛ مقدار غیرمثبت در آماره‌ها کنار گذاشته می‌شود

    Attributes:
        name: نام یکتای همتا
        value: ضریب (مثلاً P/E)؛ عدد متناهی
    """

    name: str
    value: float


@dataclass(frozen=True)
class PeerStatistics:
    """آماره‌های ضریب همتایان معتبر (ضریب مثبت) به ترتیب ورودی

    Attributes:
        used_count: تعداد همتایان معتبر استفاده‌شده
        excluded_count: تعداد همتایان کنارگذاشته‌شده (ضریب غیرمثبت)
        excluded_names: نام همتایان کنارگذاشته‌شده به ترتیب ورودی
        mean: میانگین ضریب همتایان معتبر
        median: میانه ضریب همتایان معتبر
        q1: چارک اول با درون‌یابی خطی
        q3: چارک سوم با درون‌یابی خطی
        min: کمترین ضریب معتبر
        max: بیشترین ضریب معتبر
    """

    used_count: int
    excluded_count: int
    excluded_names: List[str]
    mean: float
    median: float
    q1: float
    q3: float
    min: float
    max: float


@dataclass(frozen=True)
class ImpliedCase:
    """ارزش تلویحی بر پایه یک ضریب (چارک، میانه یا میانگین)

    Attributes:
        multiple: ضریب به‌کاررفته
        implied_enterprise_value: ارزش بنگاه تلویحی؛ برای ضریب‌های حقوق
            صاحبان سهام ``None`` است
        implied_equity_value: ارزش حقوق صاحبان سهام تلویحی (منفی کلمپ نمی‌شود)
        value_per_share: ارزش هر سهم تلویحی
    """

    multiple: float
    implied_enterprise_value: Optional[float]
    implied_equity_value: float
    value_per_share: float


@dataclass(frozen=True)
class ImpliedValuation:
    """ارزش تلویحی نسبی: آماره‌های همتایان و چهار حالت ارزش

    Attributes:
        kind: نوع ضریب
        metric: شاخص کل هدف (سود خالص، حقوق صاحبان سهام، درآمد، EBITDA یا فروش)
        statistics: آماره‌های همتایان معتبر
        low: حالت چارک اول (Q1)
        mid: حالت میانه
        high: حالت چارک سوم (Q3)
        mean: حالت میانگین
    """

    kind: MultipleKind
    metric: float
    statistics: PeerStatistics
    low: ImpliedCase
    mid: ImpliedCase
    high: ImpliedCase
    mean: ImpliedCase


def peer_statistics(peers: List[PeerMultiple]) -> PeerStatistics:
    """
    آماره‌های ضریب همتایان با کنارگذاشتن ضریب‌های غیرمثبت

    ضریب غیرمثبت (مثل P/E یک شرکت زیان‌ده) خطا نیست و فقط از آماره‌ها
    حذف می‌شود؛ اما نام خالی یا تکراری و ضریب غیرعددی یا نامتناهی ورودی
    نامعتبرند. چارک‌ها با درون‌یابی خطی روی داده مرتب‌شده محاسبه می‌شوند
    (معادل ``statistics.quantiles(method="inclusive")``) و پس از حذف باید
    حداقل ``MIN_PEERS`` همتای معتبر باقی بماند.

    Args:
        peers (List[PeerMultiple]): فهرست همتایان با نام یکتا و ضریب عددی

    Returns:
        PeerStatistics: آماره‌های همتایان معتبر و گزارش حذف‌شده‌ها

    Raises:
        ValidationError: اگر فهرست نامعتبر یا تعداد همتایان معتبر کم باشد
        CalculationError: اگر آماره‌های محاسبه‌شده متناهی نباشند
    """
    if not isinstance(peers, (list, tuple)) or any(
        not isinstance(peer, PeerMultiple) for peer in peers
    ):
        raise ValidationError("❌ همتایان باید فهرستی از PeerMultiple باشند!")

    seen_names = set()
    used_peers: List[PeerMultiple] = []
    excluded_names: List[str] = []
    for peer in peers:
        if not isinstance(peer.name, str) or not peer.name.strip():
            raise ValidationError("❌ نام همتا باید غیرخالی باشد!")
        name = peer.name.strip()
        if name in seen_names:
            raise ValidationError("❌ نام همتاها باید یکتا باشد!")
        seen_names.add(name)

        if isinstance(peer.value, bool) or not isinstance(peer.value, (int, float)):
            raise ValidationError(f"❌ ضریب همتای «{name}» باید عدد باشد!")
        require_finite_number(peer.value, f"ضریب همتای «{name}»")

        if peer.value <= 0:
            excluded_names.append(name)
        else:
            used_peers.append(peer)

    validate_peer_count(len(used_peers))

    try:
        values = sorted(float(peer.value) for peer in used_peers)
        q1, median, q3 = statistics.quantiles(values, n=4, method="inclusive")
        result = PeerStatistics(
            used_count=len(values),
            excluded_count=len(excluded_names),
            excluded_names=excluded_names,
            mean=sum(values) / len(values),
            median=median,
            q1=q1,
            q3=q3,
            min=values[0],
            max=values[-1],
        )
        if not all(
            math.isfinite(value)
            for value in (
                result.mean,
                result.median,
                result.q1,
                result.q3,
                result.min,
                result.max,
            )
        ):
            raise CalculationError("نتیجه محاسبه نامعتبر است")
        return result
    except (ZeroDivisionError, ValueError, OverflowError) as exc:
        logger.error(f"خطا در محاسبه آماره‌های همتایان: {exc}")
        raise CalculationError("نتیجه محاسبه نامعتبر است") from exc


def implied_valuation(
    kind: Union[MultipleKind, str],
    metric: float,
    shares_outstanding: float,
    peers: List[PeerMultiple],
    cash: float = 0.0,
    debt: float = 0.0,
    minority_interest: float = 0.0,
    preferred_equity: float = 0.0,
) -> ImpliedValuation:
    """
    ارزش تلویحی هدف با ضریب‌های همتایان

    برای ضریب‌های حقوق صاحبان سهام (P/E، P/B و P/S) ارزش حقوق صاحبان
    سهام = ضریب × شاخص هدف و ارزش هر سهم تقسیم آن بر تعداد سهام است.
    برای ضریب‌های بنگاهی (EV/EBITDA و EV/Sales) ابتدا ارزش بنگاه محاسبه
    و سپس با ``enterprise_to_equity`` (همان پل ``dcf_valuation``) به ارزش
    حقوق صاحبان سهام تبدیل می‌شود. شاخص هدف باید مثبت باشد؛ ضریب‌ها برای
    سود یا فروش غیرمثبت معنای اقتصادی ندارند. ارزش منفی کلمپ نمی‌شود.

    Args:
        kind: نوع ضریب؛ یکی از مقادیر ``MultipleKind`` یا رشته معادل آن
        metric: شاخص کل هدف (سود خالص، حقوق صاحبان سهام، درآمد، EBITDA یا
            فروش)؛ عدد متناهی و مثبت
        shares_outstanding: تعداد سهام هدف؛ عدد متناهی و مثبت
        peers: فهرست همتایان با ضریب مثبت
        cash: موجودی نقد هدف؛ فقط برای ضریب‌های بنگاهی
        debt: بدهی بهره‌دار هدف؛ فقط برای ضریب‌های بنگاهی
        minority_interest: منافع اقلیت هدف؛ فقط برای ضریب‌های بنگاهی
        preferred_equity: سهام ممتاز هدف؛ فقط برای ضریب‌های بنگاهی

    Returns:
        ImpliedValuation: آماره‌های همتایان و حالت‌های چارک اول، میانه،
        چارک سوم و میانگین

    Raises:
        ValidationError: در صورت نامعتبر بودن نوع ضریب، شاخص، سهام یا همتایان
        CalculationError: اگر نتیجه محاسبه متناهی نباشد
    """
    try:
        kind = MultipleKind(kind)
    except (TypeError, ValueError) as exc:
        raise ValidationError(
            "❌ نوع ضریب باید یکی از pe، pb، ps، ev_ebitda یا ev_sales باشد!"
        ) from exc

    validate_valuation_metric(metric, "شاخص هدف")
    require_finite_number(shares_outstanding, "تعداد سهام")
    validate_positive_number(shares_outstanding, "تعداد سهام")

    statistics_result = peer_statistics(peers)
    is_enterprise = kind in ENTERPRISE_MULTIPLE_KINDS

    def build_case(multiple: float) -> ImpliedCase:
        """ساخت یک حالت ارزش از ضریب داده‌شده"""
        if is_enterprise:
            enterprise_value = multiple * metric
            bridge = enterprise_to_equity(
                enterprise_value,
                cash,
                debt,
                minority_interest,
                preferred_equity,
                shares_outstanding,
            )
            return ImpliedCase(
                multiple=multiple,
                implied_enterprise_value=enterprise_value,
                implied_equity_value=bridge.equity_value,
                value_per_share=bridge.value_per_share,
            )

        equity_value = multiple * metric
        return ImpliedCase(
            multiple=multiple,
            implied_enterprise_value=None,
            implied_equity_value=equity_value,
            value_per_share=equity_value / shares_outstanding,
        )

    try:
        result = ImpliedValuation(
            kind=kind,
            metric=metric,
            statistics=statistics_result,
            low=build_case(statistics_result.q1),
            mid=build_case(statistics_result.median),
            high=build_case(statistics_result.q3),
            mean=build_case(statistics_result.mean),
        )
        for case in (result.low, result.mid, result.high, result.mean):
            numbers = [
                case.multiple,
                case.implied_equity_value,
                case.value_per_share,
            ]
            if case.implied_enterprise_value is not None:
                numbers.append(case.implied_enterprise_value)
            if not all(math.isfinite(value) for value in numbers):
                raise CalculationError("نتیجه محاسبه نامعتبر است")
        return result
    except (ZeroDivisionError, ValueError, OverflowError) as exc:
        logger.error(f"خطا در محاسبه ارزش تلویحی نسبی: {exc}")
        raise CalculationError("نتیجه محاسبه نامعتبر است") from exc
