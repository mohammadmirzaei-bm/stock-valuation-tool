"""تست‌های نقطه پایانی پیش‌بینی مبتنی بر محرک‌ها.

اجرا از ریشه پروژه:
    python3 -m unittest discover -s tests -t . -v
"""

import unittest

from pydantic import ValidationError as PydanticValidationError

from stock_valuation.api import schemas as s
from stock_valuation.api.routes import forecast as forecast_route
from stock_valuation.domain.errors import ValidationError


class TestForecastRoute(unittest.TestCase):
    """نگاشت درخواست/پاسخ مسیر forecast و خطاهای 400 و 422"""

    @staticmethod
    def _payload(**overrides):
        values = dict(
            base_revenue=1024.0,
            years=3,
            revenue_growth=0.25,
            ebitda_margin=0.5,
            da_pct_revenue=0.125,
            capex_pct_revenue=0.25,
            nwc_pct_incremental_revenue=0.5,
        )
        values.update(overrides)
        return s.ForecastRequest(**values)

    def test_happy_path_hand_computed(self):
        # درآمد پایه ۱۰۲۴ با رشد ۲۵٪: 1280، 1600 و 2000
        result = forecast_route.forecast(self._payload())
        self.assertEqual(result.revenues, [1280.0, 1600.0, 2000.0])
        self.assertEqual(result.ebitda, [640.0, 800.0, 1000.0])
        first = result.rows[0]
        self.assertEqual(first.year, 1)
        self.assertEqual(first.revenue, 1280.0)
        self.assertEqual(first.growth_percent, 25.0)
        self.assertEqual(first.ebitda_margin_percent, 50.0)
        self.assertEqual(first.ebit, 480.0)
        self.assertEqual(first.depreciation, 160.0)
        self.assertEqual(first.capex, 320.0)
        self.assertEqual(first.delta_nwc, 128.0)
        self.assertEqual(len(result.projections), 3)
        self.assertEqual(
            result.projections[1].model_dump(),
            {
                "ebit": 600.0,
                "depreciation": 200.0,
                "capex": 400.0,
                "delta_nwc": 160.0,
            },
        )

    def test_projections_fit_dcf_request_shape(self):
        # خروجی forecast باید مستقیماً ورودی DcfRequest شود
        result = forecast_route.forecast(self._payload())
        dcf_request = s.DcfRequest(
            projections=result.projections,
            wacc=0.10,
            terminal_growth=0.02,
            shares_outstanding=10.0,
            tax_rate=0.25,
        )
        self.assertEqual(len(dcf_request.projections), 3)
        self.assertEqual(dcf_request.projections[2].ebit, 750.0)

    def test_normalize_terminal_year_passthrough(self):
        result = forecast_route.forecast(
            self._payload(
                revenue_growth=0.0,
                normalize_terminal_year=True,
                terminal_growth=0.02,
            )
        )
        last = result.rows[-1]
        self.assertEqual(last.capex, last.depreciation)

    def test_domain_validation_error_is_400(self):
        # درآمد پایه صفر از Pydantic عبور می‌کند و دامنه آن را رد می‌کند
        with self.assertRaises(ValidationError):
            forecast_route.forecast(self._payload(base_revenue=0.0))

    def test_schema_violation_is_422(self):
        for years in (0, 51):
            with self.subTest(years=years):
                with self.assertRaises(PydanticValidationError):
                    self._payload(years=years)


if __name__ == "__main__":
    unittest.main()
