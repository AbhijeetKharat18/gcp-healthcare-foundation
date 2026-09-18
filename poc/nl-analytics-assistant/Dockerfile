# NL Analytics Assistant - Cloud Run container.
# Defaults to the production path (Gemini on Vertex + BigQuery). Override the
# NLA_* env vars to run the offline demo (mock + DuckDB) in the same image.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    NLA_PROVIDER=vertex \
    NLA_EXECUTOR=bigquery

WORKDIR /srv/app

COPY app/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY app/nl_analytics ./nl_analytics
# Synthetic data is bundled so the same image can run the offline demo.
COPY data /srv/data

EXPOSE 8080

# Cloud Run provides $PORT.
CMD ["sh", "-c", "exec uvicorn nl_analytics.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
