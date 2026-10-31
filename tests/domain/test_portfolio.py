"""تست‌های واحد بهینه‌سازی سبد: حداقل واریانس، مماس و مرز کارا.

مرجع دستی: دو دارایی با μ = (0.10, 0.20)، Σ = diag(0.04, 0.16) و rf = 0.03.

اجرا از ریشه پروژه:
    python3 -m unittest discover -s tests -t . -v
"""

import math
import unittest
from dataclasses import FrozenInstanceError

from stock_valuation.domain.errors import CalculationError, ValidationError
from stock_valuation.domain.portfolio import (
    PortfolioPoint,
    efficient_frontier,
    min_variance_portfolio,
    portfolio_performance,
    portfolio_point,
    tangency_portfolio,
)

MU = [0.10, 0.20]
COV = [[0.04, 0.0], [0.0, 0.16]]
RF = 0.03

# همبستگی ۰٫۹ با بازده دارایی پرنوسان‌تر کمتر: فروش استقراضی وزن منفی می‌دهد
MU_CORNER = [0.12, 0.10]
COV_CORNER = [[0.04, 0.072], [0.072, 0.16]]

MU3 = [0.08, 0.12, 0.15]
COV3 = [
    [0.04, 0.006, 0.012],
    [0.006, 0.09, 0.03],
    [0.012, 0.03, 0.16],
]


def _identity(count, variance=0.04):
    return [
        [variance if row == column else 0.0 for column in range(count)]
        for row in range(count)
    ]


def _grid_points(step_count=100):
    """همه وزن‌های سه‌دارایی با گام ۰٫۰۱ و مجموع ۱ (به‌صورت (وزن‌ها))."""
    for i in range(step_count + 1):
        for j in range(step_count + 1 - i):
            yield [i / step_count, j / step_count, (step_count - i - j) / step_count]


class TestReferenceTwoAssets(unittest.TestCase):
    """مرجع دستی؛ فقط‌خرید و فروش مجاز نتیجه یکسان می‌دهند"""

    def test_min_variance(self):
        for allow_short in (True, False):
            with self.subTest(allow_short=allow_short):
                point = min_variance_portfolio(MU, COV, allow_short)
                self.assertAlmostEqual(point.weights[0], 0.8, places=12)
                self.assertAlmostEqual(point.weights[1], 0.2, places=12)
                self.assertAlmostEqual(point.expected_return, 0.12, places=12)
                self.assertAlmostEqual(point.variance, 0.032, places=12)
                self.assertAlmostEqual(point.volatility, math.sqrt(0.032), places=12)
                self.assertIsNone(point.sharpe_ratio)

    def test_tangency(self):
        for allow_short in (True, False):
            with self.subTest(allow_short=allow_short):
                point = tangency_portfolio(MU, COV, RF, allow_short)
                self.assertAlmostEqual(point.weights[0], 1.75 / 2.8125, places=12)
                self.assertAlmostEqual(point.weights[1], 1.0625 / 2.8125, places=12)
                self.assertAlmostEqual(point.weights[0], 0.622222222222, places=10)
                self.assertAlmostEqual(point.weights[1], 0.377777777778, places=10)
                # Sharpe² = (μ − rf)ᵀ Σ⁻¹ (μ − rf)
                self.assertAlmostEqual(point.sharpe_ratio, math.sqrt(0.303125), places=12)
                self.assertAlmostEqual(point.sharpe_ratio, 0.550568, places=6)

    def test_percent_properties(self):
        point = min_variance_portfolio(MU, COV, True)
        self.assertAlmostEqual(point.expected_return_percent, 12.0, places=10)
        self.assertAlmostEqual(point.volatility_percent, math.sqrt(0.032) * 100, places=10)
        self.assertAlmostEqual(point.weights_percent[0], 80.0, places=10)

    def test_portfolio_performance(self):
        expected, volatility = portfolio_performance([0.8, 0.2], MU, COV)
        self.assertAlmostEqual(expected, 0.12, places=12)
        self.assertAlmostEqual(volatility, math.sqrt(0.032), places=12)

    def test_portfolio_point_with_rate(self):
        point = portfolio_point([0.5, 0.5], MU, COV, RF)
        # بازده 0.15، واریانس 0.25·0.04 + 0.25·0.16 = 0.05
        self.assertAlmostEqual(point.expected_return, 0.15, places=12)
        self.assertAlmostEqual(point.variance, 0.05, places=12)
        self.assertAlmostEqual(point.sharpe_ratio, 0.12 / math.sqrt(0.05), places=12)
        self.assertIsNone(portfolio_point([0.5, 0.5], MU, COV).sharpe_ratio)

    def test_performance_weight_validation(self):
        for weights in ([0.5, 0.4], [0.5], [float("nan"), 0.5], [float("inf"), 0.0]):
            with self.subTest(weights=weights):
                with self.assertRaises(ValidationError):
                    portfolio_performance(weights, MU, COV)
        # مجموع در تلورانس 1e-6 پذیرفته می‌شود
        portfolio_performance([0.5, 0.5 + 1e-7], MU, COV)
        # فروش استقراضی (وزن منفی با مجموع ۱) مجاز است
        portfolio_performance([1.5, -0.5], MU, COV)


class TestShortVersusLongOnly(unittest.TestCase):
    """وزن منفی در فروش مجاز و جواب گوشه‌ای در فقط‌خرید"""

    def test_min_variance_corner(self):
        short = min_variance_portfolio(MU_CORNER, COV_CORNER, True)
        self.assertAlmostEqual(short.weights[0], 11 / 7, places=12)
        self.assertAlmostEqual(short.weights[1], -4 / 7, places=12)
        long_only = min_variance_portfolio(MU_CORNER, COV_CORNER, False)
        self.assertEqual(long_only.weights, [1.0, 0.0])
        self.assertAlmostEqual(long_only.variance, 0.04, places=12)
        self.assertGreater(long_only.variance, short.variance)

    def test_tangency_corner(self):
        short = tangency_portfolio(MU_CORNER, COV_CORNER, RF, True)
        self.assertLess(short.weights[1], 0.0)
        long_only = tangency_portfolio(MU_CORNER, COV_CORNER, RF, False)
        self.assertEqual(long_only.weights, [1.0, 0.0])
        self.assertAlmostEqual(long_only.sharpe_ratio, 0.09 / 0.2, places=12)
        self.assertGreater(short.sharpe_ratio, long_only.sharpe_ratio)

    def test_frontier_short_rejected_when_gmv_return_exceeds_max_asset(self):
        # بازده GMV با فروش ≈ 0.1314 و بیشتر از 0.12 است
        with self.assertRaises(ValidationError):
            efficient_frontier(MU_CORNER, COV_CORNER, True)

    def test_frontier_long_only_degenerate_single_point_rejected(self):
        # GMV فقط‌خرید همان دارایی با بیشترین بازده است
        with self.assertRaises(ValidationError):
            efficient_frontier(MU_CORNER, COV_CORNER, False)

    def test_equal_expected_returns_rejected(self):
        for allow_short in (True, False):
            with self.subTest(allow_short=allow_short):
                with self.assertRaises(ValidationError):
                    efficient_frontier([0.1, 0.1], COV, allow_short)


class TestGridCrossCheck(unittest.TestCase):
    """فقط‌خرید سه‌دارایی در برابر شبکه کامل وزن با گام ۰٫۰۱"""

    @classmethod
    def setUpClass(cls):
        cls.grid = []
        for weights in _grid_points():
            expected, volatility = portfolio_performance(weights, MU3, COV3)
            cls.grid.append((weights, expected, volatility * volatility))

    def test_min_variance_against_grid(self):
        point = min_variance_portfolio(MU3, COV3, False)
        variances = [variance for _, _, variance in self.grid]
        self.assertLessEqual(point.variance, min(variances) + 1e-12)
        self.assertLess(min(variances) - point.variance, 1e-4)

    def test_tangency_against_grid(self):
        point = tangency_portfolio(MU3, COV3, RF, False)
        sharpes = [(ret - RF) / math.sqrt(var) for _, ret, var in self.grid if var > 0]
        self.assertGreaterEqual(point.sharpe_ratio, max(sharpes) - 1e-12)
        self.assertLess(point.sharpe_ratio - max(sharpes), 1e-3)

    def test_frontier_not_worse_than_any_grid_point(self):
        frontier = efficient_frontier(MU3, COV3, False, points=25)
        for point in frontier:
            for _, ret, var in self.grid:
                if ret >= point.expected_return:
                    self.assertGreaterEqual(var, point.variance - 1e-12)


class TestEfficientFrontier(unittest.TestCase):
    """شکل، یکنوایی و نقاط انتهایی مرز کارا"""

    def test_reference_points(self):
        for allow_short in (True, False):
            with self.subTest(allow_short=allow_short):
                frontier = efficient_frontier(MU, COV, allow_short, points=5)
                self.assertEqual(len(frontier), 5)
                expected = [
                    (0.12, [0.8, 0.2], 0.032),
                    (0.14, [0.6, 0.4], 0.04),
                    (0.16, [0.4, 0.6], 0.064),
                    (0.18, [0.2, 0.8], 0.10400000000000001),
                    (0.20, [0.0, 1.0], 0.16),
                ]
                for point, (ret, weights, variance) in zip(frontier, expected):
                    self.assertAlmostEqual(point.expected_return, ret, places=10)
                    self.assertAlmostEqual(point.variance, variance, places=10)
                    for got, want in zip(point.weights, weights):
                        self.assertAlmostEqual(got, want, places=10)
                    self.assertIsNone(point.sharpe_ratio)

    def test_monotone_first_is_gmv_last_is_max_asset(self):
        frontier = efficient_frontier(MU3, COV3, False, points=40)
        gmv = min_variance_portfolio(MU3, COV3, False)
        self.assertEqual(frontier[0], gmv)
        self.assertEqual(len(frontier), 40)
        for previous, current in zip(frontier, frontier[1:]):
            self.assertGreater(current.expected_return, previous.expected_return)
            self.assertGreaterEqual(current.volatility, previous.volatility - 1e-12)
        last = frontier[-1]
        self.assertAlmostEqual(last.expected_return, max(MU3), places=12)
        for got, want in zip(last.weights, [0.0, 0.0, 1.0]):
            self.assertAlmostEqual(got, want, places=12)
        for point in frontier:
            self.assertTrue(all(weight >= 0.0 for weight in point.weights))
            self.assertAlmostEqual(sum(point.weights), 1.0, places=12)

    def test_short_frontier_is_monotone_with_exact_endpoints(self):
        frontier = efficient_frontier(MU3, COV3, True, points=30)
        self.assertEqual(frontier[0], min_variance_portfolio(MU3, COV3, True))
        self.assertAlmostEqual(frontier[-1].expected_return, max(MU3), places=12)
        for previous, current in zip(frontier, frontier[1:]):
            self.assertGreater(current.expected_return, previous.expected_return)
            self.assertGreaterEqual(current.volatility, previous.volatility - 1e-12)

    def test_two_fund_theorem(self):
        # بازده نقاط هم‌فاصله است، پس طبق قضیه دو‌صندوق وزن‌ها خطی‌اند:
        # تفاضل مرتبه دوم هر وزن صفر می‌شود.
        frontier = efficient_frontier(MU3, COV3, True, points=9)
        for asset in range(3):
            series = [point.weights[asset] for point in frontier]
            for a, b, c in zip(series, series[1:], series[2:]):
                self.assertAlmostEqual(a - 2 * b + c, 0.0, places=10)

    def test_points_bounds(self):
        self.assertEqual(len(efficient_frontier(MU, COV, True, points=5)), 5)
        self.assertEqual(len(efficient_frontier(MU, COV, True, points=200)), 200)
        for bad in (4, 201, 0, True, 10.0, "10"):
            with self.subTest(bad=bad):
                with self.assertRaises(ValidationError):
                    efficient_frontier(MU, COV, True, points=bad)


class TestSingularAndDegenerate(unittest.TestCase):
    """همبستگی کامل (Σ منفرد) و نرخ بدون ریسک بالا"""

    MU_S = [0.10, 0.15]
    COV_S = [[0.04, 0.08], [0.08, 0.16]]

    def test_short_singular_is_calculation_error(self):
        with self.assertRaises(CalculationError):
            min_variance_portfolio(self.MU_S, self.COV_S, True)
        with self.assertRaises(CalculationError):
            tangency_portfolio(self.MU_S, self.COV_S, RF, True)

    def test_long_only_skips_singular_support(self):
        gmv = min_variance_portfolio(self.MU_S, self.COV_S, False)
        self.assertEqual(gmv.weights, [1.0, 0.0])
        tangent = tangency_portfolio(self.MU_S, self.COV_S, RF, False)
        self.assertEqual(tangent.weights, [1.0, 0.0])
        self.assertAlmostEqual(tangent.sharpe_ratio, 0.07 / 0.2, places=12)

    def test_long_only_frontier_with_singular_covariance(self):
        frontier = efficient_frontier(self.MU_S, self.COV_S, False, points=5)
        self.assertEqual(frontier[0].weights, [1.0, 0.0])
        for got, want in zip(frontier[-1].weights, [0.0, 1.0]):
            self.assertAlmostEqual(got, want, places=12)
        for point in frontier:
            self.assertAlmostEqual(sum(point.weights), 1.0, places=12)

    def test_zero_variance_asset_long_only(self):
        gmv = min_variance_portfolio([0.02, 0.10], [[0.0, 0.0], [0.0, 0.04]], False)
        self.assertEqual(gmv.weights, [1.0, 0.0])

    def test_all_excess_returns_negative_rejected(self):
        for allow_short in (True, False):
            with self.subTest(allow_short=allow_short):
                with self.assertRaises(ValidationError):
                    tangency_portfolio([0.01, 0.02], COV, 0.05, allow_short)

    def test_rf_above_gmv_return(self):
        # rf = 0.15 > بازده GMV = 0.12: با فروش تعریف‌نشده است
        with self.assertRaises(ValidationError) as caught:
            tangency_portfolio(MU, COV, 0.15, True)
        self.assertIn("حداقل واریانس", str(caught.exception))
        # فقط‌خرید: تنها دارایی دوم بازده مازاد مثبت دارد
        point = tangency_portfolio(MU, COV, 0.15, False)
        self.assertEqual(point.weights, [0.0, 1.0])
        self.assertAlmostEqual(point.sharpe_ratio, 0.05 / 0.4, places=12)


class TestValidation(unittest.TestCase):
    """ورودی نامعتبر در همه توابع"""

    def test_asset_count_bounds(self):
        with self.assertRaises(ValidationError):
            min_variance_portfolio([0.1], [[0.04]], True)
        with self.assertRaises(ValidationError):
            min_variance_portfolio([0.1] * 31, _identity(31), True)

    def test_long_only_asset_limit(self):
        point = min_variance_portfolio([0.1] * 8, _identity(8), False)
        for weight in point.weights:
            self.assertAlmostEqual(weight, 0.125, places=12)
        for function in (
            lambda: min_variance_portfolio([0.1] * 9, _identity(9), False),
            lambda: tangency_portfolio([0.1] * 9, _identity(9), RF, False),
            lambda: efficient_frontier([0.1] * 9, _identity(9), False),
        ):
            with self.assertRaises(ValidationError):
                function()
        # با فروش مجاز، ۹ دارایی مشکلی ندارد
        short = min_variance_portfolio([0.1] * 9, _identity(9), True)
        self.assertAlmostEqual(short.weights[0], 1 / 9, places=12)

    def test_non_finite_rejected(self):
        for bad in (float("nan"), float("inf"), -float("inf")):
            with self.subTest(bad=bad):
                with self.assertRaises(ValidationError):
                    min_variance_portfolio([bad, 0.2], COV, True)
                with self.assertRaises(ValidationError):
                    min_variance_portfolio(MU, [[bad, 0.0], [0.0, 0.16]], True)
                with self.assertRaises(ValidationError):
                    tangency_portfolio(MU, COV, bad, True)

    def test_risk_free_rate_rejected(self):
        for bad in (-0.01, True, "0.03"):
            with self.subTest(bad=bad):
                with self.assertRaises(ValidationError):
                    tangency_portfolio(MU, COV, bad, True)

    def test_asymmetric_covariance_rejected(self):
        with self.assertRaises(ValidationError):
            min_variance_portfolio(MU, [[0.04, 0.01], [0.02, 0.16]], True)

    def test_negative_variance_rejected(self):
        with self.assertRaises(ValidationError):
            min_variance_portfolio(MU, [[-0.04, 0.0], [0.0, 0.16]], True)

    def test_shape_mismatch_rejected(self):
        with self.assertRaises(ValidationError):
            min_variance_portfolio([0.1, 0.2, 0.3], COV, True)
        with self.assertRaises(ValidationError):
            min_variance_portfolio(MU, [[0.04, 0.0, 0.0], [0.0, 0.16, 0.0]], True)

    def test_allow_short_must_be_bool(self):
        for bad in (1, 0, None, "yes"):
            with self.subTest(bad=bad):
                with self.assertRaises(ValidationError):
                    min_variance_portfolio(MU, COV, bad)


class TestDeterminismAndImmutability(unittest.TestCase):
    """قطعی بودن، تغییرناپذیری نتیجه و دست‌نخورده ماندن ورودی"""

    def test_deterministic_and_inputs_unchanged(self):
        mu = list(MU3)
        cov = [row[:] for row in COV3]
        mu_snapshot = list(mu)
        cov_snapshot = [row[:] for row in cov]
        for allow_short in (True, False):
            with self.subTest(allow_short=allow_short):
                first = (
                    min_variance_portfolio(mu, cov, allow_short),
                    tangency_portfolio(mu, cov, RF, allow_short),
                    efficient_frontier(mu, cov, allow_short, points=10),
                )
                second = (
                    min_variance_portfolio(mu, cov, allow_short),
                    tangency_portfolio(mu, cov, RF, allow_short),
                    efficient_frontier(mu, cov, allow_short, points=10),
                )
                self.assertEqual(first, second)
        self.assertEqual(mu, mu_snapshot)
        self.assertEqual(cov, cov_snapshot)

    def test_result_is_frozen(self):
        point = min_variance_portfolio(MU, COV, True)
        self.assertIsInstance(point, PortfolioPoint)
        with self.assertRaises(FrozenInstanceError):
            point.expected_return = 0.0  # type: ignore[misc]

    def test_result_weights_independent_of_input(self):
        mu = list(MU)
        point = portfolio_point([0.5, 0.5], mu, COV)
        mu[0] = 9.0
        self.assertAlmostEqual(point.expected_return, 0.15, places=12)


if __name__ == "__main__":
    unittest.main()
