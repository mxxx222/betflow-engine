FROM postgres:15-alpine

# Install additional tools
RUN apk add --no-cache \
    curl

# Create migration directory
RUN mkdir -p /migrations

# Copy migration files
COPY migrations/ /migrations/

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD pg_isready -U betflow -d betflow || exit 1

# Expose port
EXPOSE 5432
