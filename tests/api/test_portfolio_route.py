"""تست‌های نقاط پایانی آماره و بهینه‌سازی سبد.

اجرا از ریشه پروژه:
    python3 -m unittest discover -s tests -t . -v
"""

import math
import unittest

from pydantic import ValidationError as PydanticValidationError

from stock_valuation.api import schemas as s
from stock_valuation.api.routes import portfolio as portfolio_route
from stock_valuation.domain.errors import CalculationError, ValidationError

_PRICES = [
    [8.0, 12.0, 6.0, 6.0],
    [8.0, 8.0, 12.0, 6.0],
]


class TestPortfolioStatisticsRoute(unittest.TestCase):
    """آماره سالانه از قیمت؛ مسیر موفق، خطای دامنه و نقض اسکیما"""

    def test_happy_path_hand_computed(self):
        payload = s.PortfolioStatisticsRequest(
            assets=[
                s.PriceSeriesInput(name="الف", prices=_PRICES[0]),
                s.PriceSeriesInput(name="ب", prices=_PRICES[1]),
            ],
            periods_per_year=1,
        )
        result = portfolio_route.statistics(payload)
        self.assertEqual(result.observations, 3)
        self.assertEqual(result.mean_returns, [0.0, 0.0])
        self.assertEqual(result.mean_returns_percent, [0.0, 0.0])
        self.assertEqual(result.covariance, [[0.25, -0.125], [-0.125, 0.25]])
        self.assertEqual(result.volatilities, [0.5, 0.5])
        self.assertEqual(result.volatilities_percent, [50.0, 50.0])
        self.assertEqual(result.correlation, [[1.0, -0.5], [-0.5, 1.0]])

    def test_constant_prices_are_400(self):
        payload = s.PortfolioStatisticsRequest(
            assets=[
                s.PriceSeriesInput(name="الف", prices=[4.0, 4.0, 4.0]),
                s.PriceSeriesInput(name="ب", prices=[4.0, 8.0, 4.0]),
            ],
            periods_per_year=1,
        )
        with self.assertRaises(ValidationError):
            portfolio_route.statistics(payload)

    def test_schema_violation_is_422(self):
        with self.assertRaises(PydanticValidationError):
            s.PortfolioStatisticsRequest(
                assets=[
                    s.PriceSeriesInput(name="الف", prices=[1.0, 2.0, 3.0]),
                    s.PriceSeriesInput(name="ب", prices=[1.0, 2.0, 3.0]),
                ],
                periods_per_year=0,
            )
        with self.assertRaises(PydanticValidationError):
            s.PortfolioStatisticsRequest(
                assets=[
                    s.PriceSeriesInput(name="الف", prices=[1.0, 2.0, 3.0]),
                    s.PriceSeriesInput(name="ب", prices=[1.0, 2.0, 3.0]),
                ],
                periods_per_year=1,
                extra=True,
            )


class TestPortfolioOptimizeRoute(unittest.TestCase):
    """تحلیل سبد با داده مرجع دو دارایی"""

    @staticmethod
    def _payload(**overrides):
        body = dict(
            asset_names=["الف", "ب"],
            mean_returns=[0.10, 0.20],
            covariance=[[0.04, 0.0], [0.0, 0.16]],
            risk_free_rate=0.03,
            risk_aversion=3.0,
            allow_short=False,
            max_leverage=1.0,
            frontier_points=5,
        )
        body.update(overrides)
        return s.PortfolioOptimizeRequest(**body)

    def test_happy_path_reference(self):
        result = portfolio_route.optimize(self._payload())
        self.assertEqual([asset.name for asset in result.assets], ["الف", "ب"])
        self.assertAlmostEqual(result.min_variance.weights[0], 0.8, places=12)
        self.assertAlmostEqual(result.min_variance.weights[1], 0.2, places=12)
        self.assertAlmostEqual(result.min_variance.expected_return, 0.12, places=12)
        self.assertAlmostEqual(result.min_variance.variance, 0.032, places=12)
        self.assertIsNone(result.min_variance.sharpe_ratio)
        self.assertAlmostEqual(result.min_variance.weights_percent[0], 80.0, places=10)
        self.assertAlmostEqual(
            result.tangency.sharpe_ratio, math.sqrt(0.303125), places=12
        )
        self.assertAlmostEqual(result.complete_portfolio.tangency_weight, 0.9375, places=12)
        self.assertAlmostEqual(
            result.complete_portfolio.risk_free_weight, 0.0625, places=12
        )
        self.assertFalse(result.complete_portfolio.leverage_capped)
        self.assertFalse(result.complete_portfolio.clipped_to_zero)
        self.assertAlmostEqual(
            result.complete_portfolio.tangency_weight_percent, 93.75, places=10
        )
        self.assertEqual(len(result.frontier), 5)
        self.assertEqual(result.frontier[0].weights, result.min_variance.weights)
        self.assertEqual(result.equal_weight.weights, [0.5, 0.5])
        self.assertEqual(result.capital_allocation_line.points[0].volatility, 0.0)
        self.assertAlmostEqual(
            result.capital_allocation_line.slope, result.tangency.sharpe_ratio, places=12
        )
        self.assertAlmostEqual(result.assets[0].volatility_percent, 20.0, places=10)
        self.assertAlmostEqual(result.assets[1].expected_return_percent, 20.0, places=10)

    def test_singular_covariance_is_400(self):
        payload = self._payload(
            mean_returns=[0.10, 0.15],
            covariance=[[0.04, 0.08], [0.08, 0.16]],
            allow_short=True,
        )
        with self.assertRaises(CalculationError):
            portfolio_route.optimize(payload)

    def test_schema_violation_is_422(self):
        with self.assertRaises(PydanticValidationError):
            self._payload(frontier_points=4)
        with self.assertRaises(PydanticValidationError):
            self._payload(risk_aversion=0)
        with self.assertRaises(PydanticValidationError):
            s.PortfolioOptimizeRequest(
                asset_names=["الف", "ب"],
                mean_returns=[0.1, 0.2],
                covariance=[[0.04, 0.0], [0.0, 0.16]],
                risk_free_rate=0.03,
                risk_aversion=3.0,
                note="اضافی",
            )


if __name__ == "__main__":
    unittest.main()
