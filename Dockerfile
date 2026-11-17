# syntax=docker/dockerfile:1
FROM python:3.12-bookworm AS builder
WORKDIR /app
ENV PIP_NO_CACHE_DIR=1
COPY requirements.txt .
RUN pip wheel -w /wheels -r requirements.txt

FROM python:3.12-slim-bookworm AS runner
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=10000
RUN useradd --create-home --uid 1001 appuser
COPY --from=builder /wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt \
    && rm -rf /wheels
COPY app.py ./
COPY webhook_monitor ./webhook_monitor
COPY templates ./templates
COPY samples ./samples
RUN chown -R appuser:appuser /app
USER appuser
EXPOSE 10000
CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:${PORT} --workers 1 --threads 4 --timeout 30 --access-logfile - --error-logfile - app:app"]
