"""تست‌های دودی داخل برنامه."""

import unittest

from stock_valuation.domain import self_tests


class TestSelfTests(unittest.TestCase):
    """تست‌های دودی داخل برنامه"""

    def test_all_self_tests_pass(self):
        results = self_tests.run_self_tests()
        self.assertEqual(len(results), 8)
        for result in results:
            self.assertTrue(result.startswith("✅"), result)


if __name__ == "__main__":
    unittest.main()
