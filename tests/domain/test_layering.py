"""تست‌های مرز لایه دامنه: بدون وابستگی به لایه نمایش یا فریم‌ورک‌های وب.

ماژول‌های دامنه به‌صورت خودکار با ``pkgutil`` کشف می‌شوند؛ ماژول تازه‌ای که
به `stock_valuation.domain` اضافه شود بدون تغییر این فایل بررسی می‌شود.

اجرا از ریشه پروژه:
    python3 -m unittest discover -s tests -t . -v
"""

import ast
import importlib
import inspect
import pkgutil
import unittest

import stock_valuation.domain as domain_package
from stock_valuation.domain import cost_of_capital, dcf, dcf_analysis, equity
from stock_valuation.domain import errors, valuation_models
from stock_valuation.domain.errors import CalculationError


def _discover_logic_modules():
    """همه ماژول‌های بسته دامنه، مرتب‌شده بر اساس نام."""
    names = sorted(info.name for info in pkgutil.iter_modules(domain_package.__path__))
    return tuple(
        importlib.import_module(f"{domain_package.__name__}.{name}") for name in names
    )


class TestLayering(unittest.TestCase):
    """لایه محاسباتی نباید به لایه نمایش و فریم‌ورک‌های وب وابسته باشد"""

    LOGIC_MODULES = _discover_logic_modules()

    # بسته‌هایی که import کردنشان در لایه دامنه ممنوع است
    FORBIDDEN_PACKAGES = ("streamlit", "fastapi", "pydantic")

    @staticmethod
    def _imports(module) -> set:
        """نام ماژول‌های واردشده در یک ماژول"""
        tree = ast.parse(inspect.getsource(module))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        return imported

    def test_no_streamlit_import(self):
        discovered = {module.__name__ for module in self.LOGIC_MODULES}
        for expected in (cost_of_capital, dcf, dcf_analysis, equity):
            with self.subTest(module=expected.__name__):
                self.assertIn(expected.__name__, discovered)
        for module in self.LOGIC_MODULES:
            imported = self._imports(module)
            for forbidden in self.FORBIDDEN_PACKAGES:
                with self.subTest(module=module.__name__, forbidden=forbidden):
                    self.assertNotIn(forbidden, imported)

    def test_no_streamlit_usage(self):
        for module in self.LOGIC_MODULES:
            with self.subTest(module=module.__name__):
                tree = ast.parse(inspect.getsource(module))
                for node in ast.walk(tree):
                    if (isinstance(node, ast.Attribute)
                            and isinstance(node.value, ast.Name)
                            and node.value.id == "st"):
                        self.fail(f"ارجاع به st در {module.__name__} یافت شد")

    def test_no_session_state_reference(self):
        for module in self.LOGIC_MODULES:
            with self.subTest(module=module.__name__):
                self.assertNotIn("session_state", inspect.getsource(module))

    def test_exception_hierarchy_is_shared(self):
        self.assertIs(valuation_models.ValidationError, errors.ValidationError)
        self.assertIs(valuation_models.CalculationError, errors.CalculationError)
        self.assertTrue(issubclass(CalculationError, Exception))
        for module in (cost_of_capital, dcf, dcf_analysis, equity):
            with self.subTest(module=module.__name__):
                self.assertIs(module.ValidationError, errors.ValidationError)
                self.assertIs(module.CalculationError, errors.CalculationError)


if __name__ == "__main__":
    unittest.main()
