"""تست‌های واحد خلاصه زمین فوتبال.

اجرا از ریشه پروژه:
    python3 -m unittest discover -s tests -t . -v
"""

import unittest
from dataclasses import FrozenInstanceError

from stock_valuation.domain.dcf_analysis import (
    DcfScenario,
    dcf_scenario_valuation,
    dcf_sensitivity,
)
from stock_valuation.domain.errors import CalculationError, ValidationError
from stock_valuation.domain.football_field import (
    FootballFieldResult,
    ValuationRange,
    football_field_summary,
    range_from_implied,
    range_from_scenarios,
    range_from_sensitivity,
)
from stock_valuation.domain.multiples import (
    MultipleKind,
    PeerMultiple,
    implied_valuation,
)
from tests.domain._fixtures import _reference_dcf_projections


def _ranges(*specs):
    """ساخت بازه‌ها از چند‌تایی‌های (نام، کمینه، میانی، بیشینه)"""
    return [ValuationRange(*spec) for spec in specs]


class TestFootballFieldSummary(unittest.TestCase):
    """خلاصه بازه‌ها، همپوشانی، موقعیت قیمت بازار و اعتبارسنجی ورودی"""

    @staticmethod
    def _three_ranges():
        """سه بازه با همپوشانی [120, 180] و میانه/میانگین 150"""
        return _ranges(
            ("DCF", 100.0, 150.0, 200.0),
            ("Multiples", 120.0, 140.0, 180.0),
            ("Scenarios", 90.0, 160.0, 210.0),
        )

    def test_hand_computed_summary_without_market_price(self):
        result = football_field_summary(self._three_ranges())
        self.assertEqual(
            [row.method for row in result.rows],
            ["DCF", "Multiples", "Scenarios"],
        )
        self.assertEqual([row.mid for row in result.rows], [150.0, 140.0, 160.0])
        self.assertEqual(result.overall_low, 90.0)
        self.assertEqual(result.overall_high, 210.0)
        self.assertEqual(result.median_of_mids, 150.0)
        self.assertEqual(result.mean_of_mids, 150.0)
        self.assertEqual(result.overlap_low, 120.0)
        self.assertEqual(result.overlap_high, 180.0)
        self.assertTrue(result.has_overlap)
        self.assertIsNone(result.market_price)
        self.assertIsNone(result.market_price_in_overlap)
        for row in result.rows:
            self.assertIsNone(row.upside_of_mid)
            self.assertIsNone(row.market_position)
            self.assertIsNone(row.upside_of_mid_percent)

    def test_median_of_mids_even_count(self):
        result = football_field_summary(
            _ranges(
                ("A", 100.0, 150.0, 200.0),
                ("B", 120.0, 140.0, 180.0),
            )
        )
        self.assertEqual(result.median_of_mids, 145.0)
        self.assertEqual(result.mean_of_mids, 145.0)

    def test_no_overlap(self):
        result = football_field_summary(
            _ranges(
                ("A", 100.0, 150.0, 200.0),
                ("B", 210.0, 220.0, 230.0),
            )
        )
        self.assertEqual(result.overlap_low, 210.0)
        self.assertEqual(result.overlap_high, 200.0)
        self.assertFalse(result.has_overlap)
        self.assertEqual(result.overall_low, 100.0)
        self.assertEqual(result.overall_high, 230.0)
        self.assertEqual(result.median_of_mids, 185.0)
        self.assertEqual(result.mean_of_mids, 185.0)

    def test_market_position_below_inside_above(self):
        ranges = _ranges(("A", 100.0, 150.0, 200.0))
        for market_price, expected in (
            (80.0, "below"),
            (150.0, "inside"),
            (250.0, "above"),
        ):
            with self.subTest(market_price=market_price):
                result = football_field_summary(ranges, market_price=market_price)
                row = result.rows[0]
                self.assertEqual(row.market_position, expected)
                self.assertAlmostEqual(
                    row.upside_of_mid, 150.0 / market_price - 1
                )
                self.assertEqual(result.market_price, market_price)

    def test_market_at_range_edges_is_inside(self):
        ranges = _ranges(("A", 100.0, 150.0, 200.0))
        for market_price in (100.0, 200.0):
            with self.subTest(market_price=market_price):
                result = football_field_summary(ranges, market_price=market_price)
                self.assertEqual(result.rows[0].market_position, "inside")
                self.assertTrue(result.market_price_in_overlap)

    def test_upside_of_mid_percent(self):
        result = football_field_summary(
            _ranges(("A", 100.0, 150.0, 200.0)), market_price=100.0
        )
        self.assertAlmostEqual(result.rows[0].upside_of_mid_percent, 50.0)

    def test_market_price_in_overlap(self):
        ranges = self._three_ranges()
        # ناحیه همپوشانی [120, 180]
        inside = football_field_summary(ranges, market_price=150.0)
        self.assertTrue(inside.market_price_in_overlap)
        edge = football_field_summary(ranges, market_price=120.0)
        self.assertTrue(edge.market_price_in_overlap)
        outside = football_field_summary(ranges, market_price=190.0)
        self.assertFalse(outside.market_price_in_overlap)
        # 190 داخل بازه «Scenarios» است ولی خارج ناحیه همپوشانی
        self.assertEqual(outside.rows[2].market_position, "inside")

    def test_market_price_in_overlap_false_without_overlap(self):
        result = football_field_summary(
            _ranges(
                ("A", 100.0, 150.0, 200.0),
                ("B", 210.0, 220.0, 230.0),
            ),
            market_price=220.0,
        )
        self.assertFalse(result.has_overlap)
        self.assertFalse(result.market_price_in_overlap)

    def test_negative_values_allowed(self):
        result = football_field_summary(
            _ranges(("A", -200.0, -150.0, -100.0)), market_price=100.0
        )
        row = result.rows[0]
        self.assertEqual((row.low, row.mid, row.high), (-200.0, -150.0, -100.0))
        self.assertEqual(row.market_position, "above")
        self.assertAlmostEqual(row.upside_of_mid, -2.5)
        self.assertEqual(result.overall_low, -200.0)
        self.assertEqual(result.overall_high, -100.0)

    def test_single_range_has_overlap(self):
        result = football_field_summary(_ranges(("A", 100.0, 120.0, 140.0)))
        self.assertTrue(result.has_overlap)
        self.assertEqual(result.overlap_low, 100.0)
        self.assertEqual(result.overlap_high, 140.0)

    def test_equal_bounds_allowed(self):
        result = football_field_summary(_ranges(("A", 100.0, 100.0, 100.0)))
        self.assertEqual(result.rows[0].low, 100.0)
        self.assertEqual(result.overlap_low, 100.0)
        self.assertEqual(result.overlap_high, 100.0)

    def test_twelve_ranges_allowed(self):
        ranges = _ranges(
            *[
                (f"روش{index}", float(index), float(index + 1), float(index + 2))
                for index in range(12)
            ]
        )
        result = football_field_summary(ranges)
        self.assertEqual(len(result.rows), 12)

    def test_more_than_twelve_ranges_rejected(self):
        ranges = _ranges(
            *[
                (f"روش{index}", float(index), float(index + 1), float(index + 2))
                for index in range(13)
            ]
        )
        with self.assertRaises(ValidationError):
            football_field_summary(ranges)

    def test_empty_ranges_rejected(self):
        with self.assertRaises(ValidationError):
            football_field_summary([])

    def test_non_range_items_rejected(self):
        for ranges in (None, "abc", [("A", 1.0, 2.0, 3.0)]):
            with self.subTest(ranges=ranges):
                with self.assertRaises(ValidationError):
                    football_field_summary(ranges)

    def test_blank_method_rejected(self):
        for method in ("", "   ", None):
            with self.subTest(method=method):
                with self.assertRaises(ValidationError):
                    football_field_summary(_ranges((method, 1.0, 2.0, 3.0)))

    def test_duplicate_method_rejected(self):
        for names in (("A", "A"), ("A", " A ")):
            with self.subTest(names=names):
                with self.assertRaises(ValidationError):
                    football_field_summary(
                        _ranges(
                            (names[0], 1.0, 2.0, 3.0),
                            (names[1], 2.0, 3.0, 4.0),
                        )
                    )

    def test_method_is_stripped_in_rows(self):
        result = football_field_summary(_ranges(("  DCF  ", 1.0, 2.0, 3.0)))
        self.assertEqual(result.rows[0].method, "DCF")

    def test_non_finite_bounds_rejected(self):
        for bad in (float("nan"), float("inf"), -float("inf")):
            for spec in (
                ("A", bad, 2.0, 3.0),
                ("A", 1.0, bad, 3.0),
                ("A", 1.0, 2.0, bad),
            ):
                with self.subTest(bad=bad, spec=spec):
                    with self.assertRaises(ValidationError):
                        football_field_summary(_ranges(spec))

    def test_non_numeric_bounds_rejected(self):
        for bad in ("1", None, True):
            with self.subTest(value=bad):
                with self.assertRaises(ValidationError):
                    football_field_summary(_ranges(("A", bad, 2.0, 3.0)))

    def test_invalid_order_rejected(self):
        for spec in (
            ("A", 20.0, 10.0, 30.0),
            ("A", 10.0, 30.0, 20.0),
        ):
            with self.subTest(spec=spec):
                with self.assertRaises(ValidationError):
                    football_field_summary(_ranges(spec))

    def test_invalid_market_price_rejected(self):
        ranges = _ranges(("A", 100.0, 150.0, 200.0))
        for market_price in (0.0, -1.0, float("nan"), float("inf")):
            with self.subTest(market_price=market_price):
                with self.assertRaises(ValidationError):
                    football_field_summary(ranges, market_price=market_price)

    def test_overflowing_statistics_is_calculation_error(self):
        # میانگین و میانه دو مقدار 1e308 به inf سرریز می‌کنند
        ranges = _ranges(
            ("A", 1e308, 1e308, 1e308),
            ("B", 1e308, 1e308, 1e308),
        )
        with self.assertRaises(CalculationError):
            football_field_summary(ranges)

    def test_deterministic_frozen_and_inputs_unchanged(self):
        ranges = self._three_ranges()
        snapshot = [(item.method, item.low, item.mid, item.high) for item in ranges]
        first = football_field_summary(ranges, market_price=150.0)
        second = football_field_summary(ranges, market_price=150.0)
        self.assertEqual(first, second)
        self.assertIsInstance(first, FootballFieldResult)
        self.assertEqual(
            [(item.method, item.low, item.mid, item.high) for item in ranges],
            snapshot,
        )
        with self.assertRaises(FrozenInstanceError):
            first.overall_low = 0.0  # type: ignore[misc]


class TestBuilders(unittest.TestCase):
    """ساخت بازه از خروجی‌های واقعی حساسیت، سناریو و ضرایب همتایان"""

    @staticmethod
    def _sensitivity_result():
        # WACC پایه ۰٫۰۴ و رشد ۰٫۰۳ تا بخشی از سلول‌ها نامعتبر (None) شوند
        return dcf_sensitivity(
            _reference_dcf_projections(), 0.04, 0.03, 10.0, 0.25
        )

    @staticmethod
    def _scenario_result():
        scenarios = [
            DcfScenario("bear", 0.25, _reference_dcf_projections(), 0.10, 0.01),
            DcfScenario("base", 0.50, _reference_dcf_projections(), 0.10, 0.02),
            DcfScenario("bull", 0.25, _reference_dcf_projections(), 0.10, 0.03),
        ]
        return dcf_scenario_valuation(
            scenarios,
            10.0,
            0.25,
            cash=50.0,
            debt=200.0,
            minority_interest=30.0,
            preferred_equity=20.0,
        )

    @staticmethod
    def _implied_result():
        peers = [
            PeerMultiple("الف", 10.0),
            PeerMultiple("ب", 20.0),
            PeerMultiple("ج", 30.0),
            PeerMultiple("د", 40.0),
        ]
        return implied_valuation(
            MultipleKind.EV_EBITDA,
            500.0,
            10.0,
            peers,
            cash=100.0,
            debt=300.0,
            minority_interest=50.0,
            preferred_equity=50.0,
        )

    def test_range_from_sensitivity_ignores_none_cells(self):
        result = self._sensitivity_result()
        cells = [value for row in result.value_per_share for value in row]
        self.assertIn(None, cells)
        values = [value for value in cells if value is not None]
        rng = range_from_sensitivity("DCF", result)
        self.assertIsInstance(rng, ValuationRange)
        self.assertEqual(rng.method, "DCF")
        self.assertEqual(rng.low, min(values))
        self.assertEqual(rng.mid, result.base_value_per_share)
        self.assertEqual(rng.high, max(values))

    def test_range_from_scenarios(self):
        result = self._scenario_result()
        rng = range_from_scenarios("Scenarios", result)
        self.assertEqual(rng.method, "Scenarios")
        self.assertEqual(rng.low, result.min_value_per_share)
        self.assertEqual(rng.mid, result.expected_value_per_share)
        self.assertEqual(rng.high, result.max_value_per_share)
        self.assertLessEqual(rng.low, rng.mid)
        self.assertLessEqual(rng.mid, rng.high)

    def test_range_from_implied(self):
        result = self._implied_result()
        rng = range_from_implied("Multiples", result)
        self.assertEqual(rng.method, "Multiples")
        self.assertEqual(rng.low, 845.0)
        self.assertEqual(rng.mid, 1220.0)
        self.assertEqual(rng.high, 1595.0)

    def test_built_ranges_feed_summary(self):
        ranges = [
            range_from_sensitivity("DCF", self._sensitivity_result()),
            range_from_scenarios("Scenarios", self._scenario_result()),
            range_from_implied("Multiples", self._implied_result()),
        ]
        summary = football_field_summary(ranges, market_price=1000.0)
        self.assertEqual(
            [row.method for row in summary.rows],
            ["DCF", "Scenarios", "Multiples"],
        )
        self.assertEqual(summary.overall_low, min(item.low for item in ranges))
        self.assertEqual(summary.overall_high, max(item.high for item in ranges))
        self.assertEqual(
            summary.mean_of_mids,
            sum(item.mid for item in ranges) / len(ranges),
        )
        # قیمت ۱۰۰۰ زیر بازه DCF، داخل بازه سناریوها و داخل بازه ضرایب است
        self.assertEqual(
            [row.market_position for row in summary.rows],
            ["below", "inside", "inside"],
        )


if __name__ == "__main__":
    unittest.main()
