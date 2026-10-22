"""استثناهای دامنه ارزیابی سهام.

این ماژول هیچ وابستگی‌ای به Streamlit یا هر کتابخانه نمایشی ندارد و صرفاً
قرارداد خطای لایه محاسباتی را تعریف می‌کند.
"""


class ValidationError(Exception):
    """خطای اعتبارسنجی ورودی"""
    pass


class CalculationError(Exception):
    """خطای محاسباتی"""
    pass
