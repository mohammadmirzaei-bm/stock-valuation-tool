"""تست‌های واحد پل ارزش بنگاه به حقوق صاحبان سهام.

اجرا از ریشه پروژه:
    python3 -m unittest discover -s tests -t . -v
"""

import unittest

from stock_valuation.domain.bridge import EquityBridge, enterprise_to_equity
from stock_valuation.domain.dcf import CashFlowProjection, dcf_valuation
from stock_valuation.domain.errors import CalculationError, ValidationError


class TestEnterpriseToEquity(unittest.TestCase):
    """تبدیل EV به ارزش حقوق صاحبان سهام و ارزش هر سهم"""

    def test_hand_computed_reference(self):
        # EV=1000, cash=50, debt=200, minority=30, preferred=20
        # Equity = 1000 + 50 − 200 − 30 − 20 = 800؛ هر سهم = 800 / 10 = 80
        bridge = enterprise_to_equity(1000.0, 50.0, 200.0, 30.0, 20.0, 10.0)
        self.assertAlmostEqual(bridge.equity_value, 800.0, places=10)
        self.assertAlmostEqual(bridge.value_per_share, 80.0, places=10)

    def test_zero_balance_sheet_fields(self):
        bridge = enterprise_to_equity(1000.0, 0.0, 0.0, 0.0, 0.0, 4.0)
        self.assertAlmostEqual(bridge.equity_value, 1000.0, places=10)
        self.assertAlmostEqual(bridge.value_per_share, 250.0, places=10)

    def test_negative_equity_not_clamped(self):
        # بدهی بیشتر از EV؛ مقدار منفی خطا نیست و کلمپ نمی‌شود
        bridge = enterprise_to_equity(100.0, 0.0, 500.0, 0.0, 0.0, 2.0)
        self.assertAlmostEqual(bridge.equity_value, -400.0, places=10)
        self.assertAlmostEqual(bridge.value_per_share, -200.0, places=10)

    def test_non_finite_enterprise_value_rejected(self):
        # EV خروجی محاسبه است؛ نامتناهی بودن آن CalculationError می‌دهد
        # تا قرارداد dcf_valuation (سرریز به inf) دست نخورد.
        for bad_ev in (float("nan"), float("inf"), -float("inf")):
            with self.subTest(enterprise_value=bad_ev):
                with self.assertRaises(CalculationError):
                    enterprise_to_equity(bad_ev, 0.0, 0.0, 0.0, 0.0, 1.0)

    def test_non_finite_cash_rejected(self):
        with self.assertRaises(ValidationError):
            enterprise_to_equity(100.0, float("inf"), 0.0, 0.0, 0.0, 1.0)

    def test_non_finite_debt_rejected(self):
        with self.assertRaises(ValidationError):
            enterprise_to_equity(100.0, 0.0, float("nan"), 0.0, 0.0, 1.0)

    def test_non_finite_minority_interest_rejected(self):
        with self.assertRaises(ValidationError):
            enterprise_to_equity(100.0, 0.0, 0.0, float("inf"), 0.0, 1.0)

    def test_non_finite_preferred_equity_rejected(self):
        with self.assertRaises(ValidationError):
            enterprise_to_equity(100.0, 0.0, 0.0, 0.0, float("nan"), 1.0)

    def test_non_finite_shares_rejected(self):
        with self.assertRaises(ValidationError):
            enterprise_to_equity(100.0, 0.0, 0.0, 0.0, 0.0, float("inf"))

    def test_non_positive_shares_rejected(self):
        for shares in (0.0, -5.0):
            with self.subTest(shares=shares):
                with self.assertRaises(ValidationError):
                    enterprise_to_equity(100.0, 0.0, 0.0, 0.0, 0.0, shares)

    def test_negative_cash_rejected(self):
        with self.assertRaises(ValidationError):
            enterprise_to_equity(100.0, -1.0, 0.0, 0.0, 0.0, 1.0)

    def test_negative_debt_rejected(self):
        with self.assertRaises(ValidationError):
            enterprise_to_equity(100.0, 0.0, -1.0, 0.0, 0.0, 1.0)

    def test_negative_minority_interest_rejected(self):
        with self.assertRaises(ValidationError):
            enterprise_to_equity(100.0, 0.0, 0.0, -1.0, 0.0, 1.0)

    def test_negative_preferred_equity_rejected(self):
        with self.assertRaises(ValidationError):
            enterprise_to_equity(100.0, 0.0, 0.0, 0.0, -1.0, 1.0)

    def test_result_is_frozen_and_deterministic(self):
        first = enterprise_to_equity(1000.0, 50.0, 200.0, 30.0, 20.0, 10.0)
        second = enterprise_to_equity(1000.0, 50.0, 200.0, 30.0, 20.0, 10.0)
        self.assertEqual(first, second)
        self.assertIsInstance(first, EquityBridge)
        with self.assertRaises(Exception):
            first.equity_value = 0.0  # type: ignore[misc]


class TestBridgeConsistencyWithDcf(unittest.TestCase):
    """dcf_valuation باید عیناً از همان پل استفاده کند"""

    def test_dcf_matches_bridge_bit_for_bit(self):
        projections = [
            CashFlowProjection(ebit=100.0, depreciation=10.0, capex=15.0, delta_nwc=5.0),
            CashFlowProjection(ebit=120.0, depreciation=12.0, capex=20.0, delta_nwc=8.0),
            CashFlowProjection(ebit=140.0, depreciation=14.0, capex=25.0, delta_nwc=10.0),
        ]
        result = dcf_valuation(
            projections, 0.10, 0.02, 5.0, 0.25,
            cash=50.0, debt=200.0, minority_interest=30.0, preferred_equity=20.0,
        )
        bridge = enterprise_to_equity(
            result.enterprise_value, 50.0, 200.0, 30.0, 20.0, 5.0
        )
        # مقایسه بیت‌به‌بیت (assertEqual)؛ ترتیب عملیات باید یکسان بماند
        self.assertEqual(result.equity_value, bridge.equity_value)
        self.assertEqual(result.value_per_share, bridge.value_per_share)


if __name__ == "__main__":
    unittest.main()
