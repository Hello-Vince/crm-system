# syntax=docker/dockerfile:1.5
FROM python:3.14.2-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY libs/shared-python /shared-python
COPY apps/audit-service/requirements.txt .
RUN pip install --upgrade pip \
    && pip wheel --no-cache-dir --wheel-dir /build/wheels -r requirements.txt

FROM python:3.14.2-slim AS runtime

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /shared-python /shared-python
ENV PYTHONPATH="/shared-python:${PYTHONPATH}"

COPY --from=builder /build/wheels /wheels
RUN pip install --no-cache-dir /wheels/*

COPY apps/audit-service /app

RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8003
CMD ["python", "manage.py", "consume_events"]
