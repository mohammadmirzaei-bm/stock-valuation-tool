"""تست‌های واحد لایه محاسباتی (بدون وابستگی به Streamlit).

اجرا از ریشه پروژه:
    python3 -m unittest discover -s tests -t . -v

یا در صورت نصب pytest:
    python3 -m pytest tests -v
"""

import ast
import inspect
import unittest

from stock_valuation.domain import errors, self_tests, validators, valuation_models
from stock_valuation.domain.errors import CalculationError, ValidationError
from stock_valuation.domain.valuation_models import (
    CashFlowProjection,
    SupernormalResult,
    annual_dividend_yield_percent,
    calculate_fcff,
    capm_breakdown,
    capm_required_return,
    constant_growth_model,
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
    risk_premium_percent,
    single_period_decomposition,
    single_period_model,
    supernormal_growth_model,
    supernormal_schedule,
    wacc,
    wacc_breakdown,
    zero_growth_model,
)


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


class TestSelfTests(unittest.TestCase):
    """تست‌های دودی داخل برنامه"""

    def test_all_self_tests_pass(self):
        results = self_tests.run_self_tests()
        self.assertEqual(len(results), 4)
        for result in results:
            self.assertTrue(result.startswith("✅"), result)


if __name__ == "__main__":
    unittest.main()

