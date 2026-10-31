"""تست‌های واحد پیش‌بینی مبتنی بر محرک‌ها.

اجرا از ریشه پروژه:
    python3 -m unittest discover -s tests -t . -v
"""

import unittest

from stock_valuation.domain.dcf import CashFlowProjection, dcf_valuation
from stock_valuation.domain.errors import ValidationError
from stock_valuation.domain.forecast import (
    ForecastDrivers,
    ForecastResult,
    build_projections,
)


def _flat_drivers(**overrides):
    """محرک‌های تخت با مقادیر دقیق ممیزی دودویی برای انتظارات دقیق"""
    values = {
        "revenue_growth": 0.25,
        "ebitda_margin": 0.5,
        "da_pct_revenue": 0.125,
        "capex_pct_revenue": 0.25,
        "nwc_pct_incremental_revenue": 0.5,
    }
    values.update(overrides)
    return ForecastDrivers(**values)


class TestBuildProjections(unittest.TestCase):
    """ساخت پیش‌بینی سالانه از محرک‌ها"""

    def test_hand_computed_three_years(self):
        # base=800؛ مقادیر دقیق دودویی تا انتظارات assertEqual معتبر باشند
        # y1: rev=1000 ebitda=500 dep=125 ebit=375 capex=250 dNWC=100
        # y2: rev=1250 ebitda=625 dep=156.25 ebit=468.75 capex=312.5 dNWC=125
        # y3: rev=1562.5 ebitda=781.25 dep=195.3125 ebit=585.9375
        #     capex=390.625 dNWC=156.25
        result = build_projections(800.0, _flat_drivers(), 3)
        self.assertEqual(result.revenues, [1000.0, 1250.0, 1562.5])
        self.assertEqual(result.ebitda, [500.0, 625.0, 781.25])
        expected_rows = [
            (1, 1000.0, 375.0, 125.0, 250.0, 100.0),
            (2, 1250.0, 468.75, 156.25, 312.5, 125.0),
            (3, 1562.5, 585.9375, 195.3125, 390.625, 156.25),
        ]
        for row, expected in zip(result.rows, expected_rows):
            year, revenue, ebit, depreciation, capex, delta_nwc = expected
            self.assertEqual(row.year, year)
            self.assertEqual(row.revenue, revenue)
            self.assertEqual(row.growth, 0.25)
            self.assertEqual(row.ebitda, revenue * 0.5)
            self.assertEqual(row.ebitda_margin, 0.5)
            self.assertEqual(row.ebit, ebit)
            self.assertEqual(row.depreciation, depreciation)
            self.assertEqual(row.capex, capex)
            self.assertEqual(row.delta_nwc, delta_nwc)

    def test_flat_drivers_match_manual_projection_list(self):
        result = build_projections(800.0, _flat_drivers(), 3)
        manual = [
            CashFlowProjection(ebit=375.0, depreciation=125.0, capex=250.0, delta_nwc=100.0),
            CashFlowProjection(ebit=468.75, depreciation=156.25, capex=312.5, delta_nwc=125.0),
            CashFlowProjection(ebit=585.9375, depreciation=195.3125, capex=390.625, delta_nwc=156.25),
        ]
        self.assertEqual(result.projections, manual)

    def test_feeding_dcf_equals_manual_list_valuation(self):
        result = build_projections(800.0, _flat_drivers(), 3)
        manual = [
            CashFlowProjection(ebit=375.0, depreciation=125.0, capex=250.0, delta_nwc=100.0),
            CashFlowProjection(ebit=468.75, depreciation=156.25, capex=312.5, delta_nwc=125.0),
            CashFlowProjection(ebit=585.9375, depreciation=195.3125, capex=390.625, delta_nwc=156.25),
        ]
        from_forecast = dcf_valuation(result.projections, 0.10, 0.02, 5.0, 0.25)
        from_manual = dcf_valuation(manual, 0.10, 0.02, 5.0, 0.25)
        # مقایسه بیت‌به‌بیت
        self.assertEqual(from_forecast.enterprise_value, from_manual.enterprise_value)
        self.assertEqual(from_forecast.equity_value, from_manual.equity_value)
        self.assertEqual(from_forecast.value_per_share, from_manual.value_per_share)
        self.assertEqual(
            [row.fcff for row in from_forecast.years],
            [row.fcff for row in from_manual.years],
        )

    def test_negative_growth_gives_negative_delta_nwc(self):
        # رشد منفی: delta_nwc منفی می‌شود (آزادسازی NWC) و قدرمطلق نمی‌گیرد
        result = build_projections(800.0, _flat_drivers(revenue_growth=-0.25), 2)
        self.assertEqual(result.revenues, [600.0, 450.0])
        self.assertEqual(result.rows[0].delta_nwc, -100.0)
        self.assertEqual(result.rows[1].delta_nwc, -75.0)

    def test_per_year_sequences(self):
        drivers = ForecastDrivers(
            revenue_growth=[0.25, 0.5, 0.0],
            ebitda_margin=[0.5, 0.4, 0.6],
            da_pct_revenue=0.125,
            capex_pct_revenue=0.25,
            nwc_pct_incremental_revenue=0.5,
        )
        result = build_projections(800.0, drivers, 3)
        self.assertEqual(result.revenues, [1000.0, 1500.0, 1500.0])
        self.assertEqual([row.growth for row in result.rows], [0.25, 0.5, 0.0])
        self.assertEqual([row.ebitda_margin for row in result.rows], [0.5, 0.4, 0.6])
        self.assertEqual(result.ebitda, [500.0, 600.0, 900.0])
        self.assertEqual(result.rows[1].delta_nwc, 250.0)
        self.assertEqual(result.rows[2].delta_nwc, 0.0)

    def test_normalization_off_by_default(self):
        result = build_projections(800.0, _flat_drivers(), 3, terminal_growth=0.02)
        last = result.rows[-1]
        self.assertEqual(last.capex, 390.625)
        self.assertEqual(last.delta_nwc, 156.25)

    def test_normalization_terminal_year(self):
        # فقط سال آخر نرمال می‌شود: capex=dep و ΔNWC=nwc×rev×g/(1+g)
        result = build_projections(
            800.0, _flat_drivers(), 3,
            terminal_growth=0.02, normalize_terminal_year=True,
        )
        self.assertEqual(result.rows[0].capex, 250.0)
        self.assertEqual(result.rows[1].capex, 312.5)
        last = result.rows[-1]
        self.assertEqual(last.capex, last.depreciation)
        self.assertAlmostEqual(
            last.delta_nwc, 0.5 * 1562.5 * 0.02 / 1.02, places=10
        )
        self.assertEqual(
            result.projections[-1],
            CashFlowProjection(
                ebit=585.9375,
                depreciation=195.3125,
                capex=195.3125,
                delta_nwc=last.delta_nwc,
            ),
        )

    def test_normalization_requires_terminal_growth(self):
        with self.assertRaises(ValidationError):
            build_projections(800.0, _flat_drivers(), 3, normalize_terminal_year=True)


class TestBuildProjectionsValidation(unittest.TestCase):
    """شاخه‌های اعتبارسنجی"""

    def test_years_out_of_range_rejected(self):
        for years in (0, 51):
            with self.subTest(years=years):
                with self.assertRaises(ValidationError):
                    build_projections(800.0, _flat_drivers(), years)

    def test_years_non_integer_rejected(self):
        for years in (3.5, "3", True, None):
            with self.subTest(years=years):
                with self.assertRaises(ValidationError):
                    build_projections(800.0, _flat_drivers(), years)

    def test_year_boundaries_accepted(self):
        for years in (1, 50):
            with self.subTest(years=years):
                result = build_projections(800.0, _flat_drivers(), years)
                self.assertEqual(len(result.rows), years)

    def test_base_revenue_invalid_rejected(self):
        for base in (0.0, -100.0, float("nan"), float("inf")):
            with self.subTest(base_revenue=base):
                with self.assertRaises(ValidationError):
                    build_projections(base, _flat_drivers(), 3)

    def test_growth_bounds(self):
        for growth in (-1.0, -1.5, 2.5, float("nan"), float("inf")):
            with self.subTest(growth=growth):
                with self.assertRaises(ValidationError):
                    build_projections(800.0, _flat_drivers(revenue_growth=growth), 3)
        for growth in (-0.9999, 2.0):
            with self.subTest(growth=growth):
                build_projections(800.0, _flat_drivers(revenue_growth=growth), 3)

    def test_percent_driver_bounds(self):
        # هر چهار محرک درصدی باید بین ۰ و ۱ باشند
        percent_fields = (
            "ebitda_margin", "da_pct_revenue",
            "capex_pct_revenue", "nwc_pct_incremental_revenue",
        )
        for field in percent_fields:
            for bad in (-0.1, 1.1, float("nan")):
                with self.subTest(field=field, value=bad):
                    with self.assertRaises(ValidationError):
                        build_projections(800.0, _flat_drivers(**{field: bad}), 3)
        for field in percent_fields:
            for edge in (0.0, 1.0):
                with self.subTest(field=field, value=edge):
                    build_projections(800.0, _flat_drivers(**{field: edge}), 3)

    def test_bool_and_str_drivers_rejected(self):
        for bad in (True, False, "0.25", {"a": 1}, {0.25, 0.5}):
            with self.subTest(driver=bad):
                with self.assertRaises(ValidationError):
                    build_projections(800.0, _flat_drivers(revenue_growth=bad), 3)

    def test_sequence_length_must_equal_years(self):
        with self.assertRaises(ValidationError):
            build_projections(
                800.0, _flat_drivers(revenue_growth=[0.25, 0.25]), 3
            )

    def test_sequence_with_non_number_item_rejected(self):
        for bad_list in ([0.25, True, 0.25], ["a", "b", "c"], [0.25, None, 0.25]):
            with self.subTest(values=bad_list):
                with self.assertRaises(ValidationError):
                    build_projections(
                        800.0, _flat_drivers(revenue_growth=bad_list), 3
                    )

    def test_tuple_sequence_accepted(self):
        result = build_projections(
            800.0, _flat_drivers(revenue_growth=(0.25, 0.25, 0.25)), 3
        )
        self.assertEqual(result.revenues, [1000.0, 1250.0, 1562.5])

    def test_terminal_growth_invalid_rejected(self):
        for bad in (-1.0, 2.5, float("nan")):
            with self.subTest(terminal_growth=bad):
                with self.assertRaises(ValidationError):
                    build_projections(
                        800.0, _flat_drivers(), 3,
                        terminal_growth=bad, normalize_terminal_year=True,
                    )

    def test_non_drivers_object_rejected(self):
        with self.assertRaises(ValidationError):
            build_projections(800.0, {"revenue_growth": 0.25}, 3)


class TestForecastImmutability(unittest.TestCase):
    """عدم تغییر ورودی‌ها و قطعیت خروجی"""

    def test_inputs_not_mutated_and_calls_identical(self):
        growth = [0.25, 0.5, 0.0]
        drivers = ForecastDrivers(
            revenue_growth=growth,
            ebitda_margin=0.5,
            da_pct_revenue=0.125,
            capex_pct_revenue=0.25,
            nwc_pct_incremental_revenue=0.5,
        )
        snapshot = list(growth)
        first = build_projections(800.0, drivers, 3)
        second = build_projections(800.0, drivers, 3)
        self.assertEqual(growth, snapshot)
        self.assertEqual(first, second)

    def test_results_are_frozen(self):
        result = build_projections(800.0, _flat_drivers(), 3)
        self.assertIsInstance(result, ForecastResult)
        with self.assertRaises(Exception):
            result.revenues = []  # type: ignore[misc]
        with self.assertRaises(Exception):
            result.rows[0].revenue = 0.0  # type: ignore[misc]

    def test_percent_properties(self):
        result = build_projections(800.0, _flat_drivers(), 3)
        self.assertEqual(result.rows[0].growth_percent, 25.0)
        self.assertEqual(result.rows[0].ebitda_margin_percent, 50.0)


if __name__ == "__main__":
    unittest.main()
