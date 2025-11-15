FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy monitoring code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash monitor
RUN chown -R monitor:monitor /app
USER monitor

# Health check
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Run SLO monitor
CMD ["python", "slo_monitor.py", "--api-url", "http://api:8000", "--interval", "30"]