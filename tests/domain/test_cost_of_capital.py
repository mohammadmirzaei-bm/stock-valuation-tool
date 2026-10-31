"""تست‌های واحد میانگین موزون هزینه سرمایه (WACC).

اجرا از ریشه پروژه:
    python3 -m unittest discover -s tests -t . -v
"""

import unittest

from stock_valuation.domain.cost_of_capital import wacc, wacc_breakdown
from stock_valuation.domain.equity import capm_required_return
from stock_valuation.domain.errors import ValidationError


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


if __name__ == "__main__":
    unittest.main()
