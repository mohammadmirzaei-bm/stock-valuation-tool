"""تست‌های واحد FCFF و ارزش‌گذاری جریان نقدی تنزیل‌شده.

اجرا از ریشه پروژه:
    python3 -m unittest discover -s tests -t . -v
"""

import unittest

from stock_valuation.domain import validators
from stock_valuation.domain.dcf import (
    CashFlowProjection,
    calculate_fcff,
    dcf_valuation,
)
from stock_valuation.domain.errors import ValidationError


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


if __name__ == "__main__":
    unittest.main()
