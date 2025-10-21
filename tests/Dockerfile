FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy test files
COPY . .

# Set Python path
ENV PYTHONPATH=/app

# Run tests
CMD ["pytest", "-v", "--cov=api", "--cov=engine", "--cov-report=html", "--cov-report=term"]
