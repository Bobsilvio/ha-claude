FROM python:3.11-slim

# Install bashio (Home Assistant add-on utilities)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    bashio \
    ca-certificates \
    curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY api.py .

# Copy the Claude custom component (will be deployed automatically)
COPY custom_components/claude /app/claude_component

# Copy run script
COPY run.sh /
RUN chmod +x /run.sh

# Expose API port
EXPOSE 5000

# Set environment defaults
ENV DEBUG_MODE=False
ENV API_PORT=5000
ENV HA_URL=http://homeassistant:8123
ENV TIMEOUT=30
ENV MAX_RETRIES=3

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/health')"

# Run the application
CMD [ "/run.sh" ]
