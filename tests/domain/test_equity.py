"""تست‌های واحد مدل‌های ارزش‌گذاری سهام عادی (بدون وابستگی به لایه نمایش).

اجرا از ریشه پروژه:
    python3 -m unittest discover -s tests -t . -v
"""

import unittest
from dataclasses import FrozenInstanceError, replace
from unittest.mock import patch

from stock_valuation.domain import equity, validators
from stock_valuation.domain.equity import (
    SupernormalResult,
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
from stock_valuation.domain.errors import CalculationError, ValidationError


class TestSinglePeriod(unittest.TestCase):
    """مدل تک‌دوره‌ای"""

    def test_price(self):
        self.assertAlmostEqual(single_period_model(1.0, 50.0, 0.1), 51 / 1.1, places=10)

    def test_decomposition_sums_to_price(self):
        decomposition = single_period_decomposition(1.0, 50.0, 0.1)
        self.assertAlmostEqual(
            decomposition.pv_dividend + decomposition.pv_terminal_price,
            decomposition.p0,
            places=10,
        )

    def test_dividend_is_discounted(self):
        decomposition = single_period_decomposition(1.0, 50.0, 0.1)
        self.assertAlmostEqual(decomposition.pv_dividend, 1.0 / 1.1, places=10)

    def test_invalid_input(self):
        with self.assertRaises(ValidationError):
            single_period_model(0.0, 50.0, 0.1)


class TestZeroGrowth(unittest.TestCase):
    """مدل رشد صفر و بازده سالانه"""

    def test_price(self):
        self.assertAlmostEqual(zero_growth_model(2.0, 0.08), 25.0, places=10)

    def test_annual_yield(self):
        self.assertAlmostEqual(annual_dividend_yield_percent(2.25, 25.0), 9.0, places=10)

    def test_invalid_input(self):
        with self.assertRaises(ValidationError):
            zero_growth_model(2.0, 0.0)


class TestConstantGrowth(unittest.TestCase):
    """مدل رشد ثابت گوردون و حداقل اختلاف نرخ بازده و رشد"""

    def test_price(self):
        self.assertAlmostEqual(constant_growth_model(1.5, 0.05, 0.12), 22.5, places=10)

    def test_breakdown(self):
        breakdown = gordon_breakdown(1.5, 0.05, 0.12)
        self.assertAlmostEqual(breakdown.d1, 1.575, places=10)
        self.assertAlmostEqual(breakdown.dividend_yield, 0.07, places=10)
        self.assertAlmostEqual(breakdown.dividend_yield_percent, 7.0, places=10)
        self.assertAlmostEqual(breakdown.capital_gains_yield_percent, 5.0, places=10)

    def test_growth_equal_to_return_is_rejected(self):
        with self.assertRaises(ValidationError):
            constant_growth_model(1.5, 0.12, 0.12)

    def test_growth_above_return_is_rejected(self):
        with self.assertRaises(ValidationError):
            constant_growth_model(1.5, 0.20, 0.12)

    def test_spread_below_minimum_is_rejected(self):
        with self.assertRaises(ValidationError):
            constant_growth_model(1.5, 0.117, 0.12)

    def test_minimum_spread_constant(self):
        self.assertEqual(validators.MIN_SPREAD, 0.005)

    def test_project_dividends(self):
        projected = project_dividends(1.0, 0.05, periods=3)
        self.assertEqual(len(projected), 3)
        self.assertAlmostEqual(projected[0], 1.05, places=10)
        self.assertAlmostEqual(projected[2], 1.0 * 1.05 ** 3, places=10)

    def test_project_dividends_invalid_periods(self):
        with self.assertRaises(ValidationError):
            project_dividends(1.0, 0.05, periods=0)


class TestSupernormalGrowth(unittest.TestCase):
    """مدل رشد غیرعادی"""

    GROWTH_RATES = [0.25, 0.20, 0.15]

    def _result(self):
        return supernormal_growth_model(1.0, self.GROWTH_RATES, 3, 0.05, 0.12)

    def test_price_matches_manual_discounting(self):
        expected = (
            1.25 / 1.12
            + 1.50 / 1.12 ** 2
            + 1.725 / 1.12 ** 3
            + (1.725 * 1.05 / 0.07) / 1.12 ** 3
        )
        self.assertAlmostEqual(self._result().p0, expected, places=9)

    def test_present_values_sum_to_price(self):
        result = self._result()
        self.assertAlmostEqual(
            result.pv_dividends_total + result.pv_p_terminal, result.p0, places=10
        )

    def test_terminal_dividend_is_d_n_plus_1(self):
        result = self._result()
        self.assertAlmostEqual(result.d_terminal, result.dividends[-1] * 1.05, places=10)

    def test_result_is_named_tuple(self):
        self.assertIsInstance(self._result(), SupernormalResult)
        self.assertIsInstance(self._result(), tuple)

    def test_empty_growth_rates_raise_validation_error(self):
        with self.assertRaises(ValidationError):
            supernormal_growth_model(1.0, [], 0, 0.05, 0.12)

    def test_length_mismatch_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            supernormal_growth_model(1.0, [0.1, 0.1], 3, 0.05, 0.12)

    def test_terminal_growth_spread_is_checked(self):
        with self.assertRaises(ValidationError):
            supernormal_growth_model(1.0, [0.1], 1, 0.12, 0.12)

    def test_schedule_rows(self):
        result = self._result()
        rows = supernormal_schedule(self.GROWTH_RATES, result, 0.05)

        self.assertEqual(len(rows), 4)
        self.assertTrue(rows[-1].is_terminal)
        self.assertAlmostEqual(rows[-1].dividend, result.d_terminal, places=10)
        self.assertAlmostEqual(rows[-1].present_value, result.pv_p_terminal, places=10)
        self.assertAlmostEqual(rows[0].dividend, result.dividends[0], places=10)
        self.assertAlmostEqual(rows[0].growth_rate_percent, 25.0, places=10)
        self.assertEqual(rows[2].period, 3)

    def test_schedule_length_mismatch(self):
        result = self._result()
        with self.assertRaises(ValidationError):
            supernormal_schedule([0.1], result, 0.05)


class TestExpectedReturn(unittest.TestCase):
    """بازده مورد انتظار"""

    def test_return(self):
        self.assertAlmostEqual(expected_return(1.0, 20.0, 0.10), 0.15, places=10)

    def test_breakdown(self):
        breakdown = expected_return_breakdown(1.0, 20.0, 0.10)
        self.assertAlmostEqual(breakdown.dividend_yield, 0.05, places=10)
        self.assertAlmostEqual(breakdown.dividend_yield_percent, 5.0, places=10)
        self.assertAlmostEqual(breakdown.capital_gains_yield_percent, 10.0, places=10)
        self.assertAlmostEqual(breakdown.total_percent, 15.0, places=10)

    def test_invalid_price(self):
        with self.assertRaises(ValidationError):
            expected_return(1.0, 0.0, 0.10)


class TestCapm(unittest.TestCase):
    """مدل CAPM"""

    def test_required_return(self):
        self.assertAlmostEqual(capm_required_return(0.04, 1.5, 0.10), 0.13, places=10)

    def test_beta_one_returns_market_return(self):
        self.assertAlmostEqual(capm_required_return(0.04, 1.0, 0.10), 0.10, places=10)

    def test_breakdown(self):
        breakdown = capm_breakdown(0.04, 1.5, 0.10)
        self.assertAlmostEqual(breakdown.market_risk_premium, 0.06, places=10)
        self.assertAlmostEqual(breakdown.risk_premium, 0.09, places=10)
        self.assertAlmostEqual(breakdown.required_return, 0.13, places=10)

    def test_breakdown_percent_properties(self):
        breakdown = capm_breakdown(0.04, 1.5, 0.10)
        self.assertAlmostEqual(breakdown.required_return_percent, 13.0, places=10)
        self.assertAlmostEqual(breakdown.risk_free_rate_percent, 4.0, places=10)
        self.assertAlmostEqual(breakdown.market_risk_premium_percent, 6.0, places=10)
        self.assertAlmostEqual(breakdown.risk_premium_percent, 9.0, places=10)

    def test_market_return_equal_to_risk_free_rejected(self):
        with self.assertRaises(ValidationError):
            capm_required_return(0.10, 1.0, 0.10)

    def test_market_return_below_risk_free_rejected(self):
        with self.assertRaises(ValidationError):
            capm_required_return(0.10, 1.0, 0.08)

    def test_non_positive_beta_rejected(self):
        with self.assertRaises(ValidationError):
            capm_required_return(0.04, 0.0, 0.10)

    def test_non_positive_risk_free_rate_rejected(self):
        with self.assertRaises(ValidationError):
            capm_required_return(0.0, 1.0, 0.10)

    def test_non_positive_market_return_rejected(self):
        with self.assertRaises(ValidationError):
            capm_required_return(0.04, 1.0, 0.0)

    def test_overflow_raises_calculation_error(self):
        with self.assertRaises(CalculationError):
            capm_required_return(0.01, 1e308, 1e308)

    def test_non_finite_input_raises_calculation_error(self):
        with self.assertRaises(CalculationError):
            capm_required_return(float("nan"), 1.0, 0.10)


class TestPreferredStock(unittest.TestCase):
    """سهام ممتاز و مقایسه با اوراق قرضه"""

    def test_price_matches_zero_growth(self):
        self.assertAlmostEqual(preferred_stock_valuation(2.25, 0.09), 25.0, places=10)

    def test_positive_risk_premium(self):
        self.assertAlmostEqual(risk_premium_percent(0.09, 8.0), 1.0, places=10)

    def test_negative_risk_premium(self):
        self.assertAlmostEqual(risk_premium_percent(0.05, 8.0), -3.0, places=10)

    def test_invalid_bond_rate(self):
        with self.assertRaises(ValidationError):
            risk_premium_percent(0.09, 0.0)


class TestGrowthOpportunities(unittest.TestCase):
    """فرصت‌های رشد"""

    def test_valuation(self):
        total_value, no_growth_value = growth_opportunities_valuation(3.0, 0.10, 5.0)
        self.assertAlmostEqual(total_value, 35.0, places=10)
        self.assertAlmostEqual(no_growth_value, 30.0, places=10)

    def test_breakdown_share(self):
        breakdown = growth_opportunities_breakdown(3.0, 0.10, 5.0)
        self.assertAlmostEqual(breakdown.growth_share_percent, 5.0 / 35.0 * 100, places=10)

    def test_zero_total_value_share(self):
        breakdown = growth_opportunities_breakdown(3.0, 0.10, -30.0)
        self.assertEqual(breakdown.growth_share_percent, 0)


class TestSustainableGrowth(unittest.TestCase):
    """رشد پایدار، هویت‌های NPVGO و منحنی نگهداری سود"""

    def _result(self, **overrides):
        params = dict(eps=5.0, r=0.12, roe=0.15, retention_ratio=0.4)
        params.update(overrides)
        return sustainable_growth_valuation(**params)

    def test_reference_values(self):
        result = self._result()
        for name, expected in (
            ("sustainable_growth", 0.06), ("payout_ratio", 0.6), ("next_dividend", 3.0),
            ("price", 50.0), ("no_growth_value", 41.66666666666667),
            ("npvgo", 8.333333333333329), ("justified_pe", 10.0),
            ("growth_share_percent", 16.666666666666657),
        ):
            with self.subTest(field=name):
                self.assertAlmostEqual(getattr(result, name), expected, places=10)
        self.assertTrue(result.growth_creates_value)
        self.assertEqual((result.eps, result.required_return, result.roe, result.retention_ratio),
                         (5.0, 0.12, 0.15, 0.4))

    def test_roe_equal_to_return_has_zero_npvgo(self):
        result = self._result(roe=0.12)
        self.assertAlmostEqual(result.npvgo, 0.0, places=10)
        self.assertFalse(result.growth_creates_value)

    def test_roe_below_return_destroys_value(self):
        result = self._result(roe=0.08)
        self.assertLess(result.npvgo, 0.0)
        self.assertFalse(result.growth_creates_value)

    def test_zero_retention_has_no_growth(self):
        result = self._result(retention_ratio=0.0)
        self.assertEqual(result.sustainable_growth, 0.0)
        self.assertEqual(result.price, 5.0 / 0.12)
        self.assertEqual(result.npvgo, 0.0)

    def test_cross_check_manual_npvgo_model(self):
        for roe in (0.08, 0.12, 0.15):
            with self.subTest(roe=roe):
                result = self._result(roe=roe)
                self.assertAlmostEqual(result.price,
                    growth_opportunities_valuation(result.eps, result.required_return, result.npvgo)[0],
                    places=10)

    def test_curve_values_and_invalid_points(self):
        result = self._result()
        self.assertEqual(len(result.retention_curve), 10)
        self.assertEqual([point.retention_ratio for point in result.retention_curve],
                         [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9])
        for point in result.retention_curve:
            with self.subTest(b=point.retention_ratio):
                if point.retention_ratio >= 0.8:
                    self.assertIsNone(point.price)
                    self.assertIsNone(point.npvgo)
                else:
                    direct = self._result(retention_ratio=point.retention_ratio)
                    self.assertEqual(point.price, direct.price)
                    self.assertEqual(point.npvgo, direct.npvgo)
                    self.assertEqual(point.sustainable_growth, direct.sustainable_growth)
        self.assertEqual(result.retention_curve[4].price, result.price)
        self.assertEqual(result.retention_curve[4].npvgo, result.npvgo)

    def test_curve_respects_minimum_spread_not_only_growth_limit(self):
        result = self._result(r=0.124, retention_ratio=0.4)
        self.assertLess(result.retention_curve[8].sustainable_growth, result.required_return)
        self.assertIsNone(result.retention_curve[8].price)
        self.assertIsNotNone(result.retention_curve[7].price)

    def test_non_positive_fundamentals_rejected(self):
        for name in ("eps", "r", "roe"):
            for value in (0.0, -0.1):
                with self.subTest(field=name, value=value), self.assertRaises(ValidationError):
                    self._result(**{name: value})

    def test_invalid_retention_rejected(self):
        for b in (-0.1, 1.0, 1.1):
            with self.subTest(b=b), self.assertRaises(ValidationError):
                self._result(retention_ratio=b)

    def test_non_finite_inputs_rejected(self):
        for name in ("eps", "r", "roe", "retention_ratio"):
            for value in (float("nan"), float("inf"), -float("inf")):
                with self.subTest(field=name, value=value), self.assertRaises(ValidationError):
                    self._result(**{name: value})

    def test_roe_cap_reused(self):
        with self.assertRaises(ValidationError):
            self._result(roe=2.01, retention_ratio=0.0)
        self.assertEqual(self._result(roe=2.0, retention_ratio=0.0).roe, 2.0)

    def test_growth_and_spread_violations_rejected(self):
        for roe, b in ((0.3, 0.5), (0.15, 0.8), (0.15, 0.78)):
            with self.subTest(roe=roe, b=b), self.assertRaises(ValidationError):
                self._result(roe=roe, retention_ratio=b)
        with self.assertRaises(ValidationError):
            self._result(r=validators.MIN_SPREAD / 2, retention_ratio=0.0)

    def test_existing_strict_spread_boundary_preserved(self):
        with self.assertRaises(ValidationError):
            self._result(r=0.09, roe=0.17, retention_ratio=0.5)
        self.assertGreater(self._result(r=0.106, roe=0.2, retention_ratio=0.5).price, 0)

    def test_percent_properties(self):
        result = self._result()
        for name, expected in (("required_return_percent", 12.0), ("roe_percent", 15.0),
                               ("retention_ratio_percent", 40.0), ("payout_ratio_percent", 60.0),
                               ("sustainable_growth_percent", 6.0)):
            with self.subTest(field=name):
                self.assertAlmostEqual(getattr(result, name), expected, places=10)
        self.assertEqual(result.retention_curve[4].retention_ratio_percent, 40.0)
        self.assertEqual(result.retention_curve[4].sustainable_growth_percent, 6.0)

    def test_non_finite_calculation_rejected(self):
        with self.assertRaises(CalculationError):
            self._result(eps=1e308)
        with self.assertRaises(CalculationError):
            self._result(r=1e308, retention_ratio=0.0)

    def test_breakdown_consistency_guard(self):
        real = growth_opportunities_breakdown(5.0, 0.12, 50.0 - 5.0 / 0.12)
        with patch.object(equity, "growth_opportunities_breakdown",
                          return_value=replace(real, total_value=51.0)):
            with self.assertRaises(CalculationError):
                self._result()

    def test_frozen_results_and_determinism(self):
        first = self._result()
        self.assertEqual(first, self._result())
        with self.assertRaises(FrozenInstanceError):
            first.price = 0.0
        with self.assertRaises(FrozenInstanceError):
            first.retention_curve[0].price = 0.0


class TestPegRatio(unittest.TestCase):
    """نسبت PEG و تفسیر آن"""

    def test_ratio(self):
        self.assertAlmostEqual(peg_ratio(15.0, 10.0), 1.5, places=10)

    def test_growth_above_100_rejected(self):
        with self.assertRaises(ValidationError):
            peg_ratio(15.0, 101.0)

    def test_zero_growth_rejected(self):
        with self.assertRaises(ValidationError):
            peg_ratio(15.0, 0.0)

    def test_interpretation_thresholds(self):
        cases = {
            0.4: ("very_undervalued", "success"),
            0.9: ("undervalued", "info"),
            1.0: ("fair", "info"),
            1.4: ("near_fair", "warning"),
            1.5: ("overvalued", "error"),
            2.5: ("overvalued", "error"),
        }
        for peg, (category, level) in cases.items():
            with self.subTest(peg=peg):
                interpretation = interpret_peg(peg)
                self.assertEqual(interpretation.category, category)
                self.assertEqual(interpretation.level, level)
                self.assertTrue(interpretation.message)

    def test_non_positive_peg_rejected(self):
        with self.assertRaises(ValidationError):
            interpret_peg(0)


class TestDeterminism(unittest.TestCase):
    """خروجی توابع باید قطعی و تکرارپذیر باشد"""

    def test_repeated_calls_are_identical(self):
        first = supernormal_growth_model(1.0, [0.25, 0.20, 0.15], 3, 0.05, 0.12)
        second = supernormal_growth_model(1.0, [0.25, 0.20, 0.15], 3, 0.05, 0.12)
        self.assertEqual(first, second)

    def test_inputs_are_not_mutated(self):
        growth_rates = [0.25, 0.20, 0.15]
        supernormal_growth_model(1.0, growth_rates, 3, 0.05, 0.12)
        self.assertEqual(growth_rates, [0.25, 0.20, 0.15])


if __name__ == "__main__":
    unittest.main()
