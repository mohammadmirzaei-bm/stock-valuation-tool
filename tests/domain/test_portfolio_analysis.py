"""تست‌های واحد تحلیل سبد: سبد کامل، خط تخصیص و معیار هم‌وزن.

مرجع: μ = (0.10, 0.20)، Σ = diag(0.04, 0.16)، rf = 0.03، A = 3.
در این داده (E[Rp] − rf) / σp² = 2.8125 و y* = 0.9375.

اجرا از ریشه پروژه:
    python3 -m unittest discover -s tests -t . -v
"""

import inspect
import math
import unittest
from dataclasses import FrozenInstanceError

import stock_valuation.domain.portfolio as portfolio_module
import stock_valuation.domain.portfolio_stats as stats_module
from stock_valuation.domain.errors import CalculationError, ValidationError
from stock_valuation.domain.portfolio import PortfolioPoint
from stock_valuation.domain.portfolio_analysis import (
    PortfolioAnalysis,
    _complete_portfolio,
    analyze_portfolio,
)
from stock_valuation.domain.validators import CAL_VOLATILITY_MULTIPLIER

MU = [0.10, 0.20]
COV = [[0.04, 0.0], [0.0, 0.16]]
RF = 0.03
AVERSION = 3.0
NAMES = ["الف", "ب"]


def _analysis(**overrides):
    payload = dict(
        asset_names=NAMES,
        mean_returns=MU,
        covariance=COV,
        risk_free_rate=RF,
        risk_aversion=AVERSION,
        frontier_points=5,
    )
    payload.update(overrides)
    return analyze_portfolio(**payload)


class TestReferenceCompletePortfolio(unittest.TestCase):
    """هویت y* = 2.8125 / 3 و اجزای سبد کامل"""

    def test_y_star_identity(self):
        # پیش‌فرض فقط‌خرید است و در این داده با فروش مجاز یکی است
        for allow_short in (False, True):
            with self.subTest(allow_short=allow_short):
                result = _analysis(allow_short=allow_short)
                tangency = result.tangency
                identity = (tangency.expected_return - RF) / tangency.variance
                self.assertAlmostEqual(identity, 2.8125, places=12)
                complete = result.complete_portfolio
                self.assertAlmostEqual(complete.tangency_weight, 0.9375, places=12)
                self.assertAlmostEqual(complete.tangency_weight, identity / AVERSION, places=12)
                self.assertAlmostEqual(complete.risk_free_weight, 0.0625, places=12)
                self.assertFalse(complete.leverage_capped)
                self.assertFalse(complete.clipped_to_zero)
                self.assertAlmostEqual(complete.tangency_weight_percent, 93.75, places=10)
                self.assertAlmostEqual(complete.risk_free_weight_percent, 6.25, places=10)

    def test_complete_return_volatility_and_risky_weights(self):
        result = _analysis()
        tangency = result.tangency
        complete = result.complete_portfolio
        excess = tangency.expected_return - RF
        self.assertAlmostEqual(
            complete.expected_return, RF + 0.9375 * excess, places=12
        )
        self.assertAlmostEqual(
            complete.expected_return, 629 / 4800, places=12
        )
        self.assertAlmostEqual(
            complete.volatility, 0.9375 * tangency.volatility, places=12
        )
        self.assertAlmostEqual(complete.risky_weights[0], 7 / 12, places=12)
        self.assertAlmostEqual(complete.risky_weights[1], 17 / 48, places=12)
        self.assertAlmostEqual(sum(complete.risky_weights), 0.9375, places=12)
        self.assertAlmostEqual(
            sum(complete.risky_weights) + complete.risk_free_weight, 1.0, places=12
        )
        self.assertEqual(complete.risk_aversion, AVERSION)

    def test_assets_equal_weight_and_allocation_line(self):
        result = _analysis(asset_names=["  الف  ", "ب"])
        self.assertEqual([asset.name for asset in result.assets], ["الف", "ب"])
        self.assertAlmostEqual(result.assets[0].expected_return, 0.10, places=12)
        self.assertAlmostEqual(result.assets[1].expected_return, 0.20, places=12)
        self.assertAlmostEqual(result.assets[0].volatility, 0.20, places=12)
        self.assertAlmostEqual(result.assets[1].volatility, 0.40, places=12)
        self.assertAlmostEqual(result.assets[0].expected_return_percent, 10.0, places=10)
        self.assertAlmostEqual(result.assets[1].volatility_percent, 40.0, places=10)

        benchmark = result.equal_weight
        self.assertEqual(benchmark.weights, [0.5, 0.5])
        self.assertAlmostEqual(benchmark.expected_return, 0.15, places=12)
        self.assertAlmostEqual(benchmark.variance, 0.05, places=12)
        self.assertAlmostEqual(
            benchmark.sharpe_ratio, 0.12 / math.sqrt(0.05), places=12
        )

        line = result.capital_allocation_line
        self.assertAlmostEqual(line.risk_free_rate, RF, places=12)
        self.assertAlmostEqual(line.slope, result.tangency.sharpe_ratio, places=12)
        self.assertEqual(line.risk_free_rate_percent, 3.0)
        self.assertEqual(line.points[0].volatility, 0.0)
        self.assertAlmostEqual(line.points[0].expected_return, RF, places=12)
        self.assertAlmostEqual(
            line.points[1].volatility,
            CAL_VOLATILITY_MULTIPLIER * result.tangency.volatility,
            places=12,
        )
        self.assertAlmostEqual(
            line.points[1].expected_return,
            RF + line.slope * line.points[1].volatility,
            places=12,
        )
        # با مضرب ۲، سبد مماس وسط پاره‌خط است
        self.assertAlmostEqual(
            line.points[1].volatility / 2.0, result.tangency.volatility, places=12
        )

    def test_frontier_starts_at_min_variance(self):
        result = _analysis()
        self.assertEqual(len(result.frontier), 5)
        self.assertEqual(result.frontier[0], result.min_variance)
        self.assertIsNone(result.min_variance.sharpe_ratio)
        self.assertIsInstance(result, PortfolioAnalysis)

    def test_default_frontier_length(self):
        result = analyze_portfolio(NAMES, MU, COV, RF, AVERSION)
        self.assertEqual(len(result.frontier), 50)


class TestLeverageClip(unittest.TestCase):
    """برش y* به سقف اهرم، و گاردی که برش به صفر از آن نمی‌گذرد"""

    def test_cap_at_max_leverage(self):
        # A = 0.01 ⇒ y* خام = 281.25، سقف پیش‌فرض ۱
        result = _analysis(risk_aversion=0.01)
        complete = result.complete_portfolio
        self.assertTrue(complete.leverage_capped)
        self.assertFalse(complete.clipped_to_zero)
        self.assertEqual(complete.tangency_weight, 1.0)
        self.assertEqual(complete.risk_free_weight, 0.0)
        self.assertAlmostEqual(
            complete.expected_return, result.tangency.expected_return, places=12
        )
        self.assertAlmostEqual(
            complete.volatility, result.tangency.volatility, places=12
        )
        for got, want in zip(complete.risky_weights, result.tangency.weights):
            self.assertAlmostEqual(got, want, places=12)

    def test_cap_respects_explicit_max_leverage(self):
        result = _analysis(max_leverage=0.5)
        complete = result.complete_portfolio
        self.assertTrue(complete.leverage_capped)
        self.assertEqual(complete.tangency_weight, 0.5)
        self.assertAlmostEqual(complete.risk_free_weight, 0.5, places=12)
        excess = result.tangency.expected_return - RF
        self.assertAlmostEqual(complete.expected_return, RF + 0.5 * excess, places=12)
        self.assertAlmostEqual(
            complete.volatility, 0.5 * result.tangency.volatility, places=12
        )

    def test_max_leverage_zero_is_all_risk_free(self):
        result = _analysis(max_leverage=0.0)
        complete = result.complete_portfolio
        self.assertTrue(complete.leverage_capped)
        self.assertFalse(complete.clipped_to_zero)
        self.assertEqual(complete.tangency_weight, 0.0)
        self.assertEqual(complete.risk_free_weight, 1.0)
        self.assertAlmostEqual(complete.expected_return, RF, places=12)
        self.assertEqual(complete.volatility, 0.0)
        self.assertEqual(complete.risky_weights, [0.0, 0.0])

    def test_negative_excess_is_rejected_by_tangency(self):
        # rf بالاتر از هر دو بازده: سبد مماس تعریف نمی‌شود، پس y* هرگز منفی نمی‌شود.
        with self.assertRaises(ValidationError):
            _analysis(risk_free_rate=0.25)

    def test_defensive_clip_to_zero(self):
        # شاخه دفاعی؛ analyze_portfolio به آن نمی‌رسد.
        synthetic = PortfolioPoint(
            weights=[0.5, 0.5],
            expected_return=0.02,
            variance=0.04,
            volatility=0.2,
            sharpe_ratio=-0.05,
        )
        complete = _complete_portfolio(synthetic, RF, AVERSION, 1.0)
        self.assertTrue(complete.clipped_to_zero)
        self.assertFalse(complete.leverage_capped)
        self.assertEqual(complete.tangency_weight, 0.0)
        self.assertEqual(complete.risk_free_weight, 1.0)
        self.assertEqual(complete.risky_weights, [0.0, 0.0])
        self.assertAlmostEqual(complete.expected_return, RF, places=12)
        self.assertEqual(complete.volatility, 0.0)

    def test_overflowing_y_star_is_calculation_error(self):
        with self.assertRaises(CalculationError) as caught:
            _analysis(risk_aversion=1e-320)
        self.assertEqual(str(caught.exception), "نتیجه محاسبه نامعتبر است")


class TestValidationAndInvariants(unittest.TestCase):
    """نام‌ها، کران پارامترها، قطعیت و تغییرناپذیری"""

    def test_names_rejected(self):
        for names in (
            ["", "ب"],
            ["  ", "ب"],
            ["الف", "الف"],
            ["الف", " الف "],
            ["الف"],
            [None, "ب"],
        ):
            with self.subTest(names=names):
                with self.assertRaises(ValidationError):
                    _analysis(asset_names=names)

    def test_name_count_must_match_returns(self):
        with self.assertRaises(ValidationError):
            _analysis(asset_names=["الف", "ب", "جیم"])

    def test_risk_aversion_rejected(self):
        for bad in (0, -1.0, float("nan"), float("inf"), True, "3"):
            with self.subTest(bad=bad):
                with self.assertRaises(ValidationError):
                    _analysis(risk_aversion=bad)

    def test_max_leverage_bounds(self):
        _analysis(max_leverage=0.0)
        _analysis(max_leverage=3)
        for bad in (-0.01, 3.01, float("nan"), float("inf"), True, "1"):
            with self.subTest(bad=bad):
                with self.assertRaises(ValidationError):
                    _analysis(max_leverage=bad)

    def test_dependencies_do_not_import_analysis(self):
        for module in (portfolio_module, stats_module):
            self.assertNotIn("portfolio_analysis", inspect.getsource(module))

    def test_deterministic_frozen_and_inputs_unchanged(self):
        names = ["الف", "ب"]
        means = list(MU)
        cov = [row[:] for row in COV]
        snapshot = (list(names), list(means), [row[:] for row in cov])
        first = analyze_portfolio(names, means, cov, RF, AVERSION, frontier_points=5)
        second = analyze_portfolio(names, means, cov, RF, AVERSION, frontier_points=5)
        self.assertEqual(first, second)
        self.assertEqual((names, means, cov), snapshot)
        with self.assertRaises(FrozenInstanceError):
            first.tangency = None  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            first.complete_portfolio.tangency_weight = 0.0  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
