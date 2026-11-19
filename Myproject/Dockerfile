FROM python:3.14-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV DB_PATH=/data/data.db
EXPOSE 8000
# Docker сам питає /health і показує в docker compose ps, чи сервіс здоровий
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4)"
CMD ["python", "-m", "waitress", "--listen=0.0.0.0:8000", "app:app"]