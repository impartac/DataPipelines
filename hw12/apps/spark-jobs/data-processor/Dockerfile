# =============================================================================
# Spark Data Processor - Docker Image
# =============================================================================
# Multi-stage build:
#   Stage 1 (builder): install Python dependencies
#   Stage 2 (runtime): minimal production image
# =============================================================================

# ---- Stage 1: builder ----
FROM python:3.10-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# Ensure /root/.local exists even if requirements.txt is empty
RUN mkdir -p /root/.local && \
    pip install --no-cache-dir --user -r requirements.txt || true

# ---- Stage 2: runtime ----
FROM python:3.10-slim AS runtime

LABEL maintainer="hse-data-pipelines"
LABEL version="1.0.0"
LABEL description="Spark Data Processing Job"

# Copy installed packages from builder (may be empty if no requirements)
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Create non-root user for security
RUN useradd -m -u 1000 spark
WORKDIR /app

# Copy application source
COPY src/ /app/src/

# Create data directories with proper permissions
RUN mkdir -p /data/input /data/output && chown -R spark:spark /data /app

USER spark

# Default environment
ENV JOB_NAME=data-processor \
    INPUT_PATH=/data/input \
    OUTPUT_PATH=/data/output \
    USE_SPARK=false

# Health check: verify Python and script are importable
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=1 \
    CMD python -c "import sys; sys.path.insert(0, '/app/src'); import main" || exit 1

ENTRYPOINT ["python", "/app/src/main.py"]
