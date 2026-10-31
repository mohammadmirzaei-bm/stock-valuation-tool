"""تست‌های واحد سناریوهای DCF، ماتریس حساسیت و DCF معکوس.

اجرا از ریشه پروژه:
    python3 -m unittest discover -s tests -t . -v
"""

import math
import unittest
from copy import deepcopy
from dataclasses import FrozenInstanceError, replace

from stock_valuation.domain import validators
from stock_valuation.domain.dcf import CashFlowProjection, dcf_valuation
from stock_valuation.domain.dcf_analysis import (
    REVERSE_DCF_MIN_GROWTH,
    DcfScenario,
    dcf_scenario_valuation,
    dcf_sensitivity,
    reverse_dcf_implied_growth,
)
from stock_valuation.domain.errors import CalculationError, ValidationError
from tests.domain._fixtures import _reference_dcf_projections


class TestDcfScenarios(unittest.TestCase):
    """ارزش و ریسک وزنی سناریوهای DCF و قرارداد خطای آن‌ها"""

    @staticmethod
    def _scenarios():
        return [
            DcfScenario(name, probability, [CashFlowProjection(ebit, 0.0, 0.0, 0.0)], 0.1, 0.0)
            for name, probability, ebit in (("bear", 0.25, 100.0), ("base", 0.5, 200.0),
                                            ("bull", 0.25, 300.0))
        ]

    def _result(self, scenarios=None, **overrides):
        params = dict(shares_outstanding=10.0, tax_rate=0.0)
        params.update(overrides)
        return dcf_scenario_valuation(self._scenarios() if scenarios is None else scenarios, **params)

    def test_rows_match_direct_dcf_with_shared_balance_sheet(self):
        scenarios = [replace(row, projections=_reference_dcf_projections(),
                             wacc_rate=rate, terminal_growth=growth)
                     for row, rate, growth in zip(self._scenarios(), (0.11, 0.09, 0.085),
                                                  (0.02, 0.03, 0.035))]
        shared = dict(shares_outstanding=100.0, tax_rate=0.25, cash=500.0, debt=1500.0,
                      minority_interest=50.0, preferred_equity=25.0)
        result = self._result(scenarios, **shared)
        self.assertEqual([row.name for row in result.scenarios], [row.name for row in scenarios])
        for row, scenario in zip(result.scenarios, scenarios):
            direct = dcf_valuation(scenario.projections, scenario.wacc_rate,
                                   scenario.terminal_growth, **shared)
            for name in ("enterprise_value", "equity_value", "value_per_share", "wacc",
                         "terminal_growth", "terminal_value_share_percent"):
                with self.subTest(scenario=row.name, field=name):
                    self.assertEqual(getattr(row, name), getattr(direct, name))

    def test_hand_computed_weighted_statistics(self):
        result = self._result()
        # ارزش‌ها ۱۰۰، ۲۰۰ و ۳۰۰؛ میانگین ۲۰۰ و واریانس ۵۰۰۰ است.
        self.assertAlmostEqual(result.expected_value_per_share, 200.0, places=10)
        self.assertAlmostEqual(result.expected_enterprise_value, 2000.0, places=10)
        self.assertAlmostEqual(result.expected_equity_value, 2000.0, places=10)
        self.assertAlmostEqual(result.std_dev_value_per_share, math.sqrt(5000.0), places=10)
        self.assertEqual(sum(row.weighted_value_per_share for row in result.scenarios),
                         result.expected_value_per_share)
        self.assertEqual(result.expected_enterprise_value,
                         sum(row.probability * row.enterprise_value for row in result.scenarios))
        self.assertEqual(result.expected_equity_value,
                         sum(row.probability * row.equity_value for row in result.scenarios))

    def test_best_worst_and_identical_ties(self):
        result = self._result()
        self.assertEqual((result.worst_scenario, result.best_scenario), ("bear", "bull"))
        self.assertAlmostEqual(result.min_value_per_share, 100.0, places=10)
        self.assertAlmostEqual(result.max_value_per_share, 300.0, places=10)
        scenarios = [replace(row, projections=self._scenarios()[0].projections)
                     for row in self._scenarios()]
        identical = self._result(scenarios)
        self.assertEqual(identical.std_dev_value_per_share, 0.0)
        self.assertEqual(identical.expected_value_per_share, identical.scenarios[0].value_per_share)
        self.assertEqual((identical.worst_scenario, identical.best_scenario), ("bear", "bear"))

    def test_market_upside_and_probability(self):
        result = self._result(market_price=150.0)
        for row in result.scenarios:
            self.assertEqual(row.upside, row.value_per_share / 150.0 - 1)
            self.assertEqual(row.upside_percent, row.upside * 100)
        self.assertAlmostEqual(result.expected_upside, 1.0 / 3.0, places=10)
        self.assertEqual(result.probability_of_upside, 0.75)
        self.assertAlmostEqual(result.expected_upside_percent, 100.0 / 3.0, places=10)
        self.assertEqual(result.probability_of_upside_percent, 75.0)

    def test_upside_probability_is_strictly_above_market(self):
        common_price = self._result().scenarios[1].value_per_share
        self.assertEqual(self._result(market_price=common_price).probability_of_upside, 0.25)

    def test_optional_upside_fields_are_none(self):
        result = self._result()
        for value in (result.market_price, result.expected_upside, result.expected_upside_percent,
                      result.probability_of_upside, result.probability_of_upside_percent):
            self.assertIsNone(value)
        for row in result.scenarios:
            self.assertIsNone(row.upside)
            self.assertIsNone(row.upside_percent)

    def test_invalid_probability_sums_show_actual_total(self):
        for probability, total in ((0.4, "0.9"), (0.6, "1.1")):
            scenarios = self._scenarios()
            scenarios[1] = replace(scenarios[1], probability=probability)
            with self.subTest(total=total), self.assertRaises(ValidationError) as ctx:
                self._result(scenarios)
            self.assertIn(total, str(ctx.exception))

    def test_invalid_probabilities_rejected(self):
        for probability in (-0.1, 1.1, float("nan"), float("inf"), -float("inf")):
            scenarios = self._scenarios()
            scenarios[0] = replace(scenarios[0], probability=probability)
            with self.subTest(probability=probability), self.assertRaises(ValidationError):
                self._result(scenarios)

    def test_probability_tolerance_without_normalization(self):
        scenarios = self._scenarios()
        scenarios[1] = replace(scenarios[1], probability=0.5000001)
        result = self._result(scenarios)
        self.assertEqual(result.scenarios[1].probability, 0.5000001)
        self.assertAlmostEqual(result.expected_value_per_share, 200.00002, places=10)
        validators.validate_scenario_set(["a", "b"], [0.5, math.nextafter(0.500001, 0.0)])
        with self.assertRaises(ValidationError):
            validators.validate_scenario_set(["a", "b"], [0.5, 0.5000011])

    def test_scenario_count_bounds(self):
        for count in (0, 1, 6):
            scenarios = [replace(self._scenarios()[0], name=str(index), probability=1.0 / count)
                         for index in range(count)]
            with self.subTest(count=count), self.assertRaises(ValidationError):
                self._result(scenarios)
        five = [replace(self._scenarios()[0], name=str(index), probability=0.2)
                for index in range(5)]
        self.assertEqual(len(self._result(five).scenarios), 5)

    def test_blank_duplicate_or_nonstring_names_rejected(self):
        for name in ("", "   ", "bear", " bear ", None):
            scenarios = self._scenarios()
            scenarios[1] = replace(scenarios[1], name=name)
            with self.subTest(name=name), self.assertRaises(ValidationError):
                self._result(scenarios)

    def test_nonlist_or_wrong_scenario_type_rejected(self):
        for scenarios in (tuple(self._scenarios()), "scenarios", [object(), object()]):
            with self.subTest(scenarios=scenarios), self.assertRaises(ValidationError):
                self._result(scenarios)

    def test_validator_requires_equal_lengths(self):
        with self.assertRaises(ValidationError):
            validators.validate_scenario_set(["a", "b"], [1.0])

    def test_failing_scenario_preserves_validation_type_and_name(self):
        for overrides in (dict(terminal_growth=0.1),
                          dict(projections=[CashFlowProjection(0.0, 0.0, 0.0, 0.0)])):
            scenarios = self._scenarios()
            scenarios[1] = replace(scenarios[1], **overrides)
            with self.subTest(overrides=overrides), self.assertRaises(ValidationError) as ctx:
                self._result(scenarios)
            self.assertIs(type(ctx.exception), ValidationError)
            self.assertIn("base", str(ctx.exception))

    def test_failing_scenario_preserves_calculation_type_and_name(self):
        scenarios = self._scenarios()
        scenarios[1] = replace(scenarios[1], projections=[CashFlowProjection(1e308, 0, 0, 0)])
        with self.assertRaises(CalculationError) as ctx:
            self._result(scenarios)
        self.assertIs(type(ctx.exception), CalculationError)
        self.assertIn("base", str(ctx.exception))

    def test_invalid_market_prices_rejected(self):
        for price in (0.0, -1.0, float("nan"), float("inf"), -float("inf")):
            with self.subTest(price=price), self.assertRaises(ValidationError):
                self._result(market_price=price)

    def test_zero_probability_is_still_valued(self):
        scenarios = self._scenarios()
        scenarios[0] = replace(scenarios[0], probability=0.0)
        scenarios[1] = replace(scenarios[1], probability=0.75)
        result = self._result(scenarios)
        self.assertEqual(result.scenarios[0].weighted_value_per_share, 0.0)
        self.assertAlmostEqual(result.scenarios[0].value_per_share, 100.0, places=10)
        self.assertAlmostEqual(result.expected_value_per_share, 225.0, places=10)
        scenarios[0] = replace(scenarios[0], terminal_growth=0.1)
        with self.assertRaises(ValidationError):
            self._result(scenarios)

    def test_negative_equity_is_not_clamped(self):
        result = self._result(debt=4000.0)
        self.assertLess(result.expected_equity_value, 0)
        self.assertAlmostEqual(result.expected_value_per_share, -200.0, places=10)
        self.assertEqual((result.worst_scenario, result.best_scenario), ("bear", "bull"))

    def test_percent_properties(self):
        row = self._result().scenarios[0]
        self.assertEqual(row.probability_percent, 25.0)
        self.assertEqual(row.wacc_percent, 10.0)
        self.assertEqual(row.terminal_growth_percent, 0.0)

    def test_numeric_failure_is_calculation_error(self):
        with self.assertRaises(CalculationError):
            self._result(market_price=1e-308)
        scenarios = [replace(row, projections=[CashFlowProjection(index * 1e200, 0, 0, 0)])
                     for index, row in enumerate(self._scenarios(), start=1)]
        with self.assertRaises(CalculationError):
            self._result(scenarios)

    def test_inputs_not_mutated_and_calls_are_identical(self):
        scenarios = self._scenarios()
        snapshot = deepcopy(scenarios)
        first = self._result(scenarios)
        self.assertEqual(first, self._result(scenarios))
        self.assertEqual(scenarios, snapshot)

    def test_frozen_input_and_results(self):
        scenarios = self._scenarios()
        with self.assertRaises(FrozenInstanceError):
            scenarios[0].probability = 0.0
        result = self._result(scenarios)
        with self.assertRaises(FrozenInstanceError):
            result.expected_value_per_share = 0.0
        with self.assertRaises(FrozenInstanceError):
            result.scenarios[0].value_per_share = 0.0


class TestDcfSensitivity(unittest.TestCase):
    """ماتریس حساسیت DCF نسبت به WACC و رشد پایانی"""

    WACC = 0.09
    GROWTH = 0.03
    TAX = 0.25
    SHARES = 100.0

    def _result(self, **overrides):
        params = {
            "projections": _reference_dcf_projections(),
            "wacc_rate": self.WACC,
            "terminal_growth": self.GROWTH,
            "shares_outstanding": self.SHARES,
            "tax_rate": self.TAX,
            "cash": 500.0,
            "debt": 1500.0,
        }
        params.update(overrides)
        return dcf_sensitivity(**params)

    def test_center_cell_equals_base_case(self):
        result = self._result()
        base = dcf_valuation(
            _reference_dcf_projections(),
            self.WACC,
            self.GROWTH,
            self.SHARES,
            self.TAX,
            cash=500.0,
            debt=1500.0,
        )
        self.assertEqual(result.base_row, 2)
        self.assertEqual(result.base_col, 2)
        self.assertEqual(result.value_per_share[2][2], base.value_per_share)
        self.assertEqual(result.enterprise_value[2][2], base.enterprise_value)
        self.assertEqual(result.base_value_per_share, base.value_per_share)
        self.assertEqual(result.base_enterprise_value, base.enterprise_value)
        self.assertEqual(result.base_wacc, self.WACC)
        self.assertEqual(result.base_terminal_growth, self.GROWTH)

    def test_axes_ascending_centered_without_float_noise(self):
        result = self._result()
        self.assertEqual(result.wacc_values, [0.07, 0.08, 0.09, 0.1, 0.11])
        self.assertEqual(result.growth_values, [0.02, 0.025, 0.03, 0.035, 0.04])
        for actual, expected in zip(
            result.wacc_values_percent, [7.0, 8.0, 9.0, 10.0, 11.0]
        ):
            self.assertAlmostEqual(actual, expected, places=10)
        for actual, expected in zip(
            result.growth_values_percent, [2.0, 2.5, 3.0, 3.5, 4.0]
        ):
            self.assertAlmostEqual(actual, expected, places=10)
        self.assertEqual(result.valid_cells, 25)
        self.assertEqual(result.total_cells, 25)

    def test_value_increases_with_growth_along_row(self):
        result = self._result()
        for row in result.value_per_share:
            valid = [value for value in row if value is not None]
            for lower, higher in zip(valid, valid[1:]):
                self.assertLess(lower, higher)

    def test_value_decreases_with_wacc_down_column(self):
        result = self._result()
        for col_index in range(len(result.growth_values)):
            valid = [
                result.value_per_share[row_index][col_index]
                for row_index in range(len(result.wacc_values))
                if result.value_per_share[row_index][col_index] is not None
            ]
            for value_lower_wacc, value_higher_wacc in zip(valid, valid[1:]):
                self.assertGreater(value_lower_wacc, value_higher_wacc)

    def test_min_spread_violations_become_none(self):
        result = dcf_sensitivity(
            _reference_dcf_projections(),
            0.06,
            0.05,
            self.SHARES,
            self.TAX,
            wacc_step=0.01,
            growth_step=0.005,
        )
        self.assertEqual(result.wacc_values, [0.04, 0.05, 0.06, 0.07, 0.08])
        self.assertEqual(result.growth_values, [0.04, 0.045, 0.05, 0.055, 0.06])
        self.assertLess(result.valid_cells, result.total_cells)
        self.assertIsNone(result.value_per_share[0][0])  # WACC 0.04 = رشد 0.04
        self.assertIsNone(result.value_per_share[0][4])  # رشد 0.06 > WACC 0.04
        self.assertIsNone(result.value_per_share[1][2])  # WACC 0.05 = رشد 0.05
        self.assertIsNone(result.enterprise_value[2][4])  # WACC 0.06 = رشد 0.06
        self.assertIsNotNone(result.value_per_share[1][0])  # اختلاف 0.01 معتبر است
        self.assertIsNotNone(result.value_per_share[2][3])  # حداقل اختلاف مرزی

    def test_non_positive_wacc_cells_become_none(self):
        result = dcf_sensitivity(
            _reference_dcf_projections(),
            0.02,
            0.0,
            self.SHARES,
            self.TAX,
            wacc_step=0.01,
            wacc_points=5,
        )
        self.assertEqual(result.wacc_values, [0.0, 0.01, 0.02, 0.03, 0.04])
        for value in result.value_per_share[0]:
            self.assertIsNone(value)
        self.assertIsNotNone(result.value_per_share[4][2])

    def test_invalid_base_case_rejected(self):
        with self.assertRaises(ValidationError):
            self._result(terminal_growth=self.WACC)

        with self.assertRaises(ValidationError):
            self._result(tax_rate=1.0)

        zero_fcff = [CashFlowProjection(0.0, 0.0, 0.0, 0.0)]
        with self.assertRaises(ValidationError):
            dcf_sensitivity(zero_fcff, self.WACC, self.GROWTH, self.SHARES, self.TAX)

    def test_even_points_rejected(self):
        with self.assertRaises(ValidationError):
            self._result(wacc_points=4)
        with self.assertRaises(ValidationError):
            self._result(growth_points=4)

    def test_out_of_range_points_rejected(self):
        for points in (2, 12):
            with self.subTest(points=points), self.assertRaises(ValidationError):
                self._result(wacc_points=points)

    def test_non_positive_step_rejected(self):
        for step in (0.0, -0.01):
            with self.subTest(step=step), self.assertRaises(ValidationError):
                self._result(wacc_step=step)

    def test_nan_step_rejected(self):
        with self.assertRaises(ValidationError):
            self._result(growth_step=float("nan"))

    def test_inputs_not_mutated_and_calls_are_identical(self):
        projections = _reference_dcf_projections()
        snapshot = list(projections)
        first = self._result(projections=projections)
        second = self._result(projections=projections)
        self.assertEqual(projections, snapshot)
        self.assertEqual(first, second)


class TestReverseDcf(unittest.TestCase):
    """رشد پایانی تلویحی بازار با DCF معکوس"""

    WACC = 0.09
    TAX = 0.25
    SHARES = 100.0
    GROWTH = 0.03
    CASH = 500.0
    DEBT = 1500.0

    def _price_at(self, growth):
        return dcf_valuation(
            _reference_dcf_projections(),
            self.WACC,
            growth,
            self.SHARES,
            self.TAX,
            cash=self.CASH,
            debt=self.DEBT,
        ).value_per_share

    def _solve(self, market_price, **overrides):
        params = {
            "projections": _reference_dcf_projections(),
            "wacc_rate": self.WACC,
            "shares_outstanding": self.SHARES,
            "tax_rate": self.TAX,
            "market_price": market_price,
            "cash": self.CASH,
            "debt": self.DEBT,
        }
        params.update(overrides)
        return reverse_dcf_implied_growth(**params)

    def test_round_trip_recovers_growth(self):
        price = self._price_at(self.GROWTH)
        result = self._solve(price)
        self.assertEqual(result.status, "solved")
        self.assertIsNotNone(result.implied_growth)
        self.assertLess(abs(result.implied_growth - self.GROWTH), 1e-6)
        self.assertAlmostEqual(result.implied_growth_percent, self.GROWTH * 100, places=4)
        self.assertEqual(result.market_price, price)
        self.assertEqual(result.wacc, self.WACC)
        self.assertAlmostEqual(result.wacc_percent, 9.0, places=10)
        self.assertAlmostEqual(result.search_min_growth, REVERSE_DCF_MIN_GROWTH, places=10)
        self.assertAlmostEqual(
            result.search_max_growth, self.WACC - validators.MIN_SPREAD, places=10
        )
        self.assertTrue(result.message)

    def test_value_at_implied_growth_matches_market_price(self):
        price = self._price_at(self.GROWTH)
        result = self._solve(price)
        breakdown = dcf_valuation(
            _reference_dcf_projections(),
            self.WACC,
            result.implied_growth,
            self.SHARES,
            self.TAX,
            cash=self.CASH,
            debt=self.DEBT,
        )
        self.assertLess(abs(breakdown.value_per_share - price), 1e-6 * max(1.0, price))
        self.assertAlmostEqual(result.enterprise_value, breakdown.enterprise_value, places=6)
        self.assertAlmostEqual(result.equity_value, breakdown.equity_value, places=6)
        self.assertAlmostEqual(
            result.terminal_value_share_percent,
            breakdown.terminal_value_share_percent,
            places=6,
        )

    def test_negative_implied_growth_solves(self):
        price = self._price_at(-0.05)
        result = self._solve(price)
        self.assertEqual(result.status, "solved")
        self.assertIsNotNone(result.implied_growth)
        self.assertLess(result.implied_growth, 0)
        self.assertLess(abs(result.implied_growth + 0.05), 1e-6)

    def test_price_below_search_range(self):
        minimum_value = self._price_at(REVERSE_DCF_MIN_GROWTH)
        result = self._solve(minimum_value / 2)
        self.assertEqual(result.status, "market_price_below_range")
        self.assertIsNone(result.implied_growth)
        self.assertIsNone(result.enterprise_value)
        self.assertIsNone(result.equity_value)
        self.assertIsNone(result.terminal_value_share_percent)
        self.assertIn("بازه جستجو", result.message)

    def test_price_above_search_range(self):
        maximum_value = self._price_at(self.WACC - validators.MIN_SPREAD)
        result = self._solve(maximum_value * 2)
        self.assertEqual(result.status, "market_price_above_range")
        self.assertIsNone(result.implied_growth)
        self.assertIsNone(result.enterprise_value)
        self.assertIn("بازه جستجو", result.message)

    def test_growth_gap_with_reference(self):
        price = self._price_at(self.GROWTH)
        result = self._solve(price, reference_terminal_growth=0.02)
        self.assertEqual(result.status, "solved")
        self.assertEqual(result.reference_terminal_growth, 0.02)
        self.assertAlmostEqual(
            result.growth_gap, result.implied_growth - 0.02, places=10
        )
        self.assertAlmostEqual(
            result.growth_gap_percent, result.growth_gap * 100, places=10
        )

    def test_growth_gap_none_without_reference(self):
        result = self._solve(self._price_at(self.GROWTH))
        self.assertIsNone(result.reference_terminal_growth)
        self.assertIsNone(result.growth_gap)
        self.assertIsNone(result.growth_gap_percent)

    def test_non_positive_market_price_rejected(self):
        for price in (0.0, -5.0):
            with self.subTest(price=price), self.assertRaises(ValidationError):
                self._solve(price)

    def test_non_finite_market_price_rejected(self):
        for price in (float("nan"), float("inf")):
            with self.subTest(price=price), self.assertRaises(ValidationError):
                self._solve(price)

    def test_non_positive_terminal_fcff_rejected(self):
        with self.assertRaises(ValidationError):
            reverse_dcf_implied_growth(
                [CashFlowProjection(0.0, 0.0, 0.0, 0.0)],
                self.WACC,
                self.SHARES,
                self.TAX,
                10.0,
            )

    def test_non_finite_reference_growth_rejected(self):
        with self.assertRaises(ValidationError):
            self._solve(
                self._price_at(self.GROWTH), reference_terminal_growth=float("nan")
            )

    def test_percent_properties_none_when_unsolved(self):
        minimum_value = self._price_at(REVERSE_DCF_MIN_GROWTH)
        result = self._solve(minimum_value / 2)
        self.assertIsNone(result.implied_growth_percent)
        self.assertIsNone(result.growth_gap_percent)


if __name__ == "__main__":
    unittest.main()
