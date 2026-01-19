# syntax=docker/dockerfile:1.5
# Stage 1: Builder
FROM python:3.14.2-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy shared library
COPY libs/shared-python /shared-python

# Install Python dependencies
COPY apps/identity-service/requirements.txt .
RUN pip install --upgrade pip \
    && pip wheel --no-cache-dir --wheel-dir /build/wheels -r requirements.txt

# Stage 2: Runtime
FROM python:3.14.2-slim AS runtime

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy shared library
COPY --from=builder /shared-python /shared-python
ENV PYTHONPATH="/shared-python:${PYTHONPATH}"

# Copy wheels and install
COPY --from=builder /build/wheels /wheels
RUN pip install --no-cache-dir /wheels/*

# Copy application code
COPY apps/identity-service /app

# Create non-root user
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8001
CMD ["gunicorn", "identity.wsgi:application", "--bind", "0.0.0.0:8001"]
