"""تست‌های نقطه پایانی خلاصه زمین فوتبال.

اجرا از ریشه پروژه:
    python3 -m unittest discover -s tests -t . -v
"""

import unittest

from pydantic import ValidationError as PydanticValidationError

from stock_valuation.api import schemas as s
from stock_valuation.api.routes import football_field as football_field_route
from stock_valuation.domain.errors import ValidationError


class TestFootballFieldRoute(unittest.TestCase):
    """نگاشت درخواست/پاسخ مسیر football-field و خطاهای 400 و 422"""

    @staticmethod
    def _payload(market_price=150.0):
        return s.FootballFieldRequest(
            ranges=[
                s.ValuationRangeInput(
                    method="DCF", low=100.0, mid=150.0, high=200.0
                ),
                s.ValuationRangeInput(
                    method="Multiples", low=120.0, mid=140.0, high=180.0
                ),
                s.ValuationRangeInput(
                    method="Scenarios", low=90.0, mid=160.0, high=210.0
                ),
            ],
            market_price=market_price,
        )

    def test_happy_path_hand_computed(self):
        result = football_field_route.football_field(self._payload())
        self.assertEqual(
            [row.method for row in result.rows],
            ["DCF", "Multiples", "Scenarios"],
        )
        self.assertEqual(result.overall_low, 90.0)
        self.assertEqual(result.overall_high, 210.0)
        self.assertEqual(result.median_of_mids, 150.0)
        self.assertEqual(result.mean_of_mids, 150.0)
        self.assertEqual(result.overlap_low, 120.0)
        self.assertEqual(result.overlap_high, 180.0)
        self.assertTrue(result.has_overlap)
        self.assertEqual(result.market_price, 150.0)
        self.assertTrue(result.market_price_in_overlap)
        self.assertEqual(
            [row.market_position for row in result.rows],
            ["inside", "inside", "inside"],
        )
        self.assertEqual(result.rows[0].upside_of_mid, 0.0)
        self.assertAlmostEqual(
            result.rows[1].upside_of_mid, 140.0 / 150.0 - 1
        )
        self.assertAlmostEqual(
            result.rows[2].upside_of_mid_percent, (160.0 / 150.0 - 1) * 100
        )

    def test_without_market_price_optional_fields_are_null(self):
        result = football_field_route.football_field(
            self._payload(market_price=None)
        )
        self.assertIsNone(result.market_price)
        self.assertIsNone(result.market_price_in_overlap)
        self.assertIsNone(result.rows[0].upside_of_mid)
        self.assertIsNone(result.rows[0].upside_of_mid_percent)
        self.assertIsNone(result.rows[0].market_position)

    def test_domain_validation_error_is_400(self):
        # ترتیب نامعتبر کرانه‌ها از Pydantic عبور می‌کند و دامنه رد می‌کند
        payload = s.FootballFieldRequest(
            ranges=[
                s.ValuationRangeInput(
                    method="A", low=20.0, mid=10.0, high=30.0
                )
            ]
        )
        with self.assertRaises(ValidationError):
            football_field_route.football_field(payload)

    def test_schema_violation_is_422(self):
        with self.assertRaises(PydanticValidationError):
            s.FootballFieldRequest(ranges=[])
        with self.assertRaises(PydanticValidationError):
            s.FootballFieldRequest(
                ranges=[
                    s.ValuationRangeInput(
                        method=f"روش{index}",
                        low=float(index),
                        mid=float(index + 1),
                        high=float(index + 2),
                    )
                    for index in range(13)
                ]
            )


if __name__ == "__main__":
    unittest.main()
