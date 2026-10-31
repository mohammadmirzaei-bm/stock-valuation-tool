"""تست‌های واحد لایه محاسباتی (بدون وابستگی به Streamlit).

اجرا از ریشه پروژه:
    python3 -m unittest discover -s tests -t . -v

یا در صورت نصب pytest:
    python3 -m pytest tests -v
"""

import ast
import inspect
import math
import unittest
from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
from unittest.mock import patch

from stock_valuation.domain import errors, self_tests, validators, valuation_models
from stock_valuation.domain import equity
from stock_valuation.domain.errors import CalculationError, ValidationError
from stock_valuation.domain.valuation_models import (
    CashFlowProjection,
    DcfScenario,
    REVERSE_DCF_MIN_GROWTH,
    SupernormalResult,
    annual_dividend_yield_percent,
    calculate_fcff,
    capm_breakdown,
    capm_required_return,
    constant_growth_model,
    dcf_scenario_valuation,
    dcf_sensitivity,
    dcf_valuation,
    expected_return,
    expected_return_breakdown,
    gordon_breakdown,
    growth_opportunities_breakdown,
    growth_opportunities_valuation,
    interpret_peg,
    peg_ratio,
    preferred_stock_valuation,
    project_dividends,
    reverse_dcf_implied_growth,
    risk_premium_percent,
    single_period_decomposition,
    single_period_model,
    supernormal_growth_model,
    supernormal_schedule,
    sustainable_growth_valuation,
    wacc,
    wacc_breakdown,
    zero_growth_model,
)


def _reference_dcf_projections():
    """پیش‌بینی پنج‌ساله مرجع برای آزمون‌های DCF، حساسیت و DCF معکوس"""
    return [
        CashFlowProjection(ebit=1000.0, depreciation=200.0, capex=250.0, delta_nwc=50.0),
        CashFlowProjection(ebit=1100.0, depreciation=210.0, capex=260.0, delta_nwc=55.0),
        CashFlowProjection(ebit=1200.0, depreciation=220.0, capex=270.0, delta_nwc=60.0),
        CashFlowProjection(ebit=1300.0, depreciation=230.0, capex=280.0, delta_nwc=65.0),
        CashFlowProjection(ebit=1400.0, depreciation=240.0, capex=290.0, delta_nwc=70.0),
    ]


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


class TestLayering(unittest.TestCase):
    """لایه محاسباتی نباید به لایه نمایش وابسته باشد"""

    LOGIC_MODULES = (errors, validators, valuation_models, self_tests)

    @staticmethod
    def _imports(module) -> set:
        """نام ماژول‌های واردشده در یک ماژول"""
        tree = ast.parse(inspect.getsource(module))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        return imported

    def test_no_streamlit_import(self):
        for module in self.LOGIC_MODULES:
            with self.subTest(module=module.__name__):
                self.assertNotIn("streamlit", self._imports(module))

    def test_no_streamlit_usage(self):
        for module in self.LOGIC_MODULES:
            with self.subTest(module=module.__name__):
                tree = ast.parse(inspect.getsource(module))
                for node in ast.walk(tree):
                    if (isinstance(node, ast.Attribute)
                            and isinstance(node.value, ast.Name)
                            and node.value.id == "st"):
                        self.fail(f"ارجاع به st در {module.__name__} یافت شد")

    def test_no_session_state_reference(self):
        for module in self.LOGIC_MODULES:
            with self.subTest(module=module.__name__):
                self.assertNotIn("session_state", inspect.getsource(module))

    def test_exception_hierarchy_is_shared(self):
        self.assertIs(valuation_models.ValidationError, errors.ValidationError)
        self.assertIs(valuation_models.CalculationError, errors.CalculationError)
        self.assertTrue(issubclass(CalculationError, Exception))


class TestFcff(unittest.TestCase):
    """جریان نقدی آزاد بنگاه"""

    def test_reference_r1(self):
        self.assertAlmostEqual(
            calculate_fcff(100.0, 0.25, 10.0, 15.0, 5.0), 65.0, places=10
        )

    def test_negative_delta_nwc_increases_fcff(self):
        # کاهش NWC ورود نقد است
        self.assertAlmostEqual(
            calculate_fcff(100.0, 0.25, 10.0, 15.0, -5.0), 75.0, places=10
        )

    def test_tax_rate_one_rejected(self):
        with self.assertRaises(ValidationError):
            calculate_fcff(100.0, 1.0, 10.0, 15.0, 5.0)

    def test_negative_tax_rate_rejected(self):
        with self.assertRaises(ValidationError):
            calculate_fcff(100.0, -0.1, 10.0, 15.0, 5.0)

    def test_non_finite_input_rejected(self):
        with self.assertRaises(ValidationError):
            calculate_fcff(float("nan"), 0.25, 10.0, 15.0, 5.0)


class TestWacc(unittest.TestCase):
    """میانگین موزون هزینه سرمایه"""

    def test_reference_r2(self):
        self.assertAlmostEqual(wacc(600.0, 400.0, 0.12, 0.06, 0.25), 0.09, places=10)

    def test_breakdown_weights_and_after_tax_debt(self):
        breakdown = wacc_breakdown(600.0, 400.0, 0.12, 0.06, 0.25)
        self.assertAlmostEqual(breakdown.equity_weight, 0.6, places=10)
        self.assertAlmostEqual(breakdown.debt_weight, 0.4, places=10)
        self.assertAlmostEqual(breakdown.after_tax_cost_of_debt, 0.045, places=10)
        self.assertAlmostEqual(breakdown.wacc_percent, 9.0, places=10)

    def test_zero_debt_equals_cost_of_equity(self):
        self.assertAlmostEqual(wacc(1000.0, 0.0, 0.12, 0.0, 0.25), 0.12, places=10)

    def test_capm_cost_of_equity_smoke(self):
        cost_of_equity = capm_required_return(0.04, 1.5, 0.10)
        self.assertAlmostEqual(cost_of_equity, 0.13, places=10)
        self.assertAlmostEqual(
            wacc(700.0, 300.0, cost_of_equity, 0.05, 0.20),
            0.7 * 0.13 + 0.3 * 0.05 * 0.8,
            places=10,
        )

    def test_equity_non_positive_rejected(self):
        with self.assertRaises(ValidationError):
            wacc(0.0, 400.0, 0.12, 0.06, 0.25)

    def test_negative_debt_rejected(self):
        with self.assertRaises(ValidationError):
            wacc(600.0, -1.0, 0.12, 0.06, 0.25)

    def test_non_positive_cost_of_equity_rejected(self):
        with self.assertRaises(ValidationError):
            wacc(600.0, 400.0, 0.0, 0.06, 0.25)

    def test_negative_cost_of_debt_rejected(self):
        with self.assertRaises(ValidationError):
            wacc(600.0, 400.0, 0.12, -0.01, 0.25)

    def test_tax_rate_one_rejected(self):
        with self.assertRaises(ValidationError):
            wacc(600.0, 400.0, 0.12, 0.06, 1.0)

    def test_non_finite_input_rejected(self):
        with self.assertRaises(ValidationError):
            wacc(600.0, 400.0, float("inf"), 0.06, 0.25)


class TestDcf(unittest.TestCase):
    """ارزش‌گذاری DCF بر پایه FCFF"""

    @staticmethod
    def _ebit_only(values):
        return [
            CashFlowProjection(ebit=ebit, depreciation=0.0, capex=0.0, delta_nwc=0.0)
            for ebit in values
        ]

    def test_reference_r3_flat_fcff(self):
        result = dcf_valuation(
            self._ebit_only([100.0, 100.0, 100.0]),
            0.10,
            0.0,
            1.0,
            0.0,
        )
        self.assertAlmostEqual(result.pv_fcff_total, 248.6851990984222, places=10)
        self.assertAlmostEqual(result.pv_terminal_value, 751.3148009015775, places=10)
        self.assertAlmostEqual(result.enterprise_value, 1000.0, places=9)
        self.assertAlmostEqual(
            result.pv_fcff_total + result.pv_terminal_value,
            result.enterprise_value,
            places=10,
        )

    def test_reference_r4_asymmetric(self):
        result = dcf_valuation(
            self._ebit_only([80.0, 90.0, 100.0]),
            0.09,
            0.03,
            10.0,
            0.0,
            cash=50.0,
            debt=200.0,
        )
        self.assertAlmostEqual(result.pv_fcff_total, 226.36404281294085, places=10)
        self.assertAlmostEqual(result.terminal_value, 1716.6666666666667, places=10)
        self.assertAlmostEqual(result.pv_terminal_value, 1325.5816407714935, places=10)
        self.assertAlmostEqual(result.enterprise_value, 1551.9456835844344, places=10)
        self.assertAlmostEqual(result.equity_value, 1401.9456835844344, places=10)
        self.assertAlmostEqual(result.value_per_share, 140.19456835844343, places=10)
        self.assertAlmostEqual(
            result.terminal_value_share_percent, 85.41417749298277, places=10
        )

    def test_hand_computed_components(self):
        # Year1: 100*(1-0.25)+10-15-5 = 65
        # Year2: 120*(1-0.25)+12-20-8 = 74
        # Year3: 140*(1-0.25)+14-25-10 = 84
        # WACC=0.10, g=0.02
        # PV = 65/1.1 + 74/1.1^2 + 84/1.1^3
        # TV = 84*1.02/(0.10-0.02) = 1071
        # PV(TV) = 1071/1.1^3
        projections = [
            CashFlowProjection(100.0, 10.0, 15.0, 5.0),
            CashFlowProjection(120.0, 12.0, 20.0, 8.0),
            CashFlowProjection(140.0, 14.0, 25.0, 10.0),
        ]
        result = dcf_valuation(projections, 0.10, 0.02, 5.0, 0.25)
        expected_pvs = (
            65.0 / 1.1
            + 74.0 / 1.1 ** 2
            + 84.0 / 1.1 ** 3
        )
        expected_tv = 84.0 * 1.02 / 0.08
        expected_pv_tv = expected_tv / 1.1 ** 3
        self.assertAlmostEqual(result.years[0].fcff, 65.0, places=10)
        self.assertAlmostEqual(result.years[1].fcff, 74.0, places=10)
        self.assertAlmostEqual(result.years[2].fcff, 84.0, places=10)
        self.assertAlmostEqual(result.pv_fcff_total, expected_pvs, places=10)
        self.assertAlmostEqual(result.terminal_value, expected_tv, places=10)
        self.assertAlmostEqual(result.pv_terminal_value, expected_pv_tv, places=10)
        self.assertAlmostEqual(
            result.enterprise_value, expected_pvs + expected_pv_tv, places=10
        )

    def test_invariants_sum_and_per_share(self):
        result = dcf_valuation(
            self._ebit_only([80.0, 90.0, 100.0]),
            0.09,
            0.03,
            10.0,
            0.0,
            cash=50.0,
            debt=200.0,
        )
        self.assertAlmostEqual(
            result.enterprise_value,
            result.pv_fcff_total + result.pv_terminal_value,
            places=10,
        )
        self.assertAlmostEqual(
            result.value_per_share,
            result.equity_value / result.shares_outstanding,
            places=10,
        )
        self.assertAlmostEqual(
            sum(row.present_value for row in result.years),
            result.pv_fcff_total,
            places=10,
        )

    def test_negative_equity_value_allowed(self):
        result = dcf_valuation(
            self._ebit_only([10.0]),
            0.10,
            0.0,
            1.0,
            0.0,
            cash=0.0,
            debt=500.0,
        )
        self.assertLess(result.equity_value, 0)
        self.assertLess(result.value_per_share, 0)

    def test_growth_equal_to_wacc_rejected(self):
        with self.assertRaises(ValidationError) as ctx:
            dcf_valuation(self._ebit_only([100.0]), 0.09, 0.09, 1.0, 0.0)
        self.assertIn("WACC", str(ctx.exception))
        self.assertIn("نرخ رشد پایانی", str(ctx.exception))

    def test_spread_below_minimum_rejected(self):
        with self.assertRaises(ValidationError):
            dcf_valuation(self._ebit_only([100.0]), 0.09, 0.086, 1.0, 0.0)

    def test_minimum_spread_boundary_accepted(self):
        # 0.105 − 0.10 در ممیز شناور کمی کمتر از 0.005 است؛
        # تلورانس 1e-12 در validate_terminal_growth_vs_wacc آن را می‌پذیرد.
        result = dcf_valuation(self._ebit_only([100.0]), 0.105, 0.10, 1.0, 0.0)
        self.assertTrue(result.enterprise_value > 0)

    def test_float_ambiguous_exact_min_spread_accepted_with_tolerance(self):
        # بدون تلورانس، 0.09 − 0.085 ≈ 0.004999... < MIN_SPREAD رد می‌شد.
        # اعتبارسنج گوردون همچنان آن را رد می‌کند؛ فقط پوشش WACC تلورانس دارد.
        with self.assertRaises(ValidationError):
            validators.validate_growth_rate_vs_return(0.085, 0.09)
        result = dcf_valuation(self._ebit_only([100.0]), 0.09, 0.085, 1.0, 0.0)
        self.assertTrue(result.enterprise_value > 0)

    def test_terminal_fcff_non_positive_rejected(self):
        with self.assertRaises(ValidationError) as ctx:
            dcf_valuation(
                [CashFlowProjection(ebit=0.0, depreciation=0.0, capex=0.0, delta_nwc=0.0)],
                0.10,
                0.0,
                1.0,
                0.0,
            )
        self.assertIn("جریان نقدی آزاد پایانی", str(ctx.exception))

    def test_empty_projections_rejected(self):
        with self.assertRaises(ValidationError):
            dcf_valuation([], 0.10, 0.0, 1.0, 0.0)

    def test_too_many_projections_rejected(self):
        rows = self._ebit_only([100.0] * 51)
        with self.assertRaises(ValidationError):
            dcf_valuation(rows, 0.10, 0.0, 1.0, 0.0)

    def test_shares_non_positive_rejected(self):
        with self.assertRaises(ValidationError):
            dcf_valuation(self._ebit_only([100.0]), 0.10, 0.0, 0.0, 0.0)

    def test_negative_cash_rejected(self):
        with self.assertRaises(ValidationError):
            dcf_valuation(self._ebit_only([100.0]), 0.10, 0.0, 1.0, 0.0, cash=-1.0)

    def test_negative_debt_rejected(self):
        with self.assertRaises(ValidationError):
            dcf_valuation(self._ebit_only([100.0]), 0.10, 0.0, 1.0, 0.0, debt=-1.0)

    def test_negative_minority_interest_rejected(self):
        with self.assertRaises(ValidationError):
            dcf_valuation(
                self._ebit_only([100.0]), 0.10, 0.0, 1.0, 0.0, minority_interest=-1.0
            )

    def test_negative_preferred_equity_rejected(self):
        with self.assertRaises(ValidationError):
            dcf_valuation(
                self._ebit_only([100.0]), 0.10, 0.0, 1.0, 0.0, preferred_equity=-1.0
            )

    def test_tax_rate_one_rejected(self):
        with self.assertRaises(ValidationError):
            dcf_valuation(self._ebit_only([100.0]), 0.10, 0.0, 1.0, 1.0)

    def test_negative_tax_rate_rejected(self):
        with self.assertRaises(ValidationError):
            dcf_valuation(self._ebit_only([100.0]), 0.10, 0.0, 1.0, -0.01)

    def test_non_positive_wacc_rejected(self):
        with self.assertRaises(ValidationError):
            dcf_valuation(self._ebit_only([100.0]), 0.0, -0.01, 1.0, 0.0)

    def test_non_finite_wacc_rejected(self):
        with self.assertRaises(ValidationError):
            dcf_valuation(self._ebit_only([100.0]), float("nan"), 0.0, 1.0, 0.0)

    def test_year_index_is_list_position(self):
        result = dcf_valuation(self._ebit_only([50.0, 60.0]), 0.10, 0.0, 1.0, 0.0)
        self.assertEqual([row.year for row in result.years], [1, 2])


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


class TestSelfTests(unittest.TestCase):
    """تست‌های دودی داخل برنامه"""

    def test_all_self_tests_pass(self):
        results = self_tests.run_self_tests()
        self.assertEqual(len(results), 8)
        for result in results:
            self.assertTrue(result.startswith("✅"), result)


if __name__ == "__main__":
    unittest.main()

