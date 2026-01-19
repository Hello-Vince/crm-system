# syntax=docker/dockerfile:1.5
FROM python:3.14.2-slim AS builder

WORKDIR /build
COPY libs/shared-python /shared-python
COPY apps/geocode-worker/requirements.txt .
RUN pip install --upgrade pip \
    && pip wheel --no-cache-dir --wheel-dir /build/wheels -r requirements.txt

FROM python:3.14.2-slim AS runtime

WORKDIR /app
COPY --from=builder /shared-python /shared-python
ENV PYTHONPATH="/shared-python:${PYTHONPATH}"

COPY --from=builder /build/wheels /wheels
RUN pip install --no-cache-dir /wheels/*

COPY apps/geocode-worker /app

RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

ENV PYTHONUNBUFFERED=1
CMD ["python", "-m", "geocode_worker"]
