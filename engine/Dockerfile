# Multi-stage build for BetFlow Engine v0.9.0
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash betflow

# Copy installed packages from builder
COPY --from=builder /root/.local /home/betflow/.local

# Copy engine code
COPY . .
RUN chown -R betflow:betflow /app

# Set environment
ENV PYTHONPATH=/app
ENV PATH=/home/betflow/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV MOJO_OPTIMIZATION_LEVEL=3
ENV BETFLOW_ENABLE_WARMUP=1
ENV BETFLOW_CPU_AFFINITY=""

# Switch to non-root user
USER betflow

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "from engine import BetFlowEngine; e = BetFlowEngine(); print('Engine ready:', e.health_check()['status'])" || exit 1

# Default command with warmup
CMD ["python", "-c", "import os; from engine import BetFlowEngine; import time; cpu_affinity = [int(x) for x in os.getenv('BETFLOW_CPU_AFFINITY', '').split(',') if x]; e = BetFlowEngine(enable_warmup=os.getenv('BETFLOW_ENABLE_WARMUP', '1') == '1', cpu_affinity=cpu_affinity if cpu_affinity else None); print('BetFlow Engine v0.9.0 ready and warmed up'); time.sleep(3600)"]
