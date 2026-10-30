# تصویر اجرایی بک‌اند FastAPI
# ساخت:  docker build -t stock-valuation-api .
# اجرا:  docker run -p 8000:8000 stock-valuation-api
FROM python:3.11-slim

WORKDIR /app

# وابستگی‌ها جدا از کد کپی می‌شوند تا تغییر سورس، کش این لایه را باطل نکند.
# فقط وابستگی‌های بک‌اند نصب می‌شوند؛ پشته Streamlit (requirements.txt) در تصویر لازم نیست.
COPY requirements-api.txt ./
RUN pip install --no-cache-dir -r requirements-api.txt

# فقط کد بک‌اند وارد تصویر می‌شود. نقطه ورود Streamlit، تنظیمات .streamlit،
# لایه نمایش `stock_valuation/ui` و فرانت‌اند React با .dockerignore حذف می‌شوند.
COPY stock_valuation ./stock_valuation

EXPOSE 8000

CMD ["uvicorn", "stock_valuation.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
