FROM postgres:15-alpine

# Install additional tools
RUN apk add --no-cache \
    python3 \
    py3-pip \
    curl

# Install Alembic
RUN pip3 install alembic psycopg2-binary

# Create migration directory
RUN mkdir -p /migrations

# Copy migration files
COPY migrations/ /migrations/
COPY alembic.ini /migrations/

# Set working directory
WORKDIR /migrations

# Create initialization script
RUN echo '#!/bin/sh' > /docker-entrypoint-initdb.d/init-migrations.sh && \
    echo 'cd /migrations' >> /docker-entrypoint-initdb.d/init-migrations.sh && \
    echo 'alembic upgrade head' >> /docker-entrypoint-initdb.d/init-migrations.sh && \
    chmod +x /docker-entrypoint-initdb.d/init-migrations.sh

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD pg_isready -U betflow -d betflow || exit 1

# Expose port
EXPOSE 5432
