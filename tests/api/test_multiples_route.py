"""تست‌های نقطه پایانی ارزش‌گذاری نسبی با ضریب همتایان.

اجرا از ریشه پروژه:
    python3 -m unittest discover -s tests -t . -v
"""

import unittest

from pydantic import ValidationError as PydanticValidationError

from stock_valuation.api import schemas as s
from stock_valuation.api.routes import multiples as multiples_route
from stock_valuation.domain.errors import ValidationError
from stock_valuation.domain.multiples import MultipleKind


class TestMultiplesRoute(unittest.TestCase):
    """نگاشت درخواست/پاسخ مسیر multiples و خطاهای 400 و 422"""

    @staticmethod
    def _payload(**overrides):
        values = dict(
            kind=MultipleKind.EV_EBITDA,
            metric=500.0,
            shares_outstanding=10.0,
            peers=[
                s.PeerMultipleInput(name="الف", value=10.0),
                s.PeerMultipleInput(name="ب", value=20.0),
                s.PeerMultipleInput(name="ج", value=30.0),
                s.PeerMultipleInput(name="د", value=40.0),
            ],
            cash=100.0,
            debt=300.0,
            minority_interest=50.0,
            preferred_equity=50.0,
        )
        values.update(overrides)
        return s.MultiplesRequest(**values)

    def test_happy_path_hand_computed(self):
        result = multiples_route.multiples(self._payload())
        self.assertEqual(result.kind, MultipleKind.EV_EBITDA)
        self.assertEqual(result.metric, 500.0)
        self.assertEqual(result.statistics.used_count, 4)
        self.assertEqual(result.statistics.excluded_count, 0)
        self.assertEqual(result.statistics.excluded_names, [])
        self.assertEqual(result.statistics.q1, 17.5)
        self.assertEqual(result.statistics.median, 25.0)
        self.assertEqual(result.statistics.q3, 32.5)
        self.assertEqual(result.statistics.mean, 25.0)
        self.assertEqual(result.statistics.min, 10.0)
        self.assertEqual(result.statistics.max, 40.0)
        # EV = 17.5 × 500 = 8750 ← 8750 + 100 − 300 − 50 − 50 = 8450
        self.assertEqual(result.low.multiple, 17.5)
        self.assertEqual(result.low.implied_enterprise_value, 8750.0)
        self.assertEqual(result.low.implied_equity_value, 8450.0)
        self.assertEqual(result.low.value_per_share, 845.0)
        self.assertEqual(result.mid.implied_enterprise_value, 12500.0)
        self.assertEqual(result.mid.value_per_share, 1220.0)
        self.assertEqual(result.high.implied_enterprise_value, 16250.0)
        self.assertEqual(result.high.value_per_share, 1595.0)
        self.assertEqual(result.mean.value_per_share, 1220.0)

    def test_equity_kind_has_no_enterprise_value(self):
        result = multiples_route.multiples(
            self._payload(kind=MultipleKind.PE, metric=100.0)
        )
        self.assertIsNone(result.low.implied_enterprise_value)
        self.assertEqual(result.low.value_per_share, 175.0)
        self.assertEqual(result.mid.value_per_share, 250.0)
        self.assertEqual(result.high.value_per_share, 325.0)

    def test_domain_validation_error_is_400(self):
        # شاخص غیرمثبت از Pydantic عبور می‌کند و دامنه آن را رد می‌کند
        with self.assertRaises(ValidationError):
            multiples_route.multiples(self._payload(metric=-100.0))

    def test_schema_violation_is_422(self):
        with self.assertRaises(PydanticValidationError):
            self._payload(kind="peg")
        with self.assertRaises(PydanticValidationError):
            self._payload(
                peers=[s.PeerMultipleInput(name="الف", value=10.0)]
            )


if __name__ == "__main__":
    unittest.main()
