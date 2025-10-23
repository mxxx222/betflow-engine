FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    aiohttp \
    psutil \
    asyncio

# Copy monitoring scripts
COPY slo_monitor.py /app/slo_monitor.py
COPY requirements.txt /app/requirements.txt

# Install Python requirements
RUN pip install --no-cache-dir -r /app/requirements.txt

# Set working directory
WORKDIR /app

# Make scripts executable
RUN chmod +x /app/slo_monitor.py

# Default command
CMD ["python", "slo_monitor.py"]
