"""تست‌های واحد بازده ساده و آماره نمونه‌ای سبد.

اجرا از ریشه پروژه:
    python3 -m unittest discover -s tests -t . -v
"""

import unittest
from dataclasses import FrozenInstanceError

from stock_valuation.domain.errors import CalculationError, ValidationError
from stock_valuation.domain.portfolio_stats import (
    SampleStatistics,
    returns_from_prices,
    sample_statistics,
)
from stock_valuation.domain.validators import (
    CORRELATION_TOLERANCE,
    COVARIANCE_SYMMETRY_TOLERANCE,
    validate_asset_names,
    validate_covariance_matrix,
    validate_periods_per_year,
)

# قیمت‌ها بازده [[0.5, -0.5, 0.0], [0.0, 0.5, -0.5]] را می‌سازند.
_PRICES = [
    [8.0, 12.0, 6.0, 6.0],
    [8.0, 8.0, 12.0, 6.0],
]
_RETURNS = [
    [0.5, -0.5, 0.0],
    [0.0, 0.5, -0.5],
]


class TestReturnsFromPrices(unittest.TestCase):
    """بازده ساده؛ قیمت مثبت و هم‌طول، حداقل سه مشاهده"""

    def test_hand_computed_two_assets(self):
        self.assertEqual(returns_from_prices(_PRICES), _RETURNS)

    def test_too_few_observations(self):
        with self.assertRaises(ValidationError):
            returns_from_prices([[1.0, 2.0], [1.0, 2.0]])

    def test_unequal_lengths(self):
        with self.assertRaises(ValidationError):
            returns_from_prices([[1.0, 2.0, 3.0], [1.0, 2.0]])

    def test_non_positive_prices(self):
        for bad in (0.0, -1.0):
            with self.subTest(bad=bad):
                with self.assertRaises(ValidationError):
                    returns_from_prices([[1.0, bad, 1.0], [1.0, 2.0, 1.0]])

    def test_non_finite_prices(self):
        for bad in (float("nan"), float("inf"), -float("inf")):
            with self.subTest(bad=bad):
                with self.assertRaises(ValidationError):
                    returns_from_prices([[1.0, bad, 1.0], [1.0, 2.0, 1.0]])

    def test_asset_count_bounds(self):
        with self.assertRaises(ValidationError):
            returns_from_prices([[1.0, 2.0, 3.0]])
        with self.assertRaises(ValidationError):
            returns_from_prices([[1.0, 2.0, 1.0] for _ in range(31)])

    def test_constant_prices_are_valid_returns(self):
        # واریانس صفر اینجا رد نمی‌شود؛ sample_statistics آن را رد می‌کند.
        returns = returns_from_prices([[4.0, 4.0, 4.0], [4.0, 8.0, 4.0]])
        self.assertEqual(returns[0], [0.0, 0.0])
        self.assertEqual(returns[1], [1.0, -0.5])

    def test_overflowing_return_is_calculation_error(self):
        with self.assertRaises(CalculationError) as caught:
            returns_from_prices(
                [[1e-308, 1e308, 1.0], [1.0, 1.0, 2.0]]
            )
        self.assertEqual(str(caught.exception), "نتیجه محاسبه نامعتبر است")

    def test_inputs_not_mutated(self):
        prices = [[8.0, 12.0, 6.0, 6.0], [8.0, 8.0, 12.0, 6.0]]
        snapshot = [row[:] for row in prices]
        returns_from_prices(prices)
        self.assertEqual(prices, snapshot)


class TestSampleStatistics(unittest.TestCase):
    """آماره دستی، سال‌سازی خطی، و رد سری ثابت"""

    def test_hand_computed_two_assets(self):
        result = sample_statistics(_RETURNS, 1)
        self.assertIsInstance(result, SampleStatistics)
        self.assertEqual(result.observations, 3)
        self.assertEqual(result.mean_returns, [0.0, 0.0])
        self.assertEqual(result.covariance, [[0.25, -0.125], [-0.125, 0.25]])
        self.assertEqual(result.volatilities, [0.5, 0.5])
        self.assertEqual(result.correlation, [[1.0, -0.5], [-0.5, 1.0]])
        self.assertEqual(result.mean_returns_percent, [0.0, 0.0])
        self.assertEqual(result.volatilities_percent, [50.0, 50.0])
        validate_covariance_matrix(result.covariance)

    def test_annualization_scales_covariance_not_correlation(self):
        result = sample_statistics(_RETURNS, 4)
        self.assertEqual(result.mean_returns, [0.0, 0.0])
        self.assertEqual(result.covariance, [[1.0, -0.5], [-0.5, 1.0]])
        self.assertEqual(result.volatilities, [1.0, 1.0])
        self.assertEqual(result.correlation, [[1.0, -0.5], [-0.5, 1.0]])
        self.assertEqual(result.observations, 3)

    def test_annualization_scales_arithmetic_mean(self):
        # میانگین دوره [0.125, 0.5] با دو دوره در سال → [0.25, 1].
        # با دو مشاهده همبستگی کامل است ولی واریانس مثبت می‌ماند.
        result = sample_statistics([[0.5, -0.25], [0.25, 0.75]], 2)
        self.assertEqual(result.observations, 2)
        self.assertEqual(result.mean_returns, [0.25, 1.0])
        self.assertEqual(result.mean_returns_percent, [25.0, 100.0])
        self.assertEqual(result.covariance, [[0.5625, -0.375], [-0.375, 0.25]])
        self.assertEqual(result.volatilities, [0.75, 0.5])
        self.assertEqual(result.correlation[0][1], -1.0)

    def test_from_prices_matches_hand_returns(self):
        result = sample_statistics(returns_from_prices(_PRICES), 1)
        direct = sample_statistics(_RETURNS, 1)
        self.assertEqual(result, direct)

    def test_constant_series_rejected(self):
        returns = returns_from_prices([[4.0, 4.0, 4.0], [4.0, 8.0, 4.0]])
        with self.assertRaises(ValidationError) as caught:
            sample_statistics(returns, 1)
        self.assertIn("واریانس", str(caught.exception))

    def test_direct_zero_variance_rejected(self):
        with self.assertRaises(ValidationError):
            sample_statistics([[0.0, 0.0, 0.0], [0.5, -0.5, 0.0]], 1)

    def test_too_few_return_observations(self):
        with self.assertRaises(ValidationError):
            sample_statistics([[0.1], [0.2]], 1)

    def test_unequal_return_lengths(self):
        with self.assertRaises(ValidationError):
            sample_statistics([[0.1, 0.2], [0.1, 0.2, 0.3]], 1)

    def test_non_finite_returns_rejected(self):
        for bad in (float("nan"), float("inf")):
            with self.subTest(bad=bad):
                with self.assertRaises(ValidationError):
                    sample_statistics([[bad, 0.1], [0.1, 0.2]], 1)

    def test_periods_per_year_bounds(self):
        sample_statistics(_RETURNS, 1)
        sample_statistics(_RETURNS, 366)
        for bad in (0, 367, -1, True, 12.0, "12"):
            with self.subTest(bad=bad):
                with self.assertRaises(ValidationError):
                    sample_statistics(_RETURNS, bad)

    def test_max_assets_accepted_and_one_more_rejected(self):
        series = [[0.5, -0.5, 0.0] for _ in range(30)]
        result = sample_statistics(series, 1)
        self.assertEqual(len(result.mean_returns), 30)
        self.assertEqual(result.correlation[0][1], 1.0)
        with self.assertRaises(ValidationError):
            sample_statistics([[0.5, -0.5, 0.0] for _ in range(31)], 1)

    def test_overflowing_sample_moment_is_calculation_error(self):
        with self.assertRaises(CalculationError) as caught:
            sample_statistics([[1e308, 0.0], [0.0, 1e308]], 366)
        self.assertEqual(str(caught.exception), "نتیجه محاسبه نامعتبر است")

    def test_inputs_not_mutated_and_result_frozen(self):
        returns = [row[:] for row in _RETURNS]
        snapshot = [row[:] for row in returns]
        first = sample_statistics(returns, 1)
        second = sample_statistics(returns, 1)
        self.assertEqual(first, second)
        self.assertEqual(returns, snapshot)
        with self.assertRaises(FrozenInstanceError):
            first.observations = 0  # type: ignore[misc]


class TestPortfolioValidators(unittest.TestCase):
    """نام دارایی، دوره سال و ماتریس کوواریانس"""

    def test_asset_names(self):
        validate_asset_names(["الف", "ب"])
        validate_asset_names(["الف", "ب "])
        for names in (
            ["", "ب"],
            ["  ", "ب"],
            ["الف", "الف"],
            ["الف", " الف "],
            ["الف"],
            ["الف"] * 31,
            [None, "ب"],
        ):
            with self.subTest(names=names):
                with self.assertRaises(ValidationError):
                    validate_asset_names(names)

    def test_periods_per_year_validator(self):
        validate_periods_per_year(1)
        validate_periods_per_year(366)
        for bad in (0, 367, True, 4.0):
            with self.subTest(bad=bad):
                with self.assertRaises(ValidationError):
                    validate_periods_per_year(bad)

    def test_covariance_symmetry_tolerance(self):
        half = COVARIANCE_SYMMETRY_TOLERANCE / 2.0
        validate_covariance_matrix([[1.0, 0.1], [0.1 + half, 1.0]])
        with self.assertRaises(ValidationError):
            validate_covariance_matrix(
                [[1.0, 0.1], [0.1 + COVARIANCE_SYMMETRY_TOLERANCE * 10.0, 1.0]]
            )

    def test_negative_diagonal_rejected(self):
        with self.assertRaises(ValidationError):
            validate_covariance_matrix([[-0.01, 0.0], [0.0, 1.0]])

    def test_correlation_above_one_tolerance(self):
        within = 1.0 + CORRELATION_TOLERANCE / 2.0
        validate_covariance_matrix([[1.0, within], [within, 1.0]])
        beyond = 1.0 + CORRELATION_TOLERANCE * 10.0
        with self.assertRaises(ValidationError):
            validate_covariance_matrix([[1.0, beyond], [beyond, 1.0]])

    def test_zero_diagonal_requires_zero_covariance(self):
        validate_covariance_matrix([[0.0, 0.0], [0.0, 1.0]])
        with self.assertRaises(ValidationError):
            validate_covariance_matrix([[0.0, 0.2], [0.2, 1.0]])

    def test_covariance_input_not_mutated(self):
        matrix = [[1.0, 0.25], [0.25, 1.0]]
        snapshot = [row[:] for row in matrix]
        validate_covariance_matrix(matrix)
        self.assertEqual(matrix, snapshot)


if __name__ == "__main__":
    unittest.main()
