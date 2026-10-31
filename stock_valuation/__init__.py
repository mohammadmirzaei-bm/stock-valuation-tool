"""بسته اصلی ابزار ارزیابی سهام.

لایه دامنه (`stock_valuation.domain`) منطق محاسباتی خالص را در خود جای می‌دهد
و لایه API (`stock_valuation.api`) قرارداد FastAPI را برای فرانت‌اند React
تعریف می‌کند. اجرای سرویس:

    uvicorn stock_valuation.api.main:app --reload
"""
