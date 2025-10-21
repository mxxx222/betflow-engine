FROM n8nio/n8n:latest

# Install additional dependencies
USER root
RUN apk add --no-cache curl

# Copy workflow files
COPY *.json /home/node/.n8n/workflows/

# Set permissions
RUN chown -R node:node /home/node/.n8n

# Switch back to node user
USER node

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5678/healthz || exit 1

# Expose port
EXPOSE 5678
