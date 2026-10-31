# تصویر اجرایی بک‌اند FastAPI
# ساخت:  docker build -t stock-valuation-api .
# اجرا:  docker run -p 8000:8000 stock-valuation-api
FROM python:3.11-slim

# لاگ‌ها بدون بافر به‌موقع در `docker logs` دیده می‌شوند و بایت‌کد در تصویر نوشته نمی‌شود.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# کاربر غیر ریشه پیش از کپی سورس ساخته می‌شود تا فایل‌ها مستقیماً با مالکیت درست
# وارد تصویر شوند و لایه chown اضافه‌ای لازم نباشد.
RUN useradd --create-home --uid 10001 appuser

# وابستگی‌ها جدا از کد کپی می‌شوند تا تغییر سورس، کش این لایه را باطل نکند.
# فقط وابستگی‌های بک‌اند نصب می‌شوند؛ requirements.txt در تصویر لازم نیست.
COPY --chown=appuser:appuser requirements-api.txt ./
RUN pip install --no-cache-dir -r requirements-api.txt

# فقط کد بک‌اند وارد تصویر می‌شود؛ فرانت‌اند React با .dockerignore حذف می‌شود.
COPY --chown=appuser:appuser stock_valuation ./stock_valuation

USER appuser

EXPOSE 8000

# بررسی سلامت با urllib استاندارد انجام می‌شود چون python:3.11-slim ابزار curl ندارد.
# urlopen برای هر کد غیر ۲۰۰ استثنا می‌دهد، پس exit code همان نتیجه بررسی است.
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"

CMD ["uvicorn", "stock_valuation.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
