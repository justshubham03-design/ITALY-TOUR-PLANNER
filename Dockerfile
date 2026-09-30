# Viaggio Italia - Production Dockerfile for Railway
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1     PYTHONDONTWRITEBYTECODE=1     PORT=8080

WORKDIR /app

COPY requirements.txt /app/
RUN if [ -s requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

COPY . /app/

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3   CMD python3 -c "import urllib.request, os; port = os.environ.get('PORT', '8080'); urllib.request.urlopen(f'http://127.0.0.1:{port}/api/health')" || exit 1

CMD ["python3", "web/app.py"]
