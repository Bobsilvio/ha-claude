FROM ghcr.io/home-assistant/amd64-base:latest

# Install Python and dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    ca-certificates \
    curl \
    bash \
    jq \
    build-base \
    python3-dev

WORKDIR /app

# Copy backend requirements and install dependencies
COPY backend/requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy backend application
COPY backend/api.py .

# Copy the Claude custom component
COPY custom_components/claude /app/claude_component

# Create s6-overlay service directory
RUN mkdir -p /etc/services.d/claude-api

# Copy run script to services.d for s6-overlay
COPY addons/claude-backend/run.sh /etc/services.d/claude-api/run
RUN chmod +x /etc/services.d/claude-api/run

# Expose API port
EXPOSE 5000

# Set environment defaults
ENV DEBUG_MODE=False
ENV API_PORT=5000
ENV HA_URL=http://homeassistant:8123
ENV TIMEOUT=30
ENV MAX_RETRIES=3

# s6-overlay will handle everything from here - do not override CMD
