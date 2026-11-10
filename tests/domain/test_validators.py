"""تست‌های مرزها و نگهبان‌های نوع اعتبارسنج‌های مشترک.

این تست‌ها شکاف‌های افشاشده در تست جهش (mutmut) را می‌بندند: کرانه‌های
شمول/عدم شمول، ورودی‌های None/bool و طول فهرست‌های ناهم‌خوان.

اجرا از ریشه پروژه:
    python3 -m unittest discover -s tests -t . -v
"""

import unittest

from stock_valuation.domain import validators
from stock_valuation.domain.errors import ValidationError


class TestNumericBoundaries(unittest.TestCase):
    """کرانه‌های شمول/عدم شمول اعتبارسنج‌های عددی"""

    def test_exact_min_spread_accepted(self):
        # 0.01 − 0.005 در ممیز شناور دقیقاً MIN_SPREAD است؛ کران شامل می‌شود.
        validators.validate_growth_rate_vs_return(0.005, 0.01)

    def test_percentage_bounds_inclusive(self):
        validators.validate_percentage(0.0, "نرخ رشد")
        validators.validate_percentage(2.0, "نرخ رشد")

    def test_small_positive_valuation_metric_accepted(self):
        validators.validate_valuation_metric(0.5, "شاخص هدف")

    def test_zero_risk_free_rate_accepted(self):
        validators.validate_risk_free_rate(0.0)

    def test_retention_ratio_upper_bound_exclusive(self):
        validators.validate_retention_ratio(0.0)
        for bad in (1.0, 1.5):
            with self.subTest(b=bad):
                with self.assertRaises(ValidationError):
                    validators.validate_retention_ratio(bad)


class TestSensitivityGridBoundaries(unittest.TestCase):
    """کرانه‌های شامل تعداد نقاط شبکه حساسیت"""

    def test_min_and_max_points_accepted(self):
        validators.validate_sensitivity_grid(0.01, 0.005, 3, 3)
        validators.validate_sensitivity_grid(0.01, 0.005, 11, 11)


class TestSequenceTypeGuards(unittest.TestCase):
    """نگهبان‌های نوع فهرست و درایه‌ها (bool عدد نیست)"""

    def test_covariance_none_rejected(self):
        with self.assertRaises(ValidationError):
            validators.validate_covariance_matrix(None)

    def test_covariance_bool_element_rejected(self):
        with self.assertRaises(ValidationError):
            validators.validate_covariance_matrix([[True, 0.0], [0.0, 1.0]])

    def test_covariance_zero_variance_asset_accepted(self):
        # واریانس صفر معتبر است؛ کوواریانس برون‌قطری آن سطر/ستون باید صفر باشد.
        validators.validate_covariance_matrix([[1.0, 0.0], [0.0, 0.0]])

    def test_covariance_large_scale_valid_correlation_accepted(self):
        # همبستگی ضمنی 3/4 = 0.75 معتبر است؛ مقیاس بزرگ نباید رد شود.
        validators.validate_covariance_matrix([[4.0, 3.0], [3.0, 4.0]])

    def test_mean_returns_bool_element_rejected(self):
        with self.assertRaises(ValidationError):
            validators.validate_mean_returns([True, 0.1])

    def test_weights_none_rejected(self):
        with self.assertRaises(ValidationError):
            validators.validate_weights(None, 2)

    def test_weights_bool_element_rejected(self):
        with self.assertRaises(ValidationError):
            validators.validate_weights([True, 0.0], 2)


class TestScenarioProbabilities(unittest.TestCase):
    """کرانه‌های بازه احتمال هر سناریو"""

    def test_probability_one_accepted(self):
        validators.validate_scenario_set(["bear", "bull"], [1.0, 0.0])

    def test_out_of_range_probabilities_rejected_even_if_sum_one(self):
        with self.assertRaises(ValidationError):
            validators.validate_scenario_set(["bear", "bull"], [1.5, -0.5])


class TestFootballRangeLengths(unittest.TestCase):
    """هر فهرست کرانه باید جداگانه هم‌طول نام‌ها باشد"""

    def test_mids_length_mismatch_rejected(self):
        with self.assertRaises(ValidationError):
            validators.validate_football_range_set(
                ["dcf", "pe"], [1.0, 2.0], [1.5], [2.0, 3.0]
            )

    def test_lows_length_mismatch_rejected(self):
        with self.assertRaises(ValidationError):
            validators.validate_football_range_set(
                ["dcf", "pe"], [1.0], [1.5, 2.5], [2.0, 3.0]
            )


if __name__ == "__main__":
    unittest.main()